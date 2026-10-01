"""Bounded, byte-verified synthesis of existing TCC evidence; no inference.

Existing trace-verified calibration and comparison artifacts are reused, not
recomputed or pooled. Only accounting, presentation and claim scope change.
"""
from __future__ import annotations

import csv
import json
import platform
import shutil
from collections import Counter
from pathlib import Path

from publication.campaign_plan import build_plan
from publication.claim_authorization import EVALUATOR_VERSION, evaluate_run
from publication.evidence_archive import EvidenceWalker, digest_file, safe_file
from publication.gate_accounting import COMPONENTS, assess_gates, gate_counts
from repository_tools.raw_byte_audit import filesystem_path

COHORTS = ("tcc_campaign_v1", "tcc_calibration_confirmatory_v1", "tcc_numerical_complement_v4")
INCIDENT = "tcc_numerical_complement_v3"
OLD = "reports/publication_synthesis/tcc_evidence_v2"
TRACE_AUDIT = "publication/validation/tcc_closure_v1/complement_trace_review_final.json"


def read(path):
    return json.loads(filesystem_path(path).read_text(encoding="utf-8"))


def write(path, payload):
    with filesystem_path(path).open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n")


def table(path, rows):
    with filesystem_path(path).open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def recount(root: Path, campaign: str, *, invalidations=None):
    """Use the frozen job population and current state, never a success-only list.

    Caller verifies the transitive graph first. State->completion->result seals
    are checked again here, so a changed state cannot adopt another posterior.
    """
    config = "tcc_final_campaign.json" if campaign == COHORTS[0] else campaign + ".json"
    plan = build_plan(root, Path("configs/publication") / config, verify_execution_sources=False)
    if plan["preflight_errors"]:
        raise ValueError("Post-processing declaration validation failed: " + "; ".join(plan["preflight_errors"]))
    state_path = f"artifacts/publication_campaign/{campaign}/campaign_state.json"
    state = read(root / state_path)
    if state["campaign_id"] != campaign or state["scientific_config_sha256"] != plan["scientific_config_sha256"]:
        raise ValueError("State/declaration identity mismatch")
    if set(state["jobs"]) != {job["job_id"] for job in plan["jobs"]}:
        raise ValueError("Undeclared/missing jobs")
    old_path = f"reports/publication_campaign/{campaign}/campaign_summary.json"
    original = read(root / old_path)
    sources = {state_path: digest_file(root / state_path), old_path: digest_file(root / old_path)}
    jobs, attempts, evaluations = [], [], []
    for declaration in plan["jobs"]:
        job = state["jobs"][declaration["job_id"]]
        for key in ("seeds", "output_dir", "experiment_id", "scenario_id", "replicate_id", "run_id"):
            if job[key] != declaration[key]:
                raise ValueError(f"Frozen job changed {key}")
        result = None
        for index, attempt in enumerate(job["attempts"]):
            if attempt["attempt_index"] != index or attempt.get("seeds", job["seeds"]) != job["seeds"]:
                raise ValueError("Attempt order/seed changed")
            outcome = None
            manifest_path = attempt["output_dir"] + "/completion_manifest.json"
            expected = attempt.get("completion_manifest_sha256")
            if expected:
                if digest_file(safe_file(root, manifest_path)) != expected:
                    raise ValueError("Registered completion changed")
                seal = read(root / manifest_path)
                outcome = read(root / attempt["output_dir"] / "result.json")
                if seal["status"] != attempt["status"] or seal.get("gates", {}) != outcome.get("gates", {}):
                    raise ValueError("Completion/result decision mismatch")
                sources[manifest_path] = expected
                sources.update({attempt["output_dir"] + "/" + name: sha for name, sha in seal["artifacts"].items()})
                if index == len(job["attempts"]) - 1 and attempt["status"] == job["status"]:
                    result = outcome
            elif attempt["status"] in {"COMPLETED", "COMPLETED_REJECTED"}:
                raise ValueError("Scientific completion without seal")
            incident = (invalidations or {}).get(job["job_id"], {})
            assessment = assess_gates(outcome, status=attempt["status"], verified=bool(expected),
                                      mode=plan["mode"], fixture=declaration["payload"].get("kind") == "fixture", invalidated=incident)
            attempts.append({"job_id": job["job_id"], "experiment_id": job["experiment_id"],
                             **attempt, "gate_assessment": assessment})
        if job["status"] in {"COMPLETED", "COMPLETED_REJECTED"} and result is None:
            raise ValueError("Missing authoritative result")
        assessment = assess_gates(result, status=job["status"], verified=result is not None, mode=plan["mode"],
                                  invalidated=(invalidations or {}).get(job["job_id"], {}))
        row = {key: job[key] for key in ("job_id", "experiment_id", "scenario_id", "replicate_id", "run_id", "status", "seeds", "output_dir")}
        row["gate_assessment"] = assessment
        row["input_sha256"] = (result or {}).get("input_sha256")
        jobs.append(row)
        if result is not None:
            directory = job["attempts"][-1]["output_dir"]
            config_path = directory + "/inference_config.json"
            run_sources = {directory + "/result.json": sources[directory + "/result.json"],
                           directory + "/completion_manifest.json": sources[directory + "/completion_manifest.json"]}
            config_data = read(root / config_path)
            run_sources[config_path] = digest_file(root / config_path)
            evaluations.append(evaluate_run(result, config_data, run_identity={"campaign_id": campaign,
                **{key: row[key] for key in ("job_id", "run_id", "scenario_id", "replicate_id")}}, verified_sources=run_sources,
                provenance_verified=True, family=row["experiment_id"], scenario=row["scenario_id"],
                declared_intervention=declaration["payload"].get("intervention"), status=row["status"],
                mode=plan["mode"], invalidated=(invalidations or {}).get(job["job_id"])))
    summary = {"schema_version": "publication-campaign-aggregate-v2", "campaign_id": campaign,
               "mode": plan["mode"], "declared_jobs": len(jobs), "total_attempts": len(attempts),
               "status_counts": dict(Counter(row["status"] for row in jobs)),
               "technical_failures": sum(row["status"] == "FAILED_TECHNICAL" for row in jobs),
               "gate_counts": gate_counts([row["gate_assessment"] for row in jobs]),
               "attempt_gate_counts": gate_counts([row["gate_assessment"] for row in attempts]),
               "gate_counts_by_family": {family: gate_counts([row["gate_assessment"] for row in jobs if row["experiment_id"] == family])
                                        for family in sorted({row["experiment_id"] for row in jobs})},
               "controller": {"historical_snapshot": original["campaign_state_status"], "assessment_current_state": state["status"]},
               "complete_declared_batch": all(row["status"] in {"COMPLETED", "COMPLETED_REJECTED"} for row in jobs),
               "deprecated_fields": {"computational_gates_passed_count": "Historical joint-pass alias; not sampler approval"},
               "computational_gates_passed_count": original["computational_gates_passed_count"],
               "source_checksums": sources, "jobs": jobs, "attempts": attempts}
    return summary, evaluations


def independent_counts(root, campaign):
    """Separate original-result loop: does not call assess_gates/gate_counts.

    Used on the all-numeric, finished v4 population. General failure accounting
    is regression-tested separately; this check must not reuse the counter.
    """
    state = read(root / f"artifacts/publication_campaign/{campaign}/campaign_state.json")
    families = {}
    for job in state["jobs"].values():
        if job["status"] not in {"COMPLETED", "COMPLETED_REJECTED"}:
            raise ValueError("Independent v4 check requires all jobs finished")
        result = read(root / job["attempts"][-1]["output_dir"] / "result.json")
        if not result.get("parameters"):
            raise ValueError("Independent v4 check requires actual diagnostic outputs")
        family = families.setdefault(job["experiment_id"], {"jobs": 0, **dict.fromkeys(COMPONENTS, 0)})
        family["jobs"] += 1
        for name in COMPONENTS:
            flag = result["gates"]["scientific" if name == "joint" else name]
            if type(flag) is not bool:
                raise ValueError("Non-Boolean recorded gate")
            family[name] += int(flag)
    return {"families": families, "total": {name: sum(row[name] for row in families.values()) for name in ("jobs", *COMPONENTS)},
            "method": "Direct original result.json loop, independent of report counters"}


def gate_report(summary):
    lines = [f"# Corrected gate accounting: {summary['campaign_id']}", "",
             f"Mode: {summary['mode']}. Historical controller snapshot: {summary['controller']['historical_snapshot']}; current controller state: {summary['controller']['assessment_current_state']}.",
             f"Declared jobs: {summary['declared_jobs']}; preserved attempts: {summary['total_attempts']}; technical failures: {summary['technical_failures']}. Completion is not scientific acceptance.", "",
             "| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |", "|---|---|---:|---:|---:|---:|---:|---:|"]
    for family, counts in {"ALL": summary["gate_counts"], **summary["gate_counts_by_family"]}.items():
        for component, c in counts.items():
            lines.append(f"| {family} | {component} | {c['declared']} | {c['evaluated']} | {c['passed']} | {c['rejected']} | {c['unassessed']} | {c['invalidated']} |")
    lines += ["", "Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.",
              "The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision."]
    return "\n".join(lines) + "\n"


def gate_figure(path, summaries):
    """Small vector scientific figure with explicit populations/denominators."""
    lines = ['<svg xmlns="http://www.w3.org/2000/svg" width="900" height="360" viewBox="0 0 900 360">',
             '<rect width="900" height="360" fill="white"/>',
             '<text x="30" y="25" font-family="sans-serif" font-size="16">v4 assessed component approval (all 24 declared fits; not independent datasets)</text>']
    counts = summaries[COHORTS[-1]]["gate_counts_by_family"]
    for i, (family, row) in enumerate(counts.items()):
        y = 70 + i * 90
        lines.append(f'<text x="20" y="{y+15}" font-family="sans-serif">{family}</text>')
        for j, name in enumerate(("sampler", "ppc", "joint")):
            c = row[name]
            x = 135 + j * 250
            w = 180 * c["passed"] / c["evaluated"] if c["evaluated"] else 0
            lines += [f'<rect x="{x}" y="{y}" width="180" height="20" fill="#eeeeee"/>',
                      f'<rect x="{x}" y="{y}" width="{w:.6f}" height="20" fill="#387c99"/>',
                      f'<text x="{x}" y="{y+40}" font-family="sans-serif" font-size="13">{name}: {c["passed"]}/{c["evaluated"]} assessed; N={c["declared"]}</text>']
    lines.append('<text x="135" y="345" font-family="sans-serif" font-size="12">Bar scale 0–100% of evaluated diagnoses. Sampler approval is not predictive adequacy.</text></svg>')
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(root: Path, output: Path):
    if not output.resolve().is_relative_to(root.resolve()) or output.exists():
        raise FileExistsError("Select a NEW repository-relative synthesis destination")
    roots = [OLD + "/artifact_manifest.json", "publication/baseline/manifest.json",
             *[f"reports/publication_campaign/{campaign}/artifact_manifest.json" for campaign in (*COHORTS, INCIDENT)], TRACE_AUDIT]
    inventory = EvidenceWalker(root).build(roots)
    trace_review = read(root / TRACE_AUDIT)
    if trace_review["status"] != "passed":
        raise ValueError("Complement trace review failed")
    invalidations = {row["job_id"]: {"ppc": "v3 free-RV conditioning incident", "joint": "depends on invalidated PPC"}
                     for row in trace_review["campaigns"][INCIDENT]["traces"] if row["predictive_invalidated"]}
    summaries, reviews = {}, []
    for campaign in (*COHORTS, INCIDENT):
        summary, evaluations = recount(root, campaign, invalidations=invalidations if campaign == INCIDENT else None)
        summaries[campaign] = summary
        reviews += evaluations
    independent = independent_counts(root, COHORTS[-1])
    for family, direct in independent["families"].items():
        expected = summaries[COHORTS[-1]]["gate_counts_by_family"][family]
        if any(direct[name] != expected[name]["passed"] for name in COMPONENTS) or direct["jobs"] != expected["joint"]["declared"]:
            raise ValueError("Independent gate check disagrees")
    sources = {name: digest_file(root / name) for name in roots}
    sources["publication/validation/external_audit_closure_v1/numerical_v3_predictive_incident.md"] = digest_file(root / "publication/validation/external_audit_closure_v1/numerical_v3_predictive_incident.md")
    output.mkdir(parents=True)
    write(output / "independent_gate_check.json", independent)
    count_rows = []
    for campaign, summary in summaries.items():
        destination = output / "campaigns" / campaign
        destination.mkdir(parents=True)
        write(destination / "campaign_summary.json", summary)
        filesystem_path(destination / "REPORT.md").write_text(gate_report(summary), encoding="utf-8", newline="\n")
        write(destination / "artifact_manifest.json", {"schema_version": "publication-derived-v1",
            "source_checksums": summary["source_checksums"],
            "artifacts": {name: digest_file(destination / name) for name in ("campaign_summary.json", "REPORT.md")}})
        for family, counts in {"ALL": summary["gate_counts"], **summary["gate_counts_by_family"]}.items():
            for component, c in counts.items():
                count_rows.append({"campaign": campaign, "family": family, "component": component,
                                   **{key: c[key] for key in ("declared", "evaluated", "passed", "rejected", "unassessed", "invalidated", "recorded_passed", "final_evidence_passed", "pass_rate_evaluated", "pass_rate_all_declared")}})
    table(output / "gate_counts.csv", count_rows)
    write(output / "run_evaluations.json", reviews)
    for name in ("calibration_metrics.csv", "coverage_trace_verified.png", "historical_t0_chains.png", "priors_by_family.json", "METHODOLOGY.md"):
        sources[OLD + "/" + name] = digest_file(root / OLD / name)
        shutil.copyfile(root / OLD / name, output / name)
    # Keep paired estimates and all local comparisons intact, with their original qualifications.
    complement = output / "complement"
    complement.mkdir()
    comparisons = []
    for family in ("PUB-02", "PUB-03", "PUB-04"):
        original = f"reports/publication_campaign/{COHORTS[-1]}/{family}/numerical_study.json"
        sources[original] = digest_file(root / original)
        study = read(root / original)
        write(complement / (family + ".json"), study)
        for comparison in study.get("comparisons", []):
            for parameter, metrics in comparison["comparison"]["parameters"].items():
                comparisons.append({"local_job_id": comparison["local_job_id"], "parameter": parameter,
                                    "standardized_mean_difference": metrics["standardized_mean_difference"],
                                    "empirical_cdf_distance": metrics["empirical_cdf_distance"],
                                    "eti94_overlap_jaccard": metrics["intervals"]["0.94"]["overlap_jaccard"],
                                    "eti94_width_ratio_external_local": metrics["intervals"]["0.94"]["width_ratio_external_local"],
                                    "independent_external_refits": 0, "scientific_promotion": False})
    table(output / "benchmark_comparisons.csv", comparisons)
    populations = {}
    for family in ("PUB-02", "PUB-03", "PUB-04"):
        selected = [row for row in summaries[COHORTS[-1]]["jobs"] if row["experiment_id"] == family]
        populations[family] = {"fits": len(selected), "distinct_input_hashes": len({row["input_sha256"] for row in selected}),
                               "new_external_refits": 0, "gate_counts": summaries[COHORTS[-1]]["gate_counts_by_family"][family]}
    write(output / "summary.json", {"schema_version": "tcc-synthesis-populations-v3",
        "campaigns": {name: {key: value for key, value in data.items() if key not in {"jobs", "attempts", "source_checksums"}}
                      for name, data in summaries.items()}, "v4_populations": populations,
        "independent_gate_check": independent, "old_metrics_reused_byte_exact": True,
        "postprocessing_environment": {"python": platform.python_version(), "platform": platform.system(), "algorithm": "stdlib only; no inference"},
        "new_final_inference_runs": 0, "no_population_pooling": True})
    definitions = [
        ("conditional_recovery", "fixed_truth_regime_limited", OLD + "/calibration_metrics.csv", "Useful radius recovery in supported short-cadence regimes coexists with conservative coverage and weak-information geometric undercoverage; fixed truths, not SBC or universal calibration.", {name: {"p2_jobs": summaries[name]["gate_counts_by_family"]["PUB-02"]["joint"]["declared"]} for name in COHORTS[:2]}, ["universal calibration", "all parameters identified by passed gate"]),
        ("standardized_coordinate", "small_paired_result_no_general_superiority", "reports/publication_campaign/" + COHORTS[-1] + "/PUB-02/numerical_study.json", "Density-equivalent standardized t0 does not demonstrate general sampler superiority in this small paired cohort.", populations["PUB-02"], ["12 independent simulated datasets", "general superiority"]),
        ("independent_implementation", "computational_proximity_not_astrophysical_validation", "reports/publication_campaign/" + COHORTS[-1] + "/PUB-03/numerical_study.json", "All local refits pass the sampler; temporal PPC fails. Posterior proximity under the comparison contract is descriptive; the same historical external posterior is reused.", populations["PUB-03"], ["three independent external benchmarks", "validated astrophysical truth", "validates scientific_003 whose prior differs"]),
        ("ablation_numerical", "qualified_descriptive_contrasts", "reports/publication_campaign/" + COHORTS[-1] + "/PUB-04/numerical_study.json", "High-accuracy integrated references pass; exposure-off variants fail sampling. No jointly sampler-supported physical exposure effect is established.", populations["PUB-04"], ["precisely estimated physical effects using rejected posterior"]),
        ("convergence_insufficient", "negative_control_evidence", "reports/publication_campaign/tcc_campaign_v1/PUB-04/ablation.json", "Predeclared controls demonstrate sampler-pass but PPC-fail; identity controls fail before sampling, not observed sampler failure.", summaries[COHORTS[0]]["gate_counts_by_family"]["PUB-04"], ["perfectly calibrated gates", "single noncoverage defines gate false positive"]),
        ("observational_scope", "all_preselected_targets_retained_negative_scope", "publication/validation/residual_review_v2/audit.json", "All five systems remain reported with predictive limitations. Temporal structure does not uniquely identify stochastic GP noise.", summaries[COHORTS[0]]["gate_counts_by_family"]["PUB-05"], ["five planets scientifically validated", "population inference", "correlated noise solved"]),
        ("v3_incident", "historical_audit_only", TRACE_AUDIT, "Direct-coordinate traces are outside this specific conditioning incident; standardized PPC and dependent joint evidence are invalidated, not reclassified as observed failures.", trace_review["campaigns"][INCIDENT]["counts"], ["invalidated PPC is negative scientific evidence", "partial v3 adds calibration replicates"]),
    ]
    claims = []
    for identifier, status, source, text, denominators, forbidden in definitions:
        sources[source] = digest_file(root / source)
        claims.append({"claim_id": identifier, "status": status, "scope": "Frozen cohorts and post-result bounded review; no pooling",
                       "sources": {source: sources[source]}, "supported_text": text, "denominators": denominators, "unsupported_claims": forbidden})
    negative = [row for row in reviews if row["run_identity"]["campaign_id"] == COHORTS[0]
                and row["run_identity"]["job_id"].startswith("PUB-04")
                and row["dimensions"]["manuscript_claim_permissions"]["demonstrate_convergence_insufficient_for_ppc"]]
    claims[4]["run_authorizations"] = [{"run_id": row["run_identity"]["run_id"], "permission": "demonstrate_convergence_insufficient_for_ppc"} for row in negative]
    write(output / "claims.json", {"schema_version": "tcc-claims-v3", "evaluator_version": EVALUATOR_VERSION,
                                   "claims": claims, "run_evaluations_path": "run_evaluations.json"})
    report = ["# Fontes canônicas para reconstrução do TCC — v3", "",
              "Fechamento pós-resultados: nenhuma inferência final nova. scientific_003 e as sínteses v1/v2 permanecem históricos e inalterados. Este pacote corrige a contagem dos componentes e incorpora o complemento v4 concluído, sem alterar os gates científicos.", "",
              "## Campanhas e populações (não somar como replicações independentes)", ""]
    for name, data in summaries.items():
        report += [f"### {name}", "", gate_report(data).split("\n", 2)[2]]
    report += ["## Resultados e interpretação", ""]
    report += [f"- {claim['supported_text']}" for claim in claims]
    radius_comparisons = [row for row in comparisons if row["parameter"] == "r"]
    differences = [row["standardized_mean_difference"] for row in radius_comparisons]
    width_ratios = [row["eti94_width_ratio_external_local"] for row in radius_comparisons]
    report += ["", f"Nas comparações locais de Rp/Rs, diferença padronizada de médias varia entre {min(differences):.5g} e {max(differences):.5g}; razão de larguras ETI94 externo/local entre {min(width_ratios):.5g} e {max(width_ratios):.5g}. Valores descritivos sob contrato, sem teste de equivalência ou promoção astrofísica."]
    p2_jobs = [row for row in summaries[COHORTS[-1]]["jobs"] if row["experiment_id"] == "PUB-02"]
    for variant in sorted({row["scenario_id"].split("__")[-1] for row in p2_jobs}):
        selected = [row for row in p2_jobs if row["scenario_id"].endswith("__" + variant)]
        passed = sum(row["gate_assessment"]["components"]["sampler"]["current_status"] == "passed" for row in selected)
        report.append(f"PUB-02, {variant}: sampler aprovado em {passed}/{len(selected)} ajustes; mesmas realizações pareadas, não superioridade geral.")
    report += ["", f"Controles históricos com sampler aprovado e PPC reprovado: {len(negative)}. O baseline scientific_003 tem identidade Gold e input preservados no publication/baseline/manifest.json; não é retroativamente aprovado/reprovado pelos protocolos novos.",
               f"v4: PUB-02 tem {populations['PUB-02']['fits']} ajustes em {populations['PUB-02']['distinct_input_hashes']} datasets pareados; PUB-04 tem {populations['PUB-04']['fits']} ajustes em {populations['PUB-04']['distinct_input_hashes']} datasets; PUB-03 tem {populations['PUB-03']['fits']} ajustes locais em {populations['PUB-03']['distinct_input_hashes']} input, com uma posterior externa histórica, sem novo ajuste externo.",
               "", "## Calibração e física", "", "calibration_metrics.csv e coverage_trace_verified.png são reutilizados byte a byte da auditoria independente dos 80 e 400 traces. Mantêm bias, RMSE, SD, ETI50/80/94, Wilson95, larguras, populações all-numeric/sampler-pass/joint-pass e rendimento operacional. Sobre/subcobertura em verdades fixas não é SBC; populações selecionadas pelo gate não estimam cobertura incondicional. Rp/Rs e depth=r² não são validações independentes. Geometria e duração podem continuar pouco identificadas, inclusive com gate aprovado.",
               "", "## Benchmark e ablações", "", "benchmark_comparisons.csv contém todas as três comparações marginais com diferenças padronizadas, distância CDF, overlap e razões de largura ETI94 (não HDI). Proximidade computacional sob hipóteses comparáveis não resolve inadequação temporal da likelihood. Os contrastes completos, inclusive rejeitados, estão em complement/PUB-04.json; são descritivos, não estimativas físicas definitivas quando um sampler falha.",
               "", "## Preservação e prontidão", "", "A: fontes auditáveis para redigir/revisar o TCC, com escopo restrito. B: disponibilidade/restauração local requer o recibo versionado de archive; não equivale à reprodução independente de MCMC. C: arquivo público durável, direitos/privacidade e DOI continuam pendentes. D: este manuscript draft ainda exige revisão editorial e adequação ao periódico. M6 permanece fora deste fechamento e ruído correlacionado não foi resolvido. Não há garantia de nota ou aceitação.",
               "", "## Reprodução e validação (sem inferência)", "", "```sh", "python scripts/close_tcc_evidence.py --build --output reports/publication_synthesis/<NEW_VERSION>",
               "python scripts/close_tcc_evidence.py --check", "python scripts/close_tcc_evidence.py --check-protected", "python scripts/close_tcc_evidence.py --verify-original", "```", "",
               "O destino precisa ser novo; nunca sobrescrever versões seladas. SOURCE_INVENTORY.json lista exatamente fontes, tabelas, figuras, captions, claims e auditorias para a próxima reconstrução do Word. BIBLIOGRAPHY.md mantém as fontes primárias e limita as alegações de novidade."]
    (output / "REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8", newline="\n")
    manuscript = ["# Manuscript draft — bounded existing-evidence version", "", "## Contribution and positioning", "",
                  "An empirical evaluation of a validation-gated, content-addressed reproducible Bayesian transit workflow. The contribution is auditable integration and quantified scope/failure transparency, not a priority claim over exoplanet, juliet or allesfitter. See the primary-source novelty matrix and bibliography.", "", "## Methods", "",
                  "Physical transit likelihood with measured heteroscedastic error plus independent white jitter; finite exposure integration; fixed period/circular assumptions and recorded limb-darkening priors. Ground truth stays separate from inference. Frozen fixed-N cohorts, preserved seeds and failures, and an independent published implementation contract protect against selection. See METHODOLOGY.md and priors_by_family.json for equations and family-specific priors. M5 is not a correlated-noise likelihood.", "", "## Results, numerical evidence and discussion", ""]
    manuscript += report[report.index("## Campanhas e populações (não somar como replicações independentes)"):]
    manuscript += ["", "## Threats to validity and future work", "", "Fixed-truth coverage is conditional; successful sampler diagnostics are necessary but not sufficient. Prior-dominated geometry, multiple comparisons, small paired complement, repeated local MC streams on one input and dependent catalog information prevent universal or population-level conclusions. No favorable target/seed selection or rescue threshold change. Future prospective studies may address correlated noise and independent targets; they were not executed here."]
    (output / "MANUSCRIPT_DRAFT.md").write_text("\n".join(manuscript) + "\n", encoding="utf-8", newline="\n")
    (output / "LIMITATIONS.md").write_text("# Limitações atuais\n\n" + "\n".join(f"- {claim['claim_id']}: não sustenta {', '.join(claim['unsupported_claims'])}." for claim in claims) + "\n\nArquivamento público/DOI, revisão de direitos/privacidade e submissão editorial permanecem pendentes. A restauração local não é reprodução de inferência. M6 não executado. Resultados negativos preservados.\n", encoding="utf-8", newline="\n")
    gate_figure(output / "v4_component_gates.svg", summaries)
    captions = read(root / OLD / "captions.json")
    captions["v4_component_gates.svg"] = "All declared v4 fits, component-specific pass/evaluated denominators. P2 twelve fits on six paired datasets, P3 three local fits reusing one external posterior, P4 nine fits on three paired datasets. Components are not joint science approval."
    write(output / "captions.json", captions)
    relative = output.relative_to(root).as_posix()
    write(output / "SOURCE_INVENTORY.json", {"canonical_synthesis": relative, "tcc_sources": [relative + "/" + p.relative_to(output).as_posix() for p in sorted(output.rglob("*")) if p.is_file()] + [relative + "/SOURCE_INVENTORY.json", relative + "/artifact_manifest.json"],
        "supporting_evidence_roots": roots, "bibliography": "docs/publication/BIBLIOGRAPHY.md",
        "historical_sources_unchanged": [OLD, "reports/publication_synthesis/tcc_evidence_v1", "publication/baseline/manifest.json"],
        "transitive_verified_files_at_build": inventory["file_count"], "new_inference": False})
    generators = {name: digest_file(root / name) for name in ("src/publication/synthesis_v3.py", "src/publication/gate_accounting.py", "src/publication/claim_authorization.py", "src/publication/campaign_reporting.py", "src/publication/campaign_plan.py", "src/publication/evidence_archive.py", "src/publication/tcc_closure.py", "src/publication/complement_trace_review.py", "scripts/close_tcc_evidence.py")}
    write(output / "artifact_manifest.json", {"schema_version": "tcc-evidence-v3", "source_checksums": sources,
        "generator_source_checksums": generators, "artifacts": {p.relative_to(output).as_posix(): digest_file(p) for p in sorted(output.rglob("*")) if p.is_file()},
        "semantics_change": "v1 computational_gates_passed was joint approval; v2 accounting separates sampler, PPC, joint, unassessed and incident invalidation. Original sealed data unchanged."})
