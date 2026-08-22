# 41 - Figuras, Tabelas e Artefatos do M1

## 1. Figuras

Diretório:

```text
figures/bayesian_baseline/hat_p_7_b/
```

Diretórios versionados:

```text
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

A execução recomendada para leitura visual e interpretação preliminar é
`002_nuts_robust`.

## 2. Input de Modelagem

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/01_modeling_input.png
```

Mostra `normalized_flux` contra `phase` e destaca a região central usada pelo
box transit.

![Input de modelagem](../../../figures/bayesian_baseline/hat_p_7_b/01_modeling_input.png)

## 3. Trace Plot

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/02_trace_plot.png
```

Mostra cadeias de:

- `baseline`;
- `depth`;
- `extra_sigma`;
- `rp_rs`.

Os traços confirmam visualmente o problema já apontado por R-hat/ESS: a
execução curta não convergiu adequadamente.

![Trace plot](../../../figures/bayesian_baseline/hat_p_7_b/02_trace_plot.png)

## 4. Posterior de `depth`

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/03_posterior_depth.png
```

Mostra a distribuição posterior da profundidade média do box.

![Posterior de depth](../../../figures/bayesian_baseline/hat_p_7_b/03_posterior_depth.png)

## 5. Posterior de `Rp/Rs`

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/04_posterior_rp_rs.png
```

Mostra a distribuição posterior do parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

![Posterior de Rp/Rs](../../../figures/bayesian_baseline/hat_p_7_b/04_posterior_rp_rs.png)

## 6. Ajuste Box Por Fase

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/05_model_fit_phase.png
```

Mostra os pontos normalizados e a média posterior do modelo box.

![Ajuste box por fase](../../../figures/bayesian_baseline/hat_p_7_b/05_model_fit_phase.png)

## 7. Posterior Predictive Check

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/06_posterior_predictive_check.png
```

Mostra observações, média preditiva e intervalo preditivo.

![Posterior predictive](../../../figures/bayesian_baseline/hat_p_7_b/06_posterior_predictive_check.png)

## 8. Tabelas

Diretório:

```text
tables/bayesian_baseline/hat_p_7_b/
```

Arquivos:

```text
modeling_input_baseline.csv
posterior_summary.csv
derived_parameters_summary.csv
posterior_predictive_summary.csv
model_run_comparison.csv
```

Diretórios versionados:

```text
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

## 9. Artefatos do Modelo

Diretório:

```text
models/bayesian_baseline/hat_p_7_b/
```

Arquivos:

```text
trace.nc
model_config.json
inference_data_summary.json
```

Diretórios versionados:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Artefatos principais da execução robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/model_config.json
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/inference_data_summary.json
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_predictive_summary.csv
```

Relatório robusto:

```text
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 10. Roadmap

Arquivo:

```text
models/modeling_roadmap.md
```

Documenta M1, M2, M3 e M4 como sequência planejada.
