"""Persist lightweight handoff checks without launching a final campaign."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

from publication.campaign_plan import DEFAULT_CONFIG, build_plan, source_identity
from publication.campaign_worker import write_json
from publication.contracts import sha256_file


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--validation-id", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.validation_id):
        raise ValueError("Unsafe validation ID")
    root = Path(__file__).resolve().parents[2]
    output = root / "publication/validation/handoff" / args.validation_id
    output.mkdir(parents=True, exist_ok=False)
    commands = {
        "lint": [sys.executable, "-m", "ruff", "check", "."],
        "static_contracts": [sys.executable, "scripts/static_validate.py"],
        "practical_suite": [sys.executable, "scripts/run_ci_tests.py"],
        "historical_artifacts": [sys.executable, "scripts/validate_hardened_artifacts.py"],
        "final_dry_run": [sys.executable, "scripts/run_publication_campaign.py", "--dry-run"],
        "not_started_status": [sys.executable, "scripts/run_publication_campaign.py", "--status"],
        "smoke_reports_regenerated": [sys.executable, "scripts/aggregate_publication_campaign.py", "--config", "configs/publication/runner_smoke_v2.json"],
        "smoke_report_freshness": [sys.executable, "scripts/verify_publication_campaign.py", "--config", "configs/publication/runner_smoke_v2.json"],
    }
    checks = []
    for name, command in commands.items():
        print(f"Handoff check: {name}", flush=True)
        started = time.monotonic()
        stdout_path, stderr_path = output / f"{name}.stdout.txt", output / f"{name}.stderr.txt"
        with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open("x", encoding="utf-8") as stderr:
            completed = subprocess.run(command, cwd=root, stdout=stdout, stderr=stderr, check=False)
        checks.append({"name": name, "command": command, "return_code": completed.returncode,
                       "passed": completed.returncode == 0, "wall_seconds": time.monotonic()-started,
                       "stdout": stdout_path.relative_to(root).as_posix(), "stdout_sha256": sha256_file(stdout_path),
                       "stderr": stderr_path.relative_to(root).as_posix(), "stderr_sha256": sha256_file(stderr_path)})
    plan = build_plan(root, Path(DEFAULT_CONFIG))
    tests_output = (output / "practical_suite.stdout.txt").read_text()
    count = re.findall(r'"tests_run":\s*(\d+)', tests_output)
    payload = {"schema_version": "publication-handoff-validation-v1", "validation_id": args.validation_id,
               "passed": all(item["passed"] for item in checks) and not plan["preflight_errors"],
               "checks": checks, "plan_preflight_errors": plan["preflight_errors"],
               "practical_tests_passed": int(count[-1]) if count else None,
               "source_checksums": source_identity(root),
               "code_commit": subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"]).decode().strip(),
               "final_scientific_campaign_executed": False,
               "final_state_exists": (root / "artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json").exists(),
               "limits": "Unit/integration/physical-smoke engineering validation only; not completion of publication science or a full archived clean-room paper reproduction."}
    if payload["final_state_exists"]:
        payload["passed"] = False
    write_json(output / "validation.json", payload)
    report = root / "reports/PUBLICATION_CAMPAIGN_HANDOFF.md"
    counts = {phase: sum(job["experiment_id"] == phase for job in plan["jobs"]) for phase in plan["phase_order"]}
    source_inventory = [
        "publication/baseline/manifest.json", "docs/publication/BIBLIOGRAPHY.md",
        "docs/publication/NOVELTY_MATRIX.json", "docs/publication/NOVELTY_MATRIX.md",
        "docs/publication/BENCHMARK_SELECTION.md", "docs/publication/BENCHMARK_ENGINEERING_REPORT.md",
        "docs/publication/COMPUTE_BUDGET_AMENDMENT.md", "docs/publication/TARGET_SELECTION_PROTOCOL.md",
        "docs/publication/CAMPAIGN_RUNBOOK.md", "configs/publication/tcc_final_campaign.json",
        "configs/publication/tcc_campaign_v1_plan.json", "publication/registry.json",
        "publication/validation/runner_smoke_v2_validation.json",
        "publication/validation/kepler_4_engineering_preparation.json",
        str((output / "validation.json").relative_to(root).as_posix()),
        *[item["path"] for item in plan["protocols"].values()],
    ]
    inventory = {"schema_version": "tcc-paper-source-inventory-v1", "existing_sources": source_inventory,
                 "future_user_campaign_outputs": ["reports/publication_campaign/tcc_campaign_v1/campaign_summary.json",
                     "reports/publication_campaign/tcc_campaign_v1/campaign_summary.md",
                     "reports/publication_campaign/tcc_campaign_v1/artifact_manifest.json",
                     "reports/publication_campaign/tcc_campaign_v1/jobs.csv", "reports/publication_campaign/tcc_campaign_v1/attempts.csv",
                     "reports/publication_campaign/tcc_campaign_v1/failures.csv", "reports/publication_campaign/tcc_campaign_v1/rejections.csv",
                     "reports/publication_campaign/tcc_campaign_v1/PUB-02/calibration.json",
                     "reports/publication_campaign/tcc_campaign_v1/PUB-03/benchmark.json",
                     "reports/publication_campaign/tcc_campaign_v1/PUB-04/ablation.json",
                     "reports/publication_campaign/tcc_campaign_v1/PUB-05/aggregate.json"],
                 "claim_rule": "Current engineering/pilots do not establish final coverage, recovery, external agreement or generalization. Future files are required outputs, not existing evidence."}
    inventory_path = root / "docs/publication/TCC_PAPER_SOURCE_INVENTORY.json"
    inventory_path.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8", newline="\n")
    lines = ["# Entrega do runner e estado científico", "",
             f"Validação de infraestrutura: **{'PASS' if payload['passed'] else 'FAIL'}**. Commit testado: `{payload['code_commit']}`.",
             f"Suíte prática: {payload['practical_tests_passed']} testes aprovados quando disponível; detalhes e stderr preservados em `{(output/'validation.json').relative_to(root).as_posix()}`.",
             "", "## Escopo entregue", "",
             "Runner autônomo, protocolos pré-batch, ledger de seeds/IDs, isolamento de tentativas, checkpoint/retomada, limite de CPU/tempo, logs separados, estados e gates distintos, agregação por família, freshness e hashes, tarefas VSCode e operação tmux. Não depende de Codex.",
             f"Campanha final declarada: {len(plan['jobs'])} trabalhos. Estimativa de planejamento: {plan['estimated_total_hours']:.2f} h; teto suave configurado: {plan['resources']['max_campaign_hours']} h. Não é garantia de conclusão.",
             "", "| Família | Trabalhos finais declarados | Estado da evidência |", "|---|---:|---|"]
    for phase, count in counts.items():
        lines.append(f"| {phase} | {count} | {'Não executados pelo agente' if count else 'Adiado; não há implementação/validação M6'} |")
    lines += ["", "Runs científicos finais realizados nesta entrega: **0**; aprovados/reprovados/falhos finais: **0/0/0**. A campanha não foi inicializada. Os arquivos futuros não são evidência já obtida.",
              "", "## Evidência já disponível e resultados negativos", "",
              "Baseline científico histórico e 26 artefatos protegidos verificados; 15 entradas FITS disponíveis. Matriz de 24 fontes primárias delimita contribuição como integração e avaliação, sem alegação de prioridade. Benchmark escolhido antes das comparações.",
              "Dois pilotos P2 de sizing fizeram sampling e falharam na etapa ArviZ; traces/falhas preservados. O primeiro smoke externo revelou seed ignorada pela ponte juliet/dynesty: corrigido sem alterar priors/likelihood. Dois pilotos corrigidos repetiram o hash canônico, mas foram rejeitados pelo orçamento intencionalmente insuficiente. Isso não prova concordância posterior final.",
              "Smoke runner v2: cinco trabalhos, seis tentativas; três fixtures concluídas e duas rejeições (uma física com20draws). Uma falha técnica anterior ao retry permanece. Stop/resume e nova chamada não duplicaram concluídos. Nenhum fixture/piloto é promovido a conclusão científica. Smoke v1 interrompido permanece auditável.",
              "", "## Perguntas ainda abertas", "",
              "Coverage/bias finais, compatibilidade independente, efeitos de ablations e generalização multi-alvo aguardam a execução do usuário. Intervalos de coverage terão precisão limitada com20replicações. P4 tem3pares: efeitos descritivos, não taxas de erro precisas. Não foi demonstrado ainda um caso final sampler-converged/scientifically-invalid.",
              "M5 usa jitter branco independente. OU exploratório e M6/GP foram adiados por prazo; não há alegação de tratamento de ruído correlacionado. Normalização P2 é exata e conhecida; P4/P5 estimam medianas e não propagam toda essa incerteza. Período/catálogos condicionam análise observacional, portanto comparação de catálogo não é validação independente. Diagnósticos temporais após thinning não excluem correlação na cadência nativa.",
              "", "## Auditoria e reprodutibilidade", "",
              "Testes incluem truth leakage, determinismo, identidade de dataset, falhas preservadas, denominadores, mapping externo, gates, corrupção, processo órfão, budget, isolamento e freshness. Preflight verifica ambientes e fontes antes do P2. A revisão hostil corrigiu inconsistência de dataset embutido, RNG externo, códigos exatos de controle e subprocesso não-zero, entre outros. Nenhum threshold foi afrouxado para salvar observações.",
              "A release científica completa permanece INCOMPLETA. Ainda não houve clean-room de todos os117resultados, arquivamento público integral de traces nem DOI. As fixtures clean-room/testes de infraestrutura não substituem isso. `publication/release_audit.json` não é autorização para publicação.",
              "", "## Operação e fontes para TCC/paper", "", "```sh",
              "python scripts/run_publication_campaign.py --dry-run", "python scripts/run_publication_campaign.py --resume",
              "python scripts/run_publication_campaign.py --status", "python scripts/run_publication_campaign.py --stop",
              "python scripts/run_publication_campaign.py --aggregate", "python scripts/verify_publication_campaign.py", "```", "",
              "Instruções completas: `docs/publication/CAMPAIGN_RUNBOOK.md`. Lista exata de fontes atuais e outputs futuros: `docs/publication/TCC_PAPER_SOURCE_INVENTORY.json`. Relatórios científicos derivados serão gerados sob `reports/publication_campaign/tcc_campaign_v1/`; não copiar números de pilotos para a versão final do TCC."]
    report.write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({key: payload[key] for key in ("passed", "practical_tests_passed", "code_commit", "plan_preflight_errors")}, indent=2))
    raise SystemExit(0 if payload["passed"] else 1)


if __name__ == "__main__":
    main()
