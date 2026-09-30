"""Audit and synthesize completed campaigns without modifying frozen evidence.

This is post-result analysis, not a new experiment or release approval. The
parent and prospective extension stay separate; all declared jobs and attempts
are retained. No inference, model tuning or data rebuilding is performed.
"""

from __future__ import annotations

import argparse
import copy
import csv
import json
import math
import os
import subprocess
import tempfile
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path, PurePosixPath

from publication.calibration import PARAMETERS, coverage_metrics
from publication.campaign_reporting import state_fingerprint
from publication.contracts import canonical_hash, safe_path, sha256_file, verify_baseline
from publication.release import runtime_environment, verify_runtime

CAMPAIGNS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1")
OUTPUT = "reports/publication_synthesis/tcc_evidence_v1"
SCHEMA = "publication-post-campaign-synthesis-v1"
LEVELS = ("0.5", "0.8", "0.94")
TERMINAL = {"COMPLETED", "COMPLETED_REJECTED", "FAILED_TECHNICAL", "CANCELLED", "BLOCKED"}
LABELS = {"r": "Rp/Rs", "depth": "geometric depth r²", "b": "impact b", "a": "a/Rs",
          "t0": "t0 [day]", "full_duration": "T14 [day]", "extra_sigma": "white jitter"}


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def table(path: Path, rows: list[dict]) -> None:
    fields = list(dict.fromkeys(key for row in rows for key in row))
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, sort_keys=True) if isinstance(value, (dict, list)) else value for key, value in row.items()})


def verify_campaign_snapshot(root: Path, directory: Path) -> None:
    """Same recursive report contract, hashing each distinct file once.

    Bounded I/O concurrency avoids repeatedly traversing DrvFS for the same
    traces bound by global and family manifests. No source is omitted.
    """
    expected, active, verified = {}, set(), set()

    def bind(base: Path, name: str, digest: str) -> Path:
        parsed = PurePosixPath(name)
        if parsed.is_absolute() or ".." in parsed.parts or "\\" in name or ":" in name:
            raise ValueError("Report reference escaped its declared namespace")
        relative = (base / name).relative_to(root).as_posix()
        # Hash once, but enforce the narrowest base if a file is referenced
        # both as a repo source and as an artifact in a nested report directory.
        if relative not in expected:
            expected[relative] = (base, name, digest)
        elif expected[relative][2] != digest:
            raise ValueError(f"Conflicting report hashes for {relative}")
        elif base.is_relative_to(expected[relative][0]):
            expected[relative] = (base, name, digest)
        return base / name

    def visit(path: Path) -> None:
        if path in active:
            raise ValueError("Cyclic report manifest dependency")
        if path in verified:
            return
        active.add(path)
        manifest = read(path)
        for name, digest in manifest["source_checksums"].items():
            bind(root, name, digest)
        for name, digest in manifest["artifacts"].items():
            bind(path.parent, name, digest)
        children = manifest.get("child_manifests", [])
        if "source_state_path" in manifest:
            state = read(safe_path(root, manifest["source_state_path"]))
            if state_fingerprint(state, manifest["family_filter"]) != manifest["source_state_jobs_fingerprint"]:
                raise ValueError("Campaign job state changed since aggregation")
            if manifest["family_filter"] is None:
                summary = read(path.parent / "summary.json")
                if not {f"{family}/artifact_manifest.json" for family in summary["families"]}.issubset(children):
                    raise ValueError("Global report omits a required family manifest")
        for name in children:
            if name not in manifest["artifacts"]:
                raise ValueError("Child report manifest is not checksum-bound")
            visit(safe_path(path.parent, name))
        active.remove(path)
        verified.add(path)

    visit(directory / "artifact_manifest.json")

    def check(item):
        base, name, digest = item
        path = safe_path(base, name)
        if sha256_file(path) != digest:
            raise ValueError(f"Stale campaign artifact/source: {path.relative_to(root)}")

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(check, expected.values()))


def validate_declared_summary(summary: dict, ledger: dict) -> None:
    """Reject missing/duplicated jobs, outcome relabeling and partial batches."""
    jobs = summary["jobs"]
    declared = ledger["declared_jobs"]
    expected = {job["job_id"]: job for job in declared}
    if len(expected) != len(declared) or len({row["job_id"] for row in jobs}) != len(jobs):
        raise ValueError("Duplicate declared or reported job identity")
    if {row["job_id"] for row in jobs} != set(expected):
        raise ValueError("Report omits or adds declared jobs")
    if summary["mode"] != "final" or summary["campaign_id"] != ledger["campaign_id"]:
        raise ValueError("Only the declared final campaign can supply evidence")
    if summary.get("integrity_errors") or summary.get("preflight_errors"):
        raise ValueError("Campaign has unresolved integrity/preflight errors")
    if summary["declared_jobs"] != len(jobs) or summary["status_counts"] != dict(Counter(row["status"] for row in jobs)):
        raise ValueError("Reported denominator or statuses differ from complete inventory")
    if not summary["complete_declared_batch"] or any(row["status"] not in TERMINAL for row in jobs):
        raise ValueError("Incomplete final batch cannot be synthesized as complete")
    if summary["total_attempts"] != len(summary["attempts"]):
        raise ValueError("Attempt denominator differs from retained history")
    if len({(row["job_id"], row["attempt_index"]) for row in summary["attempts"]}) != len(summary["attempts"]):
        raise ValueError("Duplicate attempt identity")
    if any(row["job_id"] not in expected for row in summary["attempts"]):
        raise ValueError("Undeclared attempt in campaign history")
    for job in jobs:
        for key in ("experiment_id", "scenario_id", "replicate_id", "run_id", "seeds"):
            if job[key] != expected[job["job_id"]][key]:
                raise ValueError(f"Job changed frozen {key}: {job['job_id']}")
        output_dir = f"artifacts/publication_campaign/{ledger['campaign_id']}/runs/{job['experiment_id']}/{job['scenario_id']}/{job['replicate_id']}"
        if job["output_dir"] != output_dir:
            raise ValueError("Job output path differs from its frozen identity namespace")
        attempts = [row for row in summary["attempts"] if row["job_id"] == job["job_id"]]
        if len(attempts) != job["attempt_count"] or not attempts or attempts[-1]["status"] != job["status"]:
            raise ValueError("Attempt history inconsistent with final job status")
        for index, attempt in enumerate(attempts):
            if attempt["attempt_index"] != index or attempt["seeds"] != job["seeds"]:
                raise ValueError("Attempt order or seeds changed")
            if attempt["output_dir"] != output_dir + f"/attempt_{index:03d}":
                raise ValueError("Attempt escaped declared namespace")
            if attempt["authoritative"] != (index == len(attempts) - 1):
                raise ValueError("Authoritative attempt is not the last registered attempt")
        if job["status"] in {"COMPLETED", "COMPLETED_REJECTED"} and job["authoritative_attempt_dir"] != attempts[-1]["output_dir"]:
            raise ValueError("Numerical evidence points to the wrong attempt")


def recompute_calibration(jobs: list[dict], results: dict, truths: dict, stored: dict) -> dict:
    """Recalculate every P2 metric from sealed per-run summaries and truth.

    Truth is attached after inference. Rejected posteriors are deliberately
    included. Never pool campaigns or replace missing values with noncoverage.
    """
    groups = defaultdict(list)
    for job in jobs:
        if job["experiment_id"] == "PUB-02":
            groups[job["scenario_id"]].append(job)
    if set(groups) != set(stored["scenarios"]):
        raise ValueError("Calibration omits or adds a declared scenario")
    calculated = {}
    for scenario, rows in groups.items():
        records = []
        for row in rows:
            result = copy.deepcopy(results.get(row["job_id"]))
            if result is None:
                records.append({"replicate_id": row["replicate_id"], "status": "failed", "gates": {}})
                continue
            result["replicate_id"] = row["replicate_id"]
            truth = truths[row["job_id"]]["truth"]
            for name, values in result.get("parameters", {}).items():
                if name in truth:
                    values["truth"] = truth[name]
            records.append(result)
        metrics = coverage_metrics(records, [row["replicate_id"] for row in rows])
        if canonical_hash(metrics) != canonical_hash(stored["scenarios"][scenario]):
            raise ValueError(f"Stored calibration differs from all sealed results: {scenario}")
        calculated[scenario] = metrics
    return calculated


def flatten_calibration(campaign: str, scenarios: dict) -> list[dict]:
    rows = []
    for scenario, metrics in scenarios.items():
        for name, parameter in metrics["parameters"].items():
            for level, coverage in parameter["coverage"].items():
                rows.append({"campaign_id": campaign, "scenario_id": scenario, "parameter": name,
                             "declared_count": metrics["declared_count"],
                             **{key: value for key, value in parameter.items() if key != "coverage"}, **coverage})
    return rows


def summarize_gates(campaign: str, jobs: list[dict], results: dict) -> list[dict]:
    groups = defaultdict(list)
    for job in jobs:
        groups[(job["experiment_id"], job["scenario_id"])].append(job)
    rows = []
    for (family, scenario), group in groups.items():
        records = [results.get(job["job_id"], {}) for job in group]
        row = {"campaign_id": campaign, "experiment_id": family, "scenario_id": scenario,
               "declared": len(group), "status_counts": dict(Counter(job["status"] for job in group))}
        for gate in ("provenance", "sampler", "ppc", "scientific"):
            flags = [result.get("gates", {}).get(gate) for result in records]
            row[gate + "_passed"] = sum(flag is True for flag in flags)
            row[gate + "_rejected"] = sum(flag is False for flag in flags)
            row[gate + "_unavailable"] = sum(flag is None for flag in flags)
        row["sampler_pass_ppc_fail"] = sum(r.get("gates", {}).get("sampler") is True and r.get("gates", {}).get("ppc") is False for r in records)
        rows.append(row)
    return rows


def _cohort(root: Path, campaign: str) -> dict:
    directory = root / "reports/publication_campaign" / campaign
    verify_campaign_snapshot(root, directory)
    summary = read(directory / "summary.json")
    ledger = read(root / "configs/publication" / (campaign + "_plan.json"))
    validate_declared_summary(summary, ledger)
    definitions = {row["job_id"]: row for row in ledger["declared_jobs"]}
    results, truths, diagnostics = {}, {}, []
    for job in summary["jobs"]:
        relative = job.get("authoritative_attempt_dir")
        if not relative:
            continue
        result = read(safe_path(root, relative + "/result.json"))
        executed_job = read(safe_path(root, relative + "/job.json"))
        if {key: executed_job[key] for key in definitions[job["job_id"]]} != definitions[job["job_id"]]:
            raise ValueError(f"Executed payload differs from frozen ledger: {job['job_id']}")
        # Identity-negative controls have no numerical posterior and unavailable
        # downstream gates. Keep the canonical aggregate's explicit semantics.
        if result.get("failure_stage") == "input_validation":
            result = {**result, "gates": {"provenance": False}}
        results[job["job_id"]] = result
        truth_path = safe_path(root, relative + "/truth.json")
        if truth_path.is_file():
            truths[job["job_id"]] = read(truth_path)
        diagnostics.append({"campaign_id": campaign, "experiment_id": job["experiment_id"],
                            "scenario_id": job["scenario_id"], "replicate_id": job["replicate_id"],
                            "job_id": job["job_id"], "status": job["status"], "result_path": relative + "/result.json",
                            "gates": result.get("gates", {}), "diagnostics": result.get("diagnostics", {}),
                            "inherited_rejection_reasons": result.get("inherited_m5_gate", {}).get("rejection_reasons", []),
                            "inherited_component_reasons": result.get("inherited_m5_gate", {}).get("component_reasons", {}),
                            "temporal_residual_flagged": result.get("residual_correlation", {}).get("flagged"),
                            "temporal_residual_assessable": result.get("residual_correlation", {}).get("assessable"),
                            "failure_stage": result.get("failure_stage")})
    calibration = recompute_calibration(summary["jobs"], results, truths, summary["families"]["PUB-02"])
    return {"summary": summary, "calibration": calibration, "diagnostics": diagnostics,
            "gates": summarize_gates(campaign, summary["jobs"], results)}


def _percent(value) -> str:
    return "unavailable" if value is None else f"{100 * value:.1f}%"


def _number(value) -> str:
    return "unavailable" if value is None else f"{value:.6g}"


def _coverage(value: dict) -> str:
    interval = value["wilson95_numeric"]
    if interval is None:
        return "unavailable"
    return f"{value['covered_count']}/{value['numeric_count']} ({_percent(value['empirical_coverage_numeric'])}; IC95 {_percent(interval[0])}–{_percent(interval[1])})"


def render_report(payload: dict) -> str:
    lines = ["# Relatório consolidado de evidência para TCC e paper", "",
             "Análise posterior às campanhas; números gerados a partir dos resultados selados. "
             "Integridade dos artefatos e conclusão computacional não equivalem a calibração ou validade física universal.", "",
             "## Execução e denominadores", "",
             "| Campanha | Jobs declarados | Tentativas preservadas | Gates aprovados | Rejeitados | Falhas técnicas finais |", "|---|---:|---:|---:|---:|---:|"]
    for campaign, data in payload["campaigns"].items():
        counts = data["status_counts"]
        lines.append(f"| {campaign} | {data['declared_jobs']} | {data['total_attempts']} | {counts.get('COMPLETED', 0)} | {counts.get('COMPLETED_REJECTED', 0)} | {counts.get('FAILED_TECHNICAL', 0)} |")
    lines += ["", f"Total: {payload['total_jobs']} jobs e {payload['total_attempts']} tentativas. "
              "Tentativas canceladas anteriores permanecem em `attempt_inventory.csv`; não são novos replicates independentes. "
              "Os controles de identidade são rejeições deliberadas, não falhas de execução.", "",
              "A extensão foi decidida após observar a campanha inicial, com protocolo prospectivo, novos seeds e N fixo. "
              "As coortes são apresentadas separadamente; não há pooling nem seleção dos melhores seeds.", "",
              "## P2 — confirmação independente da precisão das estimativas de calibração", "",
              "Cobertura de intervalos de caudas iguais em verdades fixas, com IC de Wilson de 95%. "
              "Não é SBC: os parâmetros verdadeiros não foram sorteados do prior. "
              "Intervalos Bayesianos não têm garantia de cobertura frequentista nominal em cada verdade fixa. "
              "Sub/sobrecobertura descreve o desempenho condicional deste workflow, sem demonstrar, isoladamente, erro do sampler. "
              "Os intervalos de Wilson são pontuais, não simultâneos; não se fazem descobertas por múltiplos testes sem ajuste.", "",
              "A tabela inclui todos os posteriors numéricos, inclusive os rejeitados. "
              "As colunas condicionadas ao sampler/gate, seus denominadores, viés, RMSE, SD e larguras em todos os níveis "
              "estão em `calibration_metrics.csv`. A taxa coberto-e-aprovado sobre todos os declarados é operacional, não cobertura.", ""]
    for campaign, scenarios in payload["calibration"].items():
        lines += [f"### Coorte {campaign}", "", "| Regime | N | Sampler aprovado | PPC aprovado | Gate final aprovado |", "|---|---:|---:|---:|---:|"]
        for scenario, metrics in scenarios.items():
            lines.append(f"| {scenario} | {metrics['declared_count']} | {metrics['gates']['sampler']['passed_count']} | {metrics['gates']['ppc']['passed_count']} | {metrics['gates']['scientific']['passed_count']} |")
        lines += ["", "| Regime | Parâmetro | Viés | Viés relativo | RMSE | Cobertura 50% | Cobertura 80% | Cobertura 94% | Largura média 94% |", "|---|---|---:|---:|---:|---|---|---|---:|"]
        for scenario, metrics in scenarios.items():
            for name in PARAMETERS:
                p = metrics["parameters"][name]
                lines.append(f"| {scenario} | {name} | {_number(p['bias'])} | {_percent(p['relative_bias'])} | {_number(p['rmse'])} | " + " | ".join(_coverage(p["coverage"][level]) for level in LEVELS) + f" | {_number(p['coverage']['0.94']['mean_interval_width'])} |")
    confirm = payload["calibration"][CAMPAIGNS[1]]
    near = confirm["near_limit_long"]["parameters"]
    near_gates = confirm["near_limit_long"]["gates"]
    lines += ["", "### Interpretação e resultados negativos", "",
              f"No regime near_limit_long, o viés relativo médio de Rp/Rs é {_percent(near['r']['relative_bias'])}; "
              f"a cobertura 94% de a/Rs é {_coverage(near['a']['coverage']['0.94'])}, "
              f"e a de duração é {_coverage(near['full_duration']['coverage']['0.94'])}. "
              f"Mesmo assim, {near_gates['scientific']['passed_count']}/{confirm['near_limit_long']['declared_count']} "
              "passam pelo gate final. A aprovação é insuficiente para garantir identificação/calibração dos parâmetros. "
              "A contribuição sustentada aqui inclui delimitar essa falha, não afirmar recuperação confiável nesse regime.", "",
              "Nos regimes profundo e raso, a cobertura de Rp/Rs excede o nominal em vários níveis; "
              "boa inclusão da verdade pode coexistir com intervalos conservadores. Compare largura e viés. "
              "A geometria pouco identificada, os priors e a correlação entre parâmetros são explicações plausíveis, "
              "não causas isoladas demonstradas por esta grade, que varia diversos fatores simultaneamente.", "",
              "As rejeições são detalhadas por execução em `diagnostics.csv` e por cenário em `gate_summary.csv`. "
              "Critérios de rejeição se sobrepõem; não some motivos como se fossem runs distintos. "
              "Modos periódicos presos em cadeias de t0 estão documentados na revisão dos traces. "
              "Esses runs permanecem rejeitados e nos agregados; não houve descarte de cadeias ou substituição de seeds.", "",
              "## P3 — benchmark independente", "",
              f"Estado da comparação: `{payload['benchmark']['status']}`; ambas implementações interpretáveis: "
              f"`{payload['benchmark'].get('both_scientifically_interpretable', False)}`. "
              "As duas implementações foram executadas sobre a mesma entrada sob o contrato publicado. "
              "A concordância marginal de alguns parâmetros é apenas descritiva: NUTS local falhou numericamente "
              "e o resultado externo falhou no PPC temporal. Não há validação externa positiva da inferência física.", "",
              "| Parâmetro | Diferença de médias / SD combinada | Sobreposição ETI94 (Jaccard) | Largura externa/local ETI94 | Discrepância marcada |", "|---|---:|---:|---:|---|"]
    for name, values in payload["benchmark"].get("comparison", {}).get("parameters", {}).items():
        interval = values["intervals"]["0.94"]
        lines.append(f"| {name} | {_number(values['standardized_mean_difference'])} | {_number(interval['overlap_jaccard'])} | {_number(interval['width_ratio_external_local'])} | {values['material_discrepancy_flag']} |")
    lines += ["", "Um modo de t0 separado por aproximadamente um período reteve uma cadeia local. "
              "O prior de t0 e a inicialização devem ser investigados prospectivamente. "
              "Não se remove a cadeia para fabricar concordância. A revisão registra evidência e hipóteses causais separadas.", "",
              "## P4 — ablations e falhas", "",
              f"{payload['ablation']['declared_jobs']} controles/intervenções; "
              f"{payload['ablation']['sampler_pass_but_ppc_or_science_fail_count']} casos com sampler aprovado e PPC/ciência reprovados. "
              "Isso demonstra empiricamente que convergência não basta para promoção. "
              "Controles de hash/identidade rejeitados antes da inferência têm sampler/PPC indisponíveis, não medidos como falhos.", "",
              "Os efeitos por replicate e parâmetro estão em `ablation_paired_effects.csv`. "
              "São diferenças descritivas entre saídas numéricas: os baselines longos falharam no sampler, "
              "o que limita sua interpretação como efeitos físicos precisos. Há somente três realizações por par. "
              "O controle senoidal é sistemática determinística e não valida ruído estocástico correlacionado.", "",
              "## P5 — todos os alvos pré-selecionados", "",
              "| Alvo | Estado | Proveniência | Sampler | PPC | Gate final |", "|---|---|---|---|---|---|"]
    for row in payload["targets"]:
        lines.append(f"| {row['target_name']} | {row['status']} | {row['gate_provenance']} | {row['gate_sampler']} | {row['gate_ppc']} | {row['gate_scientific']} |")
    lines += ["", "Nenhum alvo foi trocado ou omitido. Estes fits de publicação não sustentam generalização positiva. "
              "O histórico scientific_003 é outro contrato experimental preservado; não foi sobrescrito ou reclassificado. "
              "Catálogo/PDCSAP e efemérides condicionam a análise, portanto comparação com catálogo não é validação independente. "
              "Correlações residuais motivam investigação de adequação; não provam sozinhas que um GP resolveria o problema.", "",
              "## P6, novidade e limites", "",
              "M6 e calibração sob ruído OU continuam não executados. M5 contém ruído branco adicional independente, "
              "não covariância temporal. A prioridade atual é resolver/entender identificação, inicialização e adequação "
              "sob os contratos já testados. Não há superioridade de GP demonstrada.", "",
              "A contribuição defensável é a integração e avaliação empírica de proveniência, inferência e critérios "
              "de interpretação, incluindo seus limites e falhas. O estudo não reivindica prioridade, novo modelo "
              "de trânsito, novo sampler ou invenção de SBC/gates. Consulte NOVELTY_MATRIX e BIBLIOGRAPHY.", "",
              "A física geradora e a inferência compartilham primitivas; esta calibração não é totalmente independente "
              "da implementação. A grade contém quatro verdades fixas, sem amostragem de população. "
              "Aprovação em gates é um diagnóstico sob um contrato, não certificado de exatidão física. "
              "O estudo de sensibilidade/prior do baseline não substitui sensibilidade nesses novos regimes.", "",
              "## Reprodutibilidade e reprodução", "",
              "`artifact_manifest.json` vincula fontes, gerador, ambiente, tabelas e figuras; "
              "`SOURCE_INVENTORY.json` lista os arquivos exatos para a próxima reconstrução do TCC/paper. "
              "Os manifests das campanhas verificam recursivamente os resultados originais e seus traces. "
              "O código de síntese recalcula as métricas P2 e exige igualdade com os agregados selados.", "",
              "```sh", "python scripts/build_publication_synthesis.py", "python scripts/build_publication_synthesis.py --check", "python scripts/run_ci_tests.py", "python scripts/validate_publication_release.py", "```", "",
              "O último comando é um gate de release distinto e ainda pode falhar: "
              "a síntese não concede aprovação para publicação/tag/DOI. "
              "Clean-room completo da nova release, arquivo externo dos traces, revisão de distribuição/privacidade "
              "e integração do validador de release com o registry de campanhas permanecem pendentes. "
              "Não há afirmação de reprodução integral em máquina limpa nesta revisão.", "",
              "Os originais foram preservados. Para refazer agregações históricas use o checkout/ambiente "
              "identificado no manifest da campanha; o comando acima refaz esta síntese no checkout atual.", "",
              "## Fontes de interpretação", "",
              "[Talts et al., SBC](https://arxiv.org/abs/1804.06788), "
              "[Vehtari et al., diagnósticos MCMC](https://arxiv.org/abs/1903.08008), "
              "[Gelman et al., Bayesian Workflow](https://arxiv.org/abs/2011.01808). "
              "Fontes primárias reconferidas em 2026-09-30 e registradas na bibliografia do repositório.", ""]
    return "\n".join(lines)


def coverage_error_lengths(points: list[float], bounds: list[list[float]]) -> list[list[float]]:
    """Clip floating-point endpoint roundoff only, never change stored CIs."""
    lower, upper = [], []
    for point, (lo, hi) in zip(points, bounds, strict=True):
        if not all(math.isfinite(value) for value in (point, lo, hi)) or lo > hi or lo > point + 1e-14 or hi < point - 1e-14:
            raise ValueError("Coverage point lies outside its uncertainty interval")
        lower.append(max(0., point - lo))
        upper.append(max(0., hi - point))
    return [lower, upper]


def figures(output: Path, calibration: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    data = calibration[CAMPAIGNS[1]]
    fig, axes = plt.subplots(2, 4, figsize=(15, 8), sharex=True, sharey=True, layout="constrained")
    colors = ("#2166ac", "#d6604d", "#4d9221", "#762a83")
    for ax, parameter in zip(axes.flat, PARAMETERS, strict=False):
        for index, (scenario, metrics) in enumerate(data.items()):
            values = metrics["parameters"][parameter]["coverage"]
            y = [values[level]["empirical_coverage_numeric"] for level in LEVELS]
            bounds = [values[level]["wilson95_numeric"] for level in LEVELS]
            x = [float(level) + (index - 1.5) * .008 for level in LEVELS]
            ax.errorbar(x, y, yerr=coverage_error_lengths(y, bounds),
                        fmt="o-", capsize=2, ms=3, color=colors[index], label=scenario)
        ax.plot([0, 1], [0, 1], color="0.5", linestyle="--", linewidth=.8)
        ax.set(title=LABELS[parameter], xlim=(.42, 1.01), ylim=(-.03, 1.04), xticks=(.5, .8, .94))
        ax.set_xlabel("Nominal equal-tailed interval probability")
        ax.set_ylabel("Empirical coverage; pointwise Wilson 95% CI")
    axes.flat[-1].axis("off")
    handles, labels = axes.flat[0].get_legend_handles_labels()
    axes.flat[-1].legend(handles, labels, loc="center", frameon=False)
    fig.suptitle("Independent fixed-truth cohort: 100 datasets per regime\nAll numeric posteriors, including rejected fits; not SBC")
    fig.savefig(output / "coverage_all_parameters.png", dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), layout="constrained")
    scenarios = list(data)
    for index, scenario in enumerate(scenarios):
        p = data[scenario]["parameters"]["r"]
        axes[0].bar(index, p["relative_bias"] * 100, color=colors[index])
        for offset, key, label, color in [(-.24, "rmse", "RMSE of posterior mean", "#2166ac"), (0, "mean_posterior_sd", "Mean posterior SD", "#d6604d")]:
            axes[1].bar(index + offset, p[key], width=.22, color=color, label=label if index == 0 else None)
        axes[1].bar(index + .24, p["coverage"]["0.94"]["mean_interval_width"], width=.22,
                    color="#4d9221", label="Mean ETI94 width" if index == 0 else None)
    for ax in axes:
        ax.set_xticks(range(len(scenarios)), scenarios, rotation=20, ha="right")
        ax.axhline(0, color="black", linewidth=.6)
    axes[0].set_ylabel("Radius-ratio relative bias [%]")
    axes[1].set_ylabel("Radius-ratio scale (dimensionless)")
    axes[1].legend(fontsize=8)
    fig.suptitle("Recovery and uncertainty are distinct; all 100 numeric results per regime")
    fig.savefig(output / "radius_bias_and_uncertainty.png", dpi=180)
    plt.close(fig)


def render_manuscript(payload: dict) -> str:
    """Journal-agnostic source draft; numerical results stay generated."""
    n = payload["calibration"][CAMPAIGNS[1]]["near_limit_long"]["parameters"]["a"]["coverage"]["0.94"]
    return f"""# Auditando a confiabilidade de um workflow Bayesiano de trânsitos

Status: rascunho de fonte para TCC/manuscrito, posterior aos resultados.
Não é um manuscrito aprovado para submissão. Tabelas completas: [REPORT.md](REPORT.md).
O ledger de afirmações é [claims.json](claims.json).

## Resumo

Investigamos em quais condições um workflow rastreável de inferência de trânsitos
recupera parâmetros e quantifica incerteza. Dois experimentos com verdades fixas
contêm 80 e 400 realizações independentes, analisadas separadamente. O programa
inclui um benchmark publicado independente, intervenções controladas e cinco
sistemas reais pré-selecionados. O inventário contém {payload['total_jobs']} jobs
e {payload['total_attempts']} tentativas, inclusive uma tentativa cancelada.
Os resultados mostram recuperação dependente do regime e do parâmetro, com
intervalos conservadores em alguns casos e cobertura 94% de a/Rs de
{n['covered_count']}/{n['numeric_count']} no regime menos informativo. As falhas
preservadas demonstram que convergência e gates de adequação não garantem
identificação física. A contribuição é uma avaliação auditável desses limites;
não reivindicamos calibração universal ou superioridade sobre outros fitters.

## 1. Motivação e trabalhos relacionados

A confiabilidade exige identificação de dados, avaliação da computação e
verificação do modelo. SBC (Talts et al.) e Bayesian Workflow (Gelman et al.)
estabelecem parte desse fundamento; não são novidades deste projeto.
`exoplanet`, `juliet` e `allesfitter` já fornecem inferência científica de
trânsitos. A matriz de novidade compara capacidades verificadas e desconhecidas
sem pressupor que ferramentas anteriores careçam de validação ou proveniência.
A contribuição investigada é a integração e avaliação de contratos rastreáveis
de promoção da evidência. Ver `docs/publication/NOVELTY_MATRIX.md` e
`docs/publication/BIBLIOGRAPHY.md` no repositório.

## 2. Modelo e proveniência

O modelo circular usa trânsito com limb darkening quadrático e integração na
exposição. Para observação i:

\\[
y_i \\sim \\mathcal{{N}}(\\mu_i(\\theta),\\sigma_i^2+s^2),\\qquad
\\mu_i = c + \\Delta t_i^{{-1}}\\int_{{t_i-\\Delta t_i/2}}^{{t_i+\\Delta t_i/2}}
\\Delta F(t;\\theta)\\,dt.
\\]

`s` é jitter branco independente. Não há covariância temporal no M5. Os
parâmetros incluem r=Rp/Rs, b, a/Rs, t0 e limb darkening transformado via q1/q2.
A profundidade geométrica é r²; ela difere da profundidade observada sob limb
darkening. A duração T14 segue a geometria circular declarada no protocolo.
Os priors e samplers exatos por família constam nos protocolos congelados, que
são fonte autoritativa e precedem a execução; não se substituem por uma descrição
genérica que esconda diferenças do contrato de benchmark ou dos alvos reais.

Dados públicos percorrem RAW, Silver e Gold com hashes, identidade de segmento,
unidades e exposição. O resultado histórico scientific_003 tem seu próprio
manifest e permanece separado dos novos experimentos.

## 3. Desenho e estimandos

P2 usa quatro regimes com verdades fixas, e não uma amostra do prior: é cobertura
condicional em repetidas realizações do ruído, não SBC. A extensão de 100 novas
realizações por regime foi decidida após observar a coorte de 20; seu protocolo
prospectivo declara N fixo e novos seeds. As coortes não são combinadas.
Vários fatores variam entre regimes; as comparações não isolam efeitos causais
de cadência ou SNR. A geração compartilha primitivas físicas com a inferência,
uma limitação de independência explicitamente reconhecida.

Para cada parâmetro, viés = média das médias posteriores menos a verdade;
RMSE = raiz da média dos erros quadráticos; cobertura = frequência de inclusão
da verdade nos intervalos de caudas iguais. Relatamos 50%, 80% e 94%, larguras,
SD posterior e Wilson95 pontual para as frequências. Falhas, dados ausentes e
rejeições têm denominadores explícitos. Resultados condicionados à aprovação
são selecionados; a taxa coberto-e-aprovado sobre todos os jobs é rendimento
operacional, não calibração de intervalos. Não se infere calibração perfeita
por ausência de discrepância significativa, nem se faz seleção por p-valor.

P3 compara a implementação local e juliet sob contrato de dados/modelo/priors.
P4 inclui exposição, normalização, jitter, prior inadequado, amostragem insuficiente,
identidade inválida e sistemática senoidal. P5 mantém os cinco alvos declarados,
incluindo os rejeitados. Nenhum dos estudos valida desempenho populacional.

## 4. Resultados

Inserir as tabelas e figuras geradas em [REPORT.md](REPORT.md),
[calibration_metrics.csv](calibration_metrics.csv),
[gate_summary.csv](gate_summary.csv),
[ablation_paired_effects.csv](ablation_paired_effects.csv) e
[targets.csv](targets.csv). As captions estão em [captions.json](captions.json);
o inventário exato das fontes e figuras históricas está em
[SOURCE_INVENTORY.json](SOURCE_INVENTORY.json).

A narrativa deve apresentar tanto sobrecobertura quanto subcobertura e viés,
destacar limites de identificação, e manter as falhas do benchmark e de todos
os alvos. Sem convergência local, sem adequação preditiva e com aliases de t0,
a concordância de algumas marginais não constitui validação externa positiva.
A demonstração de sampler aprovado/PPC reprovado é sustentada pelos controles;
efeitos físicos pareados têm interpretação limitada pela divergência dos baselines.

## 5. Discussão e ameaças à validade

O prior Uniform(2,50) de a/Rs tem intervalo central94% [3.44,48.56]; portanto
um posterior sem informação pode excluir uma verdade 3.3 que está no suporte.
Esse exemplo explica por que cobertura condicional ruim não diagnostica sozinha
um bug. Não demonstra quantitativamente que todo o erro observado venha do prior.
Os resultados exigem revisão de claims de recuperação no regime fraco, e futura
avaliação prospectiva de identificação/informação, sem ajustar priors à verdade.

Gates detectam classes de falha, mas não garantem precisão dos parâmetros.
R-hat/ESS não testam adequação da likelihood; PPC global não exclui estrutura
temporal. Diagnósticos de correlação são aproximados e dependem do thinning.
Catálogos usados para condicionar a análise não oferecem validação astrofísica
independente. O conjunto multi-alvo foi escolhido por regimes, não aleatoriamente.

Limitações adicionais: primitivas físicas compartilhadas; verdades fixas;
somente três realizações por ablation; normalização empírica sem propagação
integral de incerteza; período/eccentricidade fixos; modos periódicos de t0;
posteriores rejeitados retidos apenas como diagnóstico; ausência de validação
sob ruído estocástico correlacionado. M6 não foi executado. LOO/WAIC não é usado
para ranquear modelos neste estudo. A extensão GP permanece investigação futura.

## 6. Disponibilidade e reprodução

`python scripts/build_publication_synthesis.py` gera este conjunto sem inferência;
`--check` valida hashes, figuras, textos e dependências das campanhas. Os
protocolos, seeds e fontes seladas permitem auditoria; restaurar os traces e
intermediários externos ainda é requisito de release. Não há DOI ou reprodução
integral limpa declarada. Ver [STORAGE_MANIFEST.json](STORAGE_MANIFEST.json).

## 7. Conclusão sustentada

O estudo produz evidência repetida sobre o desempenho condicional e as limitações
do workflow, preserva resultados negativos e torna auditável a distância entre
convergência, adequação e recuperação física. Os dados não sustentam uma garantia
universal de calibração ou generalização. Qualquer versão futura que modifique
inicialização, priors, likelihood ou critérios deve ser avaliada em novos IDs,
sob protocolo prospectivo, preservando estas coortes como referência.
"""


def publish_rendered_bundle(output: Path, destination: Path) -> Path:
    """Publish rendered files, sealing last; interrupted publication is detectable."""
    if not (output / "artifact_manifest.json").is_file():
        raise ValueError("Rendered bundle is missing its artifact manifest")
    destination.mkdir(parents=True, exist_ok=True)
    for path in sorted(output.iterdir(), key=lambda path: (path.name == "artifact_manifest.json", path.name)):
        os.replace(path, destination / path.name)
    output.rmdir()
    return destination


def build(root: Path, output_relative: str = OUTPUT) -> Path:
    root = root.resolve()
    output = safe_path(root, output_relative)
    if not output_relative.startswith("reports/publication_synthesis/"):
        raise ValueError("Synthesis output must stay in its own reports namespace")
    if output.exists() and any(output.iterdir()):
        if not (output / "artifact_manifest.json").is_file() or read(output / "artifact_manifest.json").get("schema_version") != SCHEMA:
            raise ValueError("Refusing to overwrite an unrelated or partial evidence directory")
    baseline = verify_baseline(root)
    environment = runtime_environment(root)
    verify_runtime(environment)
    cohorts = {campaign: _cohort(root, campaign) for campaign in CAMPAIGNS}
    payload = {"schema_version": SCHEMA, "analysis_stage": "post_result_descriptive_audit",
               "release_approved": False, "baseline": baseline, "environment": environment,
               "campaigns": {}, "calibration": {}}
    jobs, attempts, diagnostics, gates, calibration_rows = [], [], [], [], []
    for campaign, cohort in cohorts.items():
        summary = cohort["summary"]
        payload["campaigns"][campaign] = {key: summary[key] for key in ("declared_jobs", "total_attempts", "status_counts", "complete_declared_batch", "all_declared_scientific_jobs_finished", "campaign_initial_code_commit")}
        payload["calibration"][campaign] = cohort["calibration"]
        jobs.extend({"campaign_id": campaign, **job} for job in summary["jobs"])
        attempts.extend({"campaign_id": campaign, **attempt} for attempt in summary["attempts"])
        diagnostics.extend(cohort["diagnostics"])
        gates.extend(cohort["gates"])
        calibration_rows.extend(flatten_calibration(campaign, cohort["calibration"]))
    parent = cohorts[CAMPAIGNS[0]]["summary"]["families"]
    benchmark = copy.deepcopy(parent["PUB-03"])
    # Row permutation arrays stay in the source contract; retain scalar evidence.
    benchmark.get("predictive_comparison", {}).pop("row_mapping", None)
    with (root / "reports/publication_campaign" / CAMPAIGNS[0] / "PUB-05/targets.csv").open(encoding="utf-8", newline="") as stream:
        targets = list(csv.DictReader(stream))
    payload.update(total_jobs=len(jobs), total_attempts=len(attempts), benchmark=benchmark,
                   ablation=parent["PUB-04"]["ablations"], targets=targets,
                   gate_summary=gates, cohort_policy="separate; extension selected after parent outcomes; no pooling",
                   calibration_checks="Every stored P2 metric recomputed from all sealed per-run result/truth records")
    payload["claims"] = [
        {"claim_id": "conditional_recovery", "status": "regime_and_parameter_limited",
         "text": "Known-truth repeated coverage and bias were measured; universal nominal calibration is not supported.",
         "sources": [f"reports/publication_campaign/{campaign}/PUB-02/calibration.json" for campaign in CAMPAIGNS]},
        {"claim_id": "external_validation", "status": "positive_claim_not_supported",
         "text": "External fits completed but scientific diagnostics prohibit positive validation claims.",
         "sources": [f"reports/publication_campaign/{CAMPAIGNS[0]}/PUB-03/benchmark.json"]},
        {"claim_id": "convergence_insufficient", "status": "negative_control_evidence",
         "count": payload["ablation"]["sampler_pass_but_ppc_or_science_fail_count"],
         "sources": [f"reports/publication_campaign/{CAMPAIGNS[0]}/PUB-04/ablation.json"]},
        {"claim_id": "multi_target", "status": "positive_generalization_not_supported",
         "text": "All preselected targets retained, including rejected fits; no population claim.",
         "sources": [f"reports/publication_campaign/{CAMPAIGNS[0]}/PUB-05/aggregate.json"]},
        {"claim_id": "m6", "status": "not_executed", "text": "No correlated likelihood performance claim.",
         "sources": ["docs/publication/COMPUTE_BUDGET_AMENDMENT.md"]},
    ]
    sources = {}
    storage = {}
    for campaign, cohort in cohorts.items():
        directory = root / "reports/publication_campaign" / campaign
        manifest = read(directory / "artifact_manifest.json")
        for relative in ("artifact_manifest.json", *manifest["artifacts"]):
            path = directory / relative
            sources[path.relative_to(root).as_posix()] = sha256_file(path)
        for name in (f"configs/publication/{campaign}_plan.json", cohort["summary"]["source_state_path"]):
            sources[name] = sha256_file(root / name)
        for name, digest in cohort["summary"]["source_checksums"].items():
            storage[name] = {"path": name, "sha256": digest,
                             "external_archive_required": name.endswith(".nc") or (name.startswith("publication/observational/") and Path(name).name in {"silver_lightcurve.csv", "gold_lightcurve.csv"}),
                             "remote_archive": None}
        for attempt in cohort["summary"]["attempts"]:
            if not attempt.get("completion_manifest_sha256"):
                for path in safe_path(root, attempt["output_dir"]).rglob("*"):
                    if path.is_file():
                        name = path.relative_to(root).as_posix()
                        digest = sha256_file(path)
                        sources[name] = digest
                        storage[name] = {"path": name, "sha256": digest, "external_archive_required": False,
                                         "evidence_role": "unsealed_partial_not_scientific", "remote_archive": None}
    context = ["publication/baseline/manifest.json", "publication/registry.json",
               "docs/publication/NOVELTY_MATRIX.json", "docs/publication/NOVELTY_MATRIX.md",
               "docs/publication/BIBLIOGRAPHY.md", "docs/publication/CALIBRATION_REVIEW.md",
               "docs/publication/COMPUTE_BUDGET_AMENDMENT.md", "docs/publication/FINAL_EVIDENCE_STORAGE.md",
               "docs/publication/POST_CAMPAIGN_SCIENTIFIC_REVIEW.md", "docs/publication/CONFIRMATORY_RUNTIME_AUDIT.md",
               "docs/publication/BENCHMARK_SELECTION.md", "docs/publication/TARGET_SELECTION_PROTOCOL.md",
               "publication/protocols/PUB-02.json", "publication/protocols/PUB-02-confirmatory-v1.json",
               "publication/protocols/PUB-03.json", "publication/protocols/PUB-04.json", "publication/protocols/PUB-05.json",
               "requirements.txt", "environment.yml", "pyproject.toml",
               "src/publication/synthesis.py", "scripts/build_publication_synthesis.py"]
    for name in context:
        sources[name] = sha256_file(root / name)
    destination = output
    output.parent.mkdir(parents=True, exist_ok=True)
    output = Path(tempfile.mkdtemp(prefix=".synthesis-render-", dir=output.parent))
    write(output / "summary.json", payload)
    write(output / "aggregation_environment.json", environment)
    write(output / "STORAGE_MANIFEST.json", {"schema_version": "publication-storage-audit-v1",
          "archive_status": "local_only_external_deposition_pending", "files": list(storage.values())})
    write(output / "claims.json", payload["claims"])
    table(output / "run_inventory.csv", jobs)
    table(output / "attempt_inventory.csv", attempts)
    table(output / "diagnostics.csv", diagnostics)
    table(output / "gate_summary.csv", gates)
    table(output / "calibration_metrics.csv", calibration_rows)
    table(output / "ablation_paired_effects.csv", payload["ablation"]["paired_effects"])
    table(output / "targets.csv", targets)
    (output / "REPORT.md").write_text(render_report(payload), encoding="utf-8", newline="\n")
    (output / "MANUSCRIPT_DRAFT.md").write_text(render_manuscript(payload), encoding="utf-8", newline="\n")
    figures(output, payload["calibration"])
    captions = {
        "coverage_all_parameters.png": "Cobertura de ETI50/80/94 por parâmetro/regime; 100 novos datasets em cada regime. Barras: Wilson95 pontuais, sem ajuste simultâneo. Todos os posteriors numéricos, incluindo rejeitados; cobertura condicionada está na tabela. Referência diagonal não é garantia Bayesiana de cobertura condicional.",
        "radius_bias_and_uncertainty.png": "Viés relativo de Rp/Rs e comparação entre RMSE das médias, SD posterior média e largura ETI94. Escalas lineares com zero explícito; regimes não são intervenções unifatoriais. Largura não equivale a precisão de recuperação."
    }
    write(output / "captions.json", captions)
    write(output / "SOURCE_INVENTORY.json", {"schema_version": "tcc-paper-evidence-inventory-v2",
          "usage": "Sources for reconstruction; rejected results support only explicitly qualified negative/descriptive claims",
          "sources": [{"path": name, "sha256": digest} for name, digest in sorted(sources.items())],
          "generated_tables_figures_reports": sorted(path.name for path in output.iterdir() if path.is_file() and path.name not in {"artifact_manifest.json", "SOURCE_INVENTORY.json"})})
    manifest = {"schema_version": SCHEMA, "source_checksums": sources,
                "campaign_reports": [f"reports/publication_campaign/{campaign}" for campaign in CAMPAIGNS],
                "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).decode().strip(),
                "campaign_state_fingerprints": {campaign: state_fingerprint(read(root / cohorts[campaign]["summary"]["source_state_path"])) for campaign in CAMPAIGNS},
                "artifacts": {path.name: sha256_file(path) for path in sorted(output.iterdir()) if path.is_file() and path.name != "artifact_manifest.json"},
                "regenerate_command": "python scripts/build_publication_synthesis.py", "release_approved": False}
    write(output / "artifact_manifest.json", manifest)
    # Seal the manifest last. A failed render leaves the previous complete
    # bundle untouched; an interrupted publication fails checksum validation.
    return publish_rendered_bundle(output, destination)


def verify_bundle(root: Path, output: Path) -> dict:
    manifest = read(output / "artifact_manifest.json")
    if manifest.get("schema_version") != SCHEMA or manifest.get("release_approved") is not False:
        raise ValueError("Invalid synthesis schema or unsupported release approval")
    required = {"summary.json", "REPORT.md", "SOURCE_INVENTORY.json", "calibration_metrics.csv",
                "claims.json", "aggregation_environment.json", "STORAGE_MANIFEST.json", "MANUSCRIPT_DRAFT.md",
                "run_inventory.csv", "attempt_inventory.csv", "diagnostics.csv", "gate_summary.csv",
                "ablation_paired_effects.csv", "targets.csv", "captions.json",
                "coverage_all_parameters.png", "radius_bias_and_uncertainty.png"}
    if not required.issubset(manifest["artifacts"]) or not manifest["source_checksums"]:
        raise ValueError("Missing required synthesis output/source")
    for name, digest in manifest["source_checksums"].items():
        if sha256_file(safe_path(root, name)) != digest:
            raise ValueError(f"Stale synthesis source: {name}")
    for name, digest in manifest["artifacts"].items():
        if sha256_file(safe_path(output, name)) != digest:
            raise ValueError(f"Stale synthesis artifact: {name}")
    expected = [f"reports/publication_campaign/{campaign}" for campaign in CAMPAIGNS]
    if manifest["campaign_reports"] != expected:
        raise ValueError("A required campaign was omitted or replaced")
    for relative in expected:
        verify_campaign_snapshot(root, safe_path(root, relative))
    verify_baseline(root)
    payload = read(output / "summary.json")
    if (output / "REPORT.md").read_text(encoding="utf-8") != render_report(payload):
        raise ValueError("Narrative differs from machine-readable results")
    if (output / "MANUSCRIPT_DRAFT.md").read_text(encoding="utf-8") != render_manuscript(payload):
        raise ValueError("Manuscript differs from machine-readable results")
    return {"status": "passed", "scope": "post-campaign evidence integrity; not paper release approval",
            "declared_jobs": payload["total_jobs"], "preserved_attempts": payload["total_attempts"]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Verify sources/results/figures without regenerating")
    parser.add_argument("--output", default=OUTPUT)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.check:
        print(json.dumps(verify_bundle(root, safe_path(root, args.output)), indent=2))
    else:
        print(build(root, args.output).relative_to(root).as_posix())


if __name__ == "__main__":
    main()
