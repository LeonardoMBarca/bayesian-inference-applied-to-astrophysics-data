# Modelagem Bayesiana

## Modelo atual

[M5 — trânsito físico parametrizado](bayesian_physical_transit/README.md) é o
workflow recomendado. Ele usa a Gold segmentada, configuração autoritativa de
alvo, integração de exposição, NUTS, log-likelihood pontual, prior/PPC e gates
explícitos.

Código e entradas:

- `src/bayesian_modeling/physical_transit.py` — implementação compartilhada;
- `src/bayesian_modeling/contracts.py` — paths, priors, gates e comparação;
- `scripts/run_bayesian_physical_transit.py` — CLI genérica;
- `scripts/run_kepler_10b.py` — CLI fina com alvo Kepler-10 b;
- `data/gold/<target>/modeling/transit_window_lightcurve.csv` — única entrada.

Os artefatos são isolados por família, alvo e `run_id` em `models/`, `tables/`
e `figures/`; o relatório contém alvo e run no nome.

## Modelos históricos

As pastas M1, M2, M3 e a comparação antiga de HAT-P-7 b são snapshots do
desenvolvimento incremental. Elas permanecem para rastreabilidade, mas não
descrevem o M5 atual e não são automaticamente comparáveis ao dataset
Kepler-10 b endurecido:

- [M1 box transit](bayesian_baseline_hat_p_7_b/README.md);
- [M2 regressão preditiva](bayesian_predictive_phase_regression_hat_p_7_b/README.md);
- [M3 trapézio](bayesian_trapezoid_transit_hat_p_7_b/README.md);
- [comparação histórica](model_comparison_hat_p_7_b/README.md).

As implementações preservadas de M1–M3 ficam agrupadas em
`src/bayesian_modeling/legacy/`. Os caminhos `scripts/run_bayesian_*.py`
continuam válidos como entry points de compatibilidade para notebooks e
reexecuções históricas.

Claims e números dessas pastas devem ser citados como históricos, com o modelo,
alvo e dataset correspondentes. A comparação formal atual obedece ao contrato
de `scripts/run_model_comparison.py`.
