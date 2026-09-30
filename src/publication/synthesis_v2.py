"""Generate TCC v2 from independent audits, never mutate historical synthesis."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter
from pathlib import Path, PurePosixPath

from publication.claim_authorization import EVALUATOR_VERSION, evaluate_run
from publication.evidence_archive import verify_inventory
from publication.trace_audit import SCHEMA as TRACE_SCHEMA
from publication.trace_audit import verify_audit

COHORTS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1")
SCENARIOS = ("deep_short", "intermediate_long", "shallow_short", "near_limit_long")
PARAMETERS = ("r", "depth", "b", "a", "t0", "full_duration", "extra_sigma")
OUTPUT = "reports/publication_synthesis/tcc_evidence_v2"
AUDIT = "publication/validation/trace_audit_v1/audit.json"
RESIDUAL = "publication/validation/residual_review_v2/audit.json"
MECHANISM = "publication/validation/t0_mechanism_v3/audit.json"
TRANSITIVE = "publication/validation/external_audit_closure_v1/transitive_inventory_final.json"


def sha(path: Path) -> str:
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8", newline="\n")


def table(path, rows):
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def bound(root, name, expected=None):
    parsed = PurePosixPath(name)
    if parsed.is_absolute() or ".." in parsed.parts or "\\" in name or ":" in name:
        raise ValueError("Unsafe synthesis source path")
    path = root / name
    if not path.resolve().is_relative_to(root.resolve()) or path.is_symlink():
        raise ValueError("Source leaves repository")
    digest = sha(path)
    if expected is not None and digest != expected:
        raise ValueError(f"Source changed: {name}")
    return digest


def verified_analysis_inputs(root):
    """Fail before promotion if upstream audit/trace/transitive evidence is stale."""
    audit, residual, mechanism = (read(root / path) for path in (AUDIT, RESIDUAL, MECHANISM))
    if audit.get("schema_version") != TRACE_SCHEMA or audit.get("status") != "PASS":
        raise ValueError("Independent trace audit has unresolved discrepancies or unknown schema")
    if set(audit["cohorts"]) != set(COHORTS) or any(
        cohort.get("discrepancies") for cohort in audit["cohorts"].values()
    ):
        raise ValueError("Trace audit cohort/discrepancy contract failed")
    inventory = read(root / TRANSITIVE)
    verify_audit(root, (root / AUDIT).parent)
    verify_inventory(root, inventory)
    # These bytes were just independently verified. Historical source-code
    # versions remain in the inventory's Git-blob records, not compared against
    # newer working-tree implementation files.
    sources = dict(audit["source_checksums"])
    for row in inventory["files"]:
        name = row["path"]
        historical_source = name.startswith(("src/", "scripts/", "docs/", ".agents/")) or name == "publication/registry.json"
        if row["resolution"] == "working_tree_bytes" and not historical_source:
            if name in sources and sources[name] != row["sha256"]:
                raise ValueError(f"Conflicting audited source identities: {name}")
            sources[name] = row["sha256"]
    for document in (residual, mechanism):
        for field in ("source_checksums", "generator_source_checksums"):
            if not document.get(field):
                raise ValueError(f"Scientific review lacks bound {field}")
            for name, expected in document[field].items():
                actual = bound(root, name, expected)
                if name in sources and sources[name] != actual:
                    raise ValueError(f"Conflicting review source: {name}")
                sources[name] = actual
    for path in (AUDIT, RESIDUAL, MECHANISM, TRANSITIVE,
                 str(PurePosixPath(AUDIT).parent / "artifact_manifest.json")):
        sources[path] = bound(root, path)
    return audit, residual, mechanism, sources


def family_denominators(summary, family):
    jobs = [row for row in summary["jobs"] if row["experiment_id"] == family]
    attempts = [row for row in summary["attempts"] if row["experiment_id"] == family]
    return {"declared_jobs": len(jobs), "preserved_attempts": len(attempts),
            "status_counts": dict(Counter(row["status"] for row in jobs))}


def claim_denominators(identifier, audit, summaries, reviews, mechanism):
    """Actual claim population, not the total heterogeneous campaign size."""
    if identifier == "conditional_recovery":
        return {campaign: {
            "p2_declared_jobs": cohort["counts"]["declared_jobs"],
            "p2_preserved_attempts": cohort["p2_attempts"],
            "by_scenario": {scenario: {
                "declared_jobs": data["counts"]["declared_jobs"],
                "numeric_jobs": data["counts"]["numeric_jobs"],
                "sampler_passed_jobs": data["counts"]["gates"]["sampler"]["passed"],
                "joint_gate_passed_jobs": data["counts"]["joint_gate_passed_jobs"],
                "parameter_subset_counts": {parameter: {subset: metrics["numeric_count"]
                    for subset, metrics in subsets.items()} for parameter, subsets in data["metrics"].items()},
            } for scenario, data in cohort["scenarios"].items()},
        } for campaign, cohort in audit["cohorts"].items()}
    if identifier == "t0_mechanism":
        return {"initializer_only": {method: {"declared_seeds": len(data["seeds"]),
                                               "initial_points": len(data["initial_t0_days"])}
                                     for method, data in mechanism["initializer_draws"].items()},
                "historical_chains_retained": len(mechanism["historical_chain_means_days"]),
                "new_final_posterior_runs": 0}
    family = {"external_implementation": "PUB-03", "convergence_insufficient": "PUB-04",
              "observational_scope": "PUB-05"}[identifier]
    selected = [row for row in reviews if row["run_identity"]["job_id"].startswith(family + "__")]
    dimensions = [row["dimensions"] for row in selected]
    result = {**family_denominators(summaries[COHORTS[0]], family),
              "numerical_outputs": sum(row["manuscript_claim_permissions"]["describe_numerical_output_with_sampler_caveat"] for row in dimensions),
              "sampler_passed": sum(row["computational_screen"] == "passed" for row in dimensions),
              "ppc_passed": sum(row["predictive_screen"] == "passed" for row in dimensions),
              "sampler_unassessed": sum(row["computational_screen"] == "unassessed" for row in dimensions),
              "identity_controls_blocked": sum(row["manuscript_claim_permissions"]["demonstrate_identity_control_blocked_before_sampling"] for row in dimensions)}
    if family == "PUB-03":
        result["fits_by_declared_scenario"] = dict(Counter(row["run_identity"]["scenario_id"] for row in selected))
        result["independent_observational_datasets"] = 1
        result["dataset_scope"] = "Two implementation fits under one frozen same-input comparison contract; not independent datasets."
    if family == "PUB-05":
        result["distinct_selected_targets"] = len({row["run_identity"]["scenario_id"] for row in selected})
    return result


def parameter_regime_evidence(audit):
    """Explicit quantitative scope, not a newly tuned identification gate."""
    rows = []
    for campaign, cohort in audit["cohorts"].items():
        for scenario, values in cohort["scenarios"].items():
            for parameter, subsets in values["metrics"].items():
                rows.append({"campaign": campaign, "scenario": scenario, "parameter": parameter,
                             "supported_claim": "describe_fixed_truth_bias_width_and_ETI_coverage_with_denominators",
                             "support_status": "trace_verified_descriptive_evidence",
                             "quantitative_evidence": subsets,
                             "operational_yield": values["operational_yield"][parameter],
                             "unsupported_claims": ["universal_identifiability", "nominal_calibration_guaranteed", "valid_real_target_estimate"],
                             "limitations": "Post-result scope. Nonconverged numeric outputs retained and caveated; selected coverage is not unconditional coverage. No outcome-tuned cutoff grants recovery approval."})
    return rows


def prior_profile(config, model, protocol, *, numeric_output):
    """Extract recorded configuration; never infer priors from fitted values/truth."""
    config_keys = ("radius_prior_uniform", "radius_prior_median", "radius_prior_log_sigma",
                   "baseline_prior_mean", "baseline_prior_sigma", "transit_center_prior_mean_days",
                   "t0_prior_sigma_days", "infer_jitter", "jitter_error_multiplier",
                   "jitter_floor_fraction", "other_priors", "impact_parameter_prior",
                   "scaled_semimajor_axis_prior", "jitter_prior", "limb_darkening",
                   "period_days", "eccentricity", "fixed_orbit", "integrate_exposure", "oversample")
    model_keys = ("options", "prior_profile", "a_prior", "b_prior", "q1_q2_prior",
                  "baseline_prior_mean", "t0_prior_mean_days", "fixed_period_days", "eccentricity",
                  "radius_prior", "jitter_prior_scale_fraction", "jitter_unit_in_juliet",
                  "baseline_mapping", "phase_unit", "flux_unit", "family", "adapter_version")
    protocol_keys = ("inference_assumptions", "comparison_contract", "prior_rationale",
                     "known_design_assumptions", "independence_limit")
    external = "benchmark_sampling" in config
    settings = config.get("benchmark_sampling" if external else "sampling", {})
    return {"declared_inference_prior_fields": {key: config[key] for key in config_keys if key in config},
            "sealed_model_prior_metadata": {key: model[key] for key in model_keys if key in model},
            "frozen_protocol_prior_contracts": {key: protocol[key] for key in protocol_keys if key in protocol},
            "actual_sampler": {"engine": "juliet/dynesty" if external else "PyMC/NUTS",
                               "settings": {key: value for key, value in settings.items() if key != "cores"}},
            "likelihood": model.get("likelihood", config.get("likelihood")),
            "execution_scope": "numerical_output_produced" if numeric_output else "declared_input_only_rejected_before_fit",
            "units": {"r_b_a_q1_q2": "dimensionless", "t0_and_period": "day",
                      "baseline_and_white_jitter": "relative flux fraction; juliet native jitter conversion explicitly recorded"},
            "semantics": "Absent fields remain absent, not inferred from posterior or ground truth. Derived depth and duration have induced joint priors, not independent priors. Settings describe this family/variant, not historical scientific_003."}


def build_reviews(root, summaries):
    reviews, sources, profiles, protocols = [], {}, {}, {}
    for campaign, summary in summaries.items():
        for row in summary["attempts"]:
            if not row["authoritative"] or row["status"] not in {"COMPLETED", "COMPLETED_REJECTED"}:
                continue
            source_map = {}
            for filename in ("result.json", "inference_config.json", "input.csv", "completion_manifest.json", "job.json"):
                name = row["output_dir"] + "/" + filename
                source_map[name] = bound(root, name, summary["source_checksums"][name])
            result = read(root / row["output_dir"] / "result.json")
            config = read(root / row["output_dir"] / "inference_config.json")
            job = read(root / row["output_dir"] / "job.json")
            protocol_path = job["payload"]["protocol"]
            if protocol_path not in protocols:
                sources[protocol_path] = bound(root, protocol_path, summary["source_checksums"][protocol_path])
                protocols[protocol_path] = read(root / protocol_path)
            profile = prior_profile(config, result.get("model", {}), protocols[protocol_path],
                                    numeric_output=bool(result.get("parameters")))
            key = hashlib.sha256(json.dumps(profile, sort_keys=True, allow_nan=False).encode()).hexdigest()
            family_profiles = profiles.setdefault(row["experiment_id"], {})
            if key not in family_profiles:
                family_profiles[key] = {"profile_sha256": key, "definition": profile, "scopes": []}
            family_profiles[key]["scopes"].append({"campaign_id": campaign, "scenario_id": row["scenario_id"],
                                                    "run_id": campaign + "__" + row["job_id"],
                                                    "config_path": row["output_dir"] + "/inference_config.json",
                                                    "protocol_path": protocol_path})
            identity = {"campaign_id": campaign, **{key: row[key] for key in ("job_id", "scenario_id", "replicate_id", "attempt_index")}}
            identity["run_id"] = campaign + "__" + row["job_id"]
            reviews.append(evaluate_run(result, config, run_identity=identity,
                                        verified_sources=source_map, provenance_verified=True,
                                        family=row["experiment_id"], scenario=row["scenario_id"],
                                        declared_intervention=job["payload"].get("intervention")))
            sources.update(source_map)
    return reviews, sources, {"schema_version": "recorded-family-priors-v1",
                              "families": {family: list(rows.values()) for family, rows in profiles.items()},
                              "source_checksums": sources}


def calibration_rows(audit):
    rows = []
    for campaign in COHORTS:
        for scenario in SCENARIOS:
            data = audit["cohorts"][campaign]["scenarios"][scenario]
            for parameter in PARAMETERS:
                for population in ("all_numeric", "sampler_passed", "joint_gate_passed"):
                    metrics = data["metrics"][parameter][population]
                    for level, coverage in metrics["coverage"].items():
                        rows.append({"campaign": campaign, "scenario": scenario, "parameter": parameter,
                                     "population": population, "level": level,
                                     **{k: metrics[k] for k in ("bias", "absolute_bias", "relative_bias", "rmse", "mae", "mean_posterior_sd", "numeric_count", "declared_count")},
                                     "covered_count": coverage["covered_count"], "denominator": coverage["denominator"],
                                     "coverage": coverage["empirical_coverage"], "mean_width": coverage["mean_interval_width"],
                                     "wilson95": json.dumps(coverage["wilson95"]),
                                     "covered_and_passed_operational_yield": data["operational_yield"][parameter][level]["rate"]})
    return rows


def report_text(audit, summaries, reviews, residual, mechanism):
    lines = ["# Evidência científica auditada — TCC v2", "",
             "Esta revisão é posterior aos resultados. Preserva `tcc_evidence_v1`, as campanhas e `scientific_003`; não reclassifica seus gates históricos. Integridade, computação, predição e recuperação física são perguntas diferentes.", "",
             "## Inventário e integridade", "", "| Coorte | Jobs | Tentativas | Gate histórico aprovado | Rejeitado |", "|---|---:|---:|---:|---:|"]
    for name in COHORTS:
        s = summaries[name]
        lines.append(f"| {name} | {s['declared_jobs']} | {s['total_attempts']} | {s['status_counts'].get('COMPLETED',0)} | {s['status_counts'].get('COMPLETED_REJECTED',0)} |")
    lines += ["", "Jobs e tentativas não são denominadores intercambiáveis. O cancelamento antes do posterior permanece no histórico. Controles de identidade têm sampler/PPC não avaliados, não zero observado.",
              "A auditoria independente recalculou médias, SD amostral e quantis dos traces, sem importar o agregador original. Coortes de80 e400 permanecem separadas. Compare o inventário transitive e os recibos de restauração antes de afirmar disponibilidade independente.", "",
              "## Recuperação: regime e parâmetro", "",
              "Intervalos de caudas iguais (ETI), não HDI. Cobertura condicional em verdades fixas, não SBC. Wilson95 é pontual; não é controle simultâneo de múltiplas comparações. All-numeric inclui saídas numericamente rejeitadas e não presume posteriors exatos. CSV contém populações condicionadas e rendimento operacional, sem confundir os estimandos.", "",
              "| Coorte | Regime | Parâmetro | Viés | RMSE | Cobertos94 / numéricos | Largura94 |", "|---|---|---|---:|---:|---|---:|"]
    for name in COHORTS:
        for scenario in SCENARIOS:
            for parameter in PARAMETERS:
                m = audit["cohorts"][name]["scenarios"][scenario]["metrics"][parameter]["all_numeric"]
                c = m["coverage"]["0.94"]
                lines.append(f"| {name} | {scenario} | {parameter} | {m['bias']:.7g} | {m['rmse']:.7g} | {c['covered_count']}/{c['denominator']} | {c['mean_interval_width']:.7g} |")
    confirm = audit["cohorts"][COHORTS[1]]["scenarios"]
    weak = confirm["near_limit_long"]["metrics"]
    r = weak["r"]["all_numeric"]
    lines += ["", f"No regime near_limit_long, viés relativo de r={100*r['relative_bias']:.1f}%. Cobertura94 de a/Rs={weak['a']['all_numeric']['coverage']['0.94']['empirical_coverage']:.1%}, duração={weak['full_duration']['all_numeric']['coverage']['0.94']['empirical_coverage']:.1%}. Essa falha não é corrigida por condicionar aos aprovados; ver denominadores separados na tabela CSV.",
              "Nos regimes short profundo/raso, pequeno viés médio de raio coexiste com cobertura conservadora. Isso é evidência útil de desempenho condicional, não calibração universal. Impact parameter e geometria podem permanecer pouco informados. r e r² têm eventos de inclusão ligados pela transformação monótona e não são validações independentes.",
              "A prior Uniform(2,50) tem ETI94=[3.44,48.56], excluindo uma verdade3.3 dentro do suporte quando os dados não informam. É uma explicação-limite, não decomposição causal de todo viés. Alterar priors usando a verdade não seria uma correção legítima.", "",
              "## Benchmark e limitação numérica", "",
              "O benchmark histórico juliet foi executado sob contrato de dados/priors comparáveis, mas NUTS local não convergiu; ambas predições falharam no teste temporal. Concordância marginal é descritiva, não validação externa positiva nem validação retroativa de scientific_003 (prior de raio diferente).",
              f"Médias de t0 por cadeia local (dias), diretamente do trace: {mechanism['historical_chain_means_days']}. Warmup histórico disponível: {mechanism['historical_warmup_saved']}.",
              f"No experimento diagnóstico do inicializador, {mechanism['initializer_draws']['direct']['beyond_half_period']}/{len(mechanism['initializer_draws']['direct']['initial_t0_days'])} pontos diretos e {mechanism['initializer_draws']['standardized']['beyond_half_period']}/{len(mechanism['initializer_draws']['standardized']['initial_t0_days'])} padronizados ficaram além de meio período. Não são as posições iniciais históricas, nem um teste final de convergência. A verificação de logdensidade/Jacobiano/gradiente demonstra equivalência da alternativa, não sua eficácia final.",
              "O estudo complementar usa novos IDs/protocolo e mantém os runs antigos. Sua execução final e seus resultados não podem ser substituídos por pilotos.", "",
              "## Ablations: decisões e falhas", ""]
    negative = [v for v in reviews if v["dimensions"]["manuscript_claim_permissions"]["demonstrate_convergence_insufficient_for_ppc"] and v["run_identity"]["job_id"].startswith("PUB-04")]
    lines += [f"{len(negative)} controles PUB-04 têm sampler aprovado e PPC reprovado. Convergência, portanto, não foi suficiente para adequação. As três sistemáticas senoidais são determinísticas, não uma validação de GP. Baselines longos com divergências limitam efeitos pareados históricos: tabelas são descritivas, não efeitos físicos precisamente estabelecidos.",
              "Controles deliberados de input inválido demonstram bloqueio de identidade, não recuperação de parâmetros. Uma não cobertura individual não define falso positivo do gate. A falha agregada no regime fraco limita a promessa de recuperação de parâmetros mesmo com gate aprovado.", "",
              "## Resíduos observacionais existentes", "",
              "Revisão sem refit: ordem temporal real, três segmentos por alvo, gaps entre pontos selecionados, máscaras in/out por duração catalogada e projeções de deslocamento do template. As projeções são aproximações descritivas e não medições independentes de deriva de efeméride.", "",
              "| Alvo | Segmento | Pontos | Lag1 OOT | Lag1 após tendência linear |", "|---|---|---:|---:|---:|"]
    for target in residual["targets"]:
        for segment in target["segments"]:
            oot = segment["partitions"]["out_of_transit"]["selected_lag1"]
            detrend = segment["partitions"]["all"]["selected_lag1_after_linear_trend_removal"]
            lines.append(f"| {target['target']} | {segment['segment_id']} | {segment['rows']} | {oot if oot is None else format(oot,'.5g')} | {detrend if detrend is None else format(detrend,'.5g')} |")
    lines += ["", "Estrutura fora do trânsito e persistente após remoção linear descritiva enfraquece uma explicação exclusivamente por forma de trânsito ou simples tendência. Não distingue, sozinha, variabilidade estelar, sistemática determinística ou ruído estocástico. Seleção/thinning muda os pares disponíveis; a escala lag1 não é sempre a cadência instrumental. Os cinco alvos continuam rejeitados no contrato histórico; não foram trocados.", "",
              "## Escopo de afirmações e reprodução", "",
              "`run_evaluations.json` separa bytes/proveniência, sampler, PPC, escala física, informação por parâmetro e permissões de claims. Razão SD posterior/prior é exploratória, sem cutoff ajustado; não é novo gate de identificabilidade. `claims.json` vincula cada conclusão às fontes.",
              "M5 continua jitter branco independente. M6 não foi executado e não é requisito para entregar esta evidência TCC limitada. Não há novidade absoluta, generalização populacional ou garantia de exatidão pelos gates. Ver metodologia, limitações e bibliografia.",
              "Restauração exata dos bytes, regeneração de relatórios e nova reprodução numérica são verificações diferentes. Bundle local não é arquivo público/DOI. `validate_publication_release.py` separa evidência inválida (exit2) de pendência editorial/arquivamento explicitamente identificada (exit1). Consulte os recibos finais, não assuma aprovação a partir desta síntese."]
    return "\n".join(lines) + "\n"


def coverage_plot_values(cells, levels):
    """Plot pointwise uncertainty; unavailable is NaN, never apparent zero."""
    import math
    values, lower, upper = [], [], []
    for level in levels:
        value = cells[level]["empirical_coverage"]
        interval = cells[level]["wilson95"]
        if value is None or interval is None:
            values.append(math.nan)
            lower.append(math.nan)
            upper.append(math.nan)
            continue
        if interval[0] > value + 1e-12 or interval[1] < value - 1e-12:
            raise ValueError("Coverage interval excludes its reported point estimate")
        values.append(value)
        lower.append(max(0.0, value - interval[0]))
        upper.append(max(0.0, interval[1] - value))
    return values, [lower, upper]


def figures(output, audit, mechanism):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    levels = ("0.5", "0.8", "0.94")
    fig, axes = plt.subplots(7, 2, figsize=(11, 19), sharex=True, sharey=True)
    for column, campaign in enumerate(COHORTS):
        for row, parameter in enumerate(PARAMETERS):
            ax = axes[row, column]
            ax.plot([0,1], [0,1], color="black", lw=.7, ls=":")
            for scenario in SCENARIOS:
                cells = audit["cohorts"][campaign]["scenarios"][scenario]["metrics"][parameter]["all_numeric"]["coverage"]
                values, errors = coverage_plot_values(cells, levels)
                ax.errorbar([float(x) for x in levels], values, yerr=errors,
                            marker="o", markersize=3, capsize=2, alpha=.8, label=scenario)
            ax.set(xlim=(.45,1), ylim=(-.03,1.03), title=f"{parameter}: {campaign}")
            ax.grid(alpha=.2)
    axes[0,0].legend(fontsize=7)
    fig.supxlabel("Nominal ETI coverage")
    fig.supylabel("Fixed-truth empirical coverage (all numeric, including rejected)")
    fig.tight_layout()
    fig.savefig(output / "coverage_trace_verified.png", dpi=130, metadata={"Software":"publication synthesis v2"})
    plt.close(fig)
    fig, ax = plt.subplots(figsize=(7,3))
    ax.scatter(range(len(mechanism["historical_chain_means_days"])), mechanism["historical_chain_means_days"])
    ax.axhline(0, color="gray", ls=":")
    ax.set(xlabel="Historical benchmark chain (all retained)", ylabel="Mean t0 [days]", title="Retained adjacent-period numerical trapping; not physical displacement")
    fig.tight_layout()
    fig.savefig(output / "historical_t0_chains.png", dpi=150)
    plt.close(fig)


def source_inventory(root, output):
    relative = output.resolve().relative_to(root.resolve()).as_posix()
    return {"tcc_sources": [relative + "/" + path.name for path in sorted(output.iterdir()) if path.is_file()],
            "supporting_audits": [AUDIT, RESIDUAL, MECHANISM, TRANSITIVE],
            "historical_sources_unchanged": ["reports/publication_synthesis/tcc_evidence_v1",
                                             *[f"reports/publication_campaign/{campaign}" for campaign in COHORTS]],
            "bibliography": "docs/publication/BIBLIOGRAPHY.md",
            "reproduction": "python scripts/build_publication_synthesis_v2.py --output <NEW_REPOSITORY_RELATIVE_DIRECTORY>; "
                            + f"python scripts/build_publication_synthesis_v2.py --check --output {relative}"}


def build(root: Path, output: Path):
    if not output.resolve().is_relative_to(root.resolve()):
        raise ValueError("Synthesis output must be inside the repository for portable source inventory")
    if output.exists():
        raise FileExistsError("Use a NEW synthesis version or explicitly chosen new output directory")
    audit, residual, mechanism, sources = verified_analysis_inputs(root)
    summaries = {name: read(root / f"reports/publication_campaign/{name}/campaign_summary.json") for name in COHORTS}
    reviews, review_sources, family_priors = build_reviews(root, summaries)
    sources.update(review_sources)
    for name in (AUDIT, RESIDUAL, MECHANISM, "publication/validation/external_audit_closure_v1/protected_snapshot.json",
                 "publication/validation/external_audit_closure_v1/raw_index_restoration.json",
                 "docs/publication/BIBLIOGRAPHY.md", "docs/publication/NOVELTY_MATRIX.json",
                 "src/publication/residual_review.py", "scripts/audit_observational_residuals.py",
                 "src/publication/t0_mechanism_audit.py", "scripts/audit_t0_initialization.py"):
        sources[name] = bound(root, name)
    for name in COHORTS:
        path = f"reports/publication_campaign/{name}/campaign_summary.json"
        sources[path] = bound(root, path)
    claims = []
    definitions = [
        ("conditional_recovery", "regime_and_parameter_limited", AUDIT, "Repeated coverage, bias and uncertainty quantified from traces; useful radius recovery in short regimes coexists with conservative intervals and weak-regime geometry failure.", ["universal nominal calibration", "SBC", "gate approval guarantees parameter accuracy"]),
        ("external_implementation", "descriptive_only", "reports/publication_campaign/tcc_campaign_v1/PUB-03/benchmark.json", "Independent implementation completed under a comparability contract; positive validation remains unsupported due to local sampler and temporal predictive failures.", ["external astrophysical validation", "benchmark validates scientific_003"]),
        ("convergence_insufficient", "negative_control_evidence", "reports/publication_campaign/tcc_campaign_v1/PUB-04/ablation.json", "Predeclared controls exhibit sampler-pass/PPC-fail; identity controls are blocked before inference.", ["all gates perfectly calibrated", "unqualified precise ablation effects"]),
        ("observational_scope", "negative_applicability_evidence", RESIDUAL, "All selected targets retained; existing residual review quantifies segment/time structure without refitting or automatic GP attribution.", ["five planets physically validated", "population generalization", "GP solution demonstrated"]),
        ("t0_mechanism", "diagnostic_not_final_efficacy", MECHANISM, "Initializer operates in direct days; periodic likelihood and severe alias prior penalty verified. Standardized coordinate is density-equivalent; final efficacy requires new prospective runs.", ["historical initial states reconstructed", "old rejected chain can be removed", "new sampler efficacy already established"]),
    ]
    for identifier, status, source, text, unsupported in definitions:
        sources[source] = bound(root, source)
        claims.append({"claim_id": identifier, "status": status, "scope": "historical contracts and explicitly post-result audit",
                       "sources": {source: sources[source]}, "supported_text": text, "unsupported_claims": unsupported,
                       "denominators": claim_denominators(identifier, audit, summaries, reviews, mechanism),
                       "campaign_context": {name: {"jobs": summaries[name]["declared_jobs"], "attempts": summaries[name]["total_attempts"]} for name in COHORTS}})
    claims[0]["parameter_regime_evidence"] = parameter_regime_evidence(audit)
    negative = [row for row in reviews if row["run_identity"]["job_id"].startswith("PUB-04") and row["dimensions"]["manuscript_claim_permissions"]["demonstrate_convergence_insufficient_for_ppc"]]
    claims[2]["run_authorizations"] = [{"run_id": row["run_identity"]["run_id"], "permission": "demonstrate_convergence_insufficient_for_ppc"} for row in negative]
    output.mkdir(parents=True)
    write(output / "run_evaluations.json", reviews)
    write(output / "priors_by_family.json", family_priors)
    write(output / "claims.json", {"schema_version": "tcc-claims-v2", "evaluator_version": EVALUATOR_VERSION, "claims": claims, "run_evaluations_path": "run_evaluations.json"})
    table(output / "calibration_metrics.csv", calibration_rows(audit))
    write(output / "summary.json", {"campaigns": {name: {key: summary[key] for key in ("declared_jobs", "total_attempts", "status_counts")} for name, summary in summaries.items()}, "evaluations": len(reviews), "convergence_insufficient_ablation_count": len(negative), "claim_statuses": dict(Counter(row['status'] for row in claims))})
    (output / "REPORT.md").write_text(report_text(audit, summaries, reviews, residual, mechanism), encoding="utf-8", newline="\n")
    for filename in ("METHODOLOGY.md", "LIMITATIONS.md", "MANUSCRIPT_DRAFT.md"):
        source = "docs/publication/v2_sources/" + filename
        sources[source] = bound(root, source)
        shutil.copyfile(root / source, output / filename)
    figures(output, audit, mechanism)
    write(output / "captions.json", {
        "coverage_trace_verified.png": "Fixed-truth equal-tailed coverage from independent trace calculations. Both cohorts separate; all numeric outputs retained including sampler rejections. Bars are pointwise Wilson95, not simultaneous confidence. Widths and conditioned denominators are in CSV; lines are descriptive, not calibration tests. r² and r inclusion are not independent evidence. Unavailable values are not plotted as zero.",
        "historical_t0_chains.png": "All four historical local benchmark chains. Displaced chain is a numerical alias, not a physical transit-time measurement. No chain was removed or wrapped."})
    write(output / "SOURCE_INVENTORY.json", source_inventory(root, output))
    generator = {name: bound(root, name) for name in ("src/publication/synthesis_v2.py", "src/publication/claim_authorization.py", "scripts/build_publication_synthesis_v2.py")}
    write(output / "artifact_manifest.json", {"schema_version": "tcc-evidence-v2", "source_checksums": sources,
                                              "generator_source_checksums": generator,
                                              "artifacts": {p.name: sha(p) for p in output.iterdir() if p.is_file()}})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(OUTPUT))
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if args.check:
        from publication.campaign_release import validate_synthesis
        print(json.dumps(validate_synthesis(root, args.output.as_posix()), indent=2))
    else:
        build(root, root / args.output)
        print(json.dumps({"output": str(args.output), "historical_outputs_modified": False}))


if __name__ == "__main__":
    main()
