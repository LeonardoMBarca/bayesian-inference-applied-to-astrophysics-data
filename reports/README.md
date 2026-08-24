# Relatórios

O fechamento auditável do programa está em
`REPOSITORY_HARDENING_FINAL.md`.

O relatório científico atual é
`bayesian_physical_transit_kepler_10_b_scientific_003_report.md`, gerado do mesmo
objeto estruturado que produz `model_config.json`.

Relatórios sem target e `run_id` no nome, ou relativos a M1–M3/HAT-P-7 b, são
snapshots históricos. Eles permanecem por rastreabilidade, mas não devem ser
usados como descrição do M5 atual nem combinados em comparação formal sem o
contrato de `scripts/run_model_comparison.py`.

Os resultados atuais de sensibilidade estão em
`sensitivity/kepler_10_b/sensitivity_002/`. A comparação formal correspondente
está em `model_comparison/prior_sensitivity_002/`; ela preserva os valores de
LOO/WAIC, mas não fornece ranking porque os diagnósticos Pareto-k de LOO
emitiram alerta. A tentativa `sensitivity_001_weak_interrupted` é evidência de
execução incompleta e permanece explicitamente inválida para interpretação.
