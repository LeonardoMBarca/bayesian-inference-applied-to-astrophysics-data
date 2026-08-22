# 40 - Resultados e Diagnósticos do M1

## 1. Resultado Atual Recomendado

A execução recomendada para interpretação preliminar do M1 é:

```text
002_nuts_robust
```

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
```

Resumo robusto:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat |
|---|---:|---:|---:|---:|
| `baseline` | `0,99597938` | `0,99561513` | `0,99636166` | `1,00044605` |
| `depth` | `0,00525258` | `0,00464576` | `0,00587726` | `1,00034161` |
| `extra_sigma` | `0,00360075` | `0,00339170` | `0,00382274` | `1,00088086` |
| `rp_rs` | `0,07243869` | `0,06815983` | `0,07666328` | `1,00033967` |

Diagnóstico robusto:

```text
max R-hat = 1,00088086
min ESS = 4553,60020940
divergences = 0
BFMI mínimo = 1,10526248
```

Conclusão:

```text
A execução NUTS robusta satisfaz os critérios definidos para uso do M1 como baseline comparativo.
```

Detalhes completos:

```text
docs/modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 2. Resultado Posterior da Execução Operacional Original

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/posterior_summary.csv
```

Resumo:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat |
|---|---:|---:|---:|---:|
| `baseline` | `0,99582952` | `0,99513262` | `0,99617200` | `2,33522345` |
| `depth` | `0,00507495` | `0,00439089` | `0,00577990` | `1,27595378` |
| `extra_sigma` | `0,00360586` | `0,00338010` | `0,00384425` | `1,15526789` |
| `rp_rs` | `0,07118168` | `0,06626377` | `0,07602563` | `1,27595378` |

## 3. Parâmetros Derivados

Arquivo robusto:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
```

Resultado principal robusto:

```text
depth_mean = 0,00525258
rp_rs_mean = 0,07243869
```

Arquivo operacional original:

```text
tables/bayesian_baseline/hat_p_7_b/derived_parameters_summary.csv
```

Resultado principal:

```text
depth_mean = 0,00507495
rp_rs_mean = 0,07118168
```

## 4. Comparação Com a EDA

Profundidade visual aproximada da EDA:

```text
0,0065010087865026
```

Profundidade posterior M1 robusta:

```text
0,00525258
```

Profundidade posterior M1 operacional original:

```text
0,00507495
```

Interpretação:

Os valores têm a mesma ordem de grandeza, mas não são idênticos. Isso é
esperado porque:

- a EDA usa contraste de medianas;
- M1 usa uma região central fixa;
- M1 estima baseline, profundidade e dispersão extra;
- o modelo box é simplificado.

## 5. Diagnósticos MCMC da Execução Operacional Original

Maior R-hat:

```text
2,33522345
```

Menor ESS:

```text
4,25512801
```

Conclusão:

```text
Os diagnósticos não indicam convergência adequada.
```

## 6. Por Que os Diagnósticos Originais Ficaram Fracos

O ambiente operacional original não possuía `Python.h`, impedindo o uso normal
do backend C do PyTensor. Isso tornou NUTS 2000/2000 impraticável naquela
primeira execução.

Para validar o pipeline completo, foi usada uma execução curta com:

```text
sampler = Metropolis
draws = 300
tune = 300
chains = 4
```

Essa execução gera artefatos e demonstra o fluxo M1, mas não deve ser usada
como resultado científico final.

## 7. Posterior Predictive

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/posterior_predictive_summary.csv
```

Status:

```text
created
```

Campos:

```text
phase
observed_flux
predicted_mean
predicted_hdi_3
predicted_hdi_97
residual
```

## 8. Interpretação Cautelosa

M1 cumpriu o objetivo de pipeline:

- preparou os dados;
- especificou o modelo;
- gerou posterior;
- gerou posterior predictive;
- salvou trace e tabelas.

Na execução operacional original, pelos diagnósticos, ele ainda não deve ser
interpretado como inferência final.

Na execução robusta `002_nuts_robust`, os diagnósticos ficaram adequados para o
uso do M1 como baseline comparativo.

## 9. Recomendação Atual

Usar a execução robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Não usar a execução curta Metropolis para conclusões científicas.
