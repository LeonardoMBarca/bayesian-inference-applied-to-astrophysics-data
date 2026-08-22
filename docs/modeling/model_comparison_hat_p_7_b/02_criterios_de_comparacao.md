# 02 - Critérios de Comparação do M4

## 1. Comparação de Parâmetros

Arquivo:

```text
tables/model_comparison/hat_p_7_b/parameter_comparison.csv
```

Campos principais:

- `model_id`;
- `model_name`;
- `model_family`;
- `depth_type`;
- `depth_mean`;
- `depth_hdi_3`;
- `depth_hdi_97`;
- `rp_rs_mean`;
- `rp_rs_hdi_3`;
- `rp_rs_hdi_97`;
- `duration_hours`;
- `ingress_hours`;
- `interpretation_note`.

Critério:

- M1 e M3 possuem profundidade direta de modelo.
- M2 possui `predicted_depth` exploratório derivado da curva preditiva.
- M2 não possui `Rp/Rs` físico direto.

## 2. Comparação de Diagnósticos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/diagnostic_comparison.csv
```

Campos:

- `sampler`;
- `draws`;
- `tune`;
- `chains`;
- `target_accept`;
- `r_hat_max`;
- `ess_min`;
- `divergences`;
- `bfmi_min`;
- `diagnostic_status`;
- `notes`.

Critério operacional:

```text
diagnostic_status = good
```

quando:

- `R-hat <= 1,01`;
- `ESS mínimo >= 1000`;
- `divergências = 0`.

## 3. Métricas Preditivas Simples

Arquivo:

```text
tables/model_comparison/hat_p_7_b/predictive_metric_comparison.csv
```

Métricas calculadas:

- RMSE;
- MAE;
- erro absoluto mediano;
- média dos resíduos;
- desvio padrão dos resíduos;
- desvio padrão dos resíduos padronizados;
- cobertura de intervalo preditivo 94%;
- número de pontos.

Essas métricas são simples e diagnósticas. Elas não substituem comparação
bayesiana formal por LOO/WAIC.

## 4. Comparação de Resíduos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/residual_comparison.csv
```

Formato longo:

- `model_id`;
- `phase`;
- `observed_flux`;
- `predicted_mean`;
- `residual`;
- `standardized_residual`;
- `normalized_flux_err`.

Para M1, a escala de resíduo padronizado foi reconstruída usando:

```text
sqrt(normalized_flux_err^2 + extra_sigma_mean^2)
```

Para M2 e M3, os resíduos padronizados foram lidos das tabelas já geradas.

## 5. LOO/WAIC Opcional

Arquivo:

```text
tables/model_comparison/hat_p_7_b/loo_waic_comparison.csv
```

O script tenta usar ArviZ para calcular LOO e WAIC, mas apenas se o arquivo
`trace.nc` contiver grupo `log_likelihood`.

Resultado atual:

```text
M1: unavailable
M2: unavailable
M3: unavailable
```

Motivo:

```text
trace.nc does not contain a log_likelihood group
```

O M4 registra essa limitação explicitamente e não inventa valores.

## 6. Recomendação de Modelo

Arquivo:

```text
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
```

Critérios:

- `interpretability_score`;
- `predictive_score`;
- `physical_structure_score`;
- `diagnostic_score`;
- `complexity_score`;
- `recommended_role`.

Papéis:

- `baseline_reference`;
- `predictive_description`;
- `primary_preliminary_result`;
- `future_extension_needed`, quando aplicável em etapas futuras.

Resultado:

- M1: `baseline_reference`;
- M2: `predictive_description`;
- M3: `primary_preliminary_result`.

## 7. Figuras

Diretório:

```text
figures/model_comparison/hat_p_7_b/
```

Figuras:

1. `01_depth_comparison.png`;
2. `02_rp_rs_comparison.png`;
3. `03_model_fit_comparison.png`;
4. `04_residual_comparison.png`;
5. `05_predictive_interval_comparison.png`;
6. `06_diagnostic_comparison.png`;
7. `07_model_complexity_interpretability_map.png`.
