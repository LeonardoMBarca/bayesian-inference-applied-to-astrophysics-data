# M2 - Bayesian Predictive Phase Regression - HAT-P-7 b

## 1. Objetivo do M2

O M2 modela o fluxo normalizado de HAT-P-7 b como uma função suave da fase
orbital. Diferente do M1, ele não assume forma box-shaped e não estima
diretamente uma profundidade física como parâmetro primário.

O objetivo é obter:

- curva preditiva média;
- intervalo de credibilidade da função latente;
- intervalo preditivo para observações futuras;
- diagnóstico de resíduos;
- comparação qualitativa com o M1 robusto.

## 2. Diferença Entre M1 e M2

M1 pergunta:

```text
Qual a profundidade média do trânsito assumindo uma forma box?
```

M2 pergunta:

```text
Qual função suave de fluxo em função da fase é suportada pelos dados?
```

Assim, M2 é preditivo e flexível. Ele ajuda a descrever a forma observada da
curva, mas não substitui um modelo físico de trânsito.

## 3. Dataset Usado

Entrada:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Dataset efetivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/modeling_input_predictive.csv
```

Resumo:

- linhas na janela Gold original: `1664`
- linhas após `abs(phase) <= 0.15`: `516`
- linhas após filtro de qualidade: `516`
- pontos usados no M2: `516`
- baseline mediano: `1040715.45`

## 4. Pré-processamento

Foram mantidas as mesmas regras base do M1:

- `abs(phase) <= 0.15`;
- `quality == 0`, quando a coluna existe;
- remoção de linhas sem `phase`, `flux` ou `flux_err`;
- remoção de `flux_err <= 0`;
- normalização local por mediana da região `0,08 <= abs(phase) <= 0,15`.

## 5. Especificação do Modelo

A função latente é:

```text
f(x) = intercept + soma_k w_k * phi_k(x)
```

com bases radiais gaussianas fixas:

```text
phi_k(x) = exp(-0.5 * ((x - c_k) / width)^2)
```

Configuração:

- `n_basis = 12`
- `basis_width = 0.035`
- centros distribuídos uniformemente em `[-0,15, 0,15]`
- grid preditivo com `300` pontos

## 6. Priors

```text
intercept ~ Normal(1.0, 0.01)
weight_sigma ~ HalfNormal(0.01)
weights_raw_k ~ Normal(0, 1)
weights_k = weights_raw_k * weight_sigma
extra_sigma ~ HalfNormal(0.005)
```

Likelihood:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(f(phase_i), sigma_eff_i)
```

## 7. Funções de Base Radial

As funções de base foram salvas em:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/prediction_grid.csv
```

Figura:

![Funções de base](../figures/bayesian_predictive_phase_regression/hat_p_7_b/02_basis_functions.png)

## 8. Resultados Posteriores

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/posterior_summary.csv
```

Resumo dos pesos:

| parameter | basis_center | mean | hdi_3% | hdi_97% | r_hat |
| --- | --- | --- | --- | --- | --- |
| weights[0] | -0.15 | -0.00023548 | -0.00503759 | 0.00419446 | 1.00106771 |
| weights[1] | -0.12272727272727273 | 0.00070797 | -0.00512211 | 0.00520105 | 1.00036132 |
| weights[2] | -0.09545454545454546 | 0.00269688 | -0.00189511 | 0.00804785 | 1.00130276 |
| weights[3] | -0.06818181818181818 | -0.0017106 | -0.00681499 | 0.00286592 | 1.00101653 |
| weights[4] | -0.04090909090909091 | -0.0039854 | -0.01002415 | 0.00043752 | 1.00026292 |
| weights[5] | -0.013636363636363641 | 0.00077474 | -0.00368736 | 0.0059127 | 1.00100914 |
| weights[6] | 0.013636363636363641 | -0.00136367 | -0.00607743 | 0.00330665 | 1.00064338 |
| weights[7] | 0.040909090909090895 | -0.00536806 | -0.0115054 | -0.00095096 | 1.0011918 |
| weights[8] | 0.06818181818181818 | 2.499e-05 | -0.0047351 | 0.00512591 | 1.00060507 |
| weights[9] | 0.09545454545454546 | 0.00295928 | -0.00169383 | 0.00775116 | 1.00083856 |
| weights[10] | 0.12272727272727271 | -0.00011922 | -0.00596432 | 0.00427884 | 1.00064368 |
| weights[11] | 0.15 | -0.00019405 | -0.00480781 | 0.00426936 | 1.00042086 |

## 9. Curva Preditiva

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
```

Profundidade exploratória derivada da curva:

```text
predicted_depth_mean = 0.00721029
predicted_depth_hdi_3 = 0.00637213
predicted_depth_hdi_97 = 0.00809741
```

Essa profundidade é exploratória e não equivale a um parâmetro físico direto.

Figura:

![Curva latente M2](../figures/bayesian_predictive_phase_regression/hat_p_7_b/05_predictive_curve_latent.png)

## 10. Posterior Predictive Check

Status:

```text
created
```

Cobertura aproximada do intervalo preditivo de 94% nos pontos observados:

```text
1.000000
```

Figura:

![Posterior predictive M2](../figures/bayesian_predictive_phase_regression/hat_p_7_b/06_posterior_predictive_observations.png)

## 11. Resíduos

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/residual_summary.csv
```

Métricas:

- média dos resíduos: `-0.00000214`
- mediana dos resíduos: `0.00234046`
- desvio padrão dos resíduos: `0.00318197`
- desvio padrão dos resíduos padronizados: `0.99112818`

Figura:

![Resíduos por fase](../figures/bayesian_predictive_phase_regression/hat_p_7_b/07_residuals_by_phase.png)

## 12. Comparação Qualitativa com M1

M2 predicted_depth exploratório = 0.00721029; M1 depth paramétrico = 0.00525258; diferença M2 - M1 = 0.00195771.

Figura:

![Comparação M2 com M1](../figures/bayesian_predictive_phase_regression/hat_p_7_b/08_comparison_with_m1.png)

Interpretação:

- M1 resume o trânsito por uma profundidade box-shaped;
- M2 descreve uma curva suave de fluxo por fase;
- M2 melhora a descrição visual do formato por permitir transição suave;
- a profundidade exploratória do M2 deve ser comparada com cautela à depth do M1.

## 13. Diagnósticos MCMC

- NUTS rodou corretamente: `True`
- sampler: `NUTS`
- draws: `2000`
- tune: `2000`
- chains: `4`
- target_accept: `0.99`
- divergências: `0`
- R-hat máximo: `1.00292448`
- ESS mínimo: `2269.80467052`
- aceitação média: `0.98810751`
- BFMI mínimo: `0.71467278`
- recomendado para interpretação preditiva M2: `True`

Nota:

```text
NUTS diagnostics satisfy the project criteria for M2 predictive interpretation.
```

## 14. Interpretação Científica

O M2 recupera visualmente o trânsito como depressão suave na região de fase
zero e fornece incerteza sobre a função latente e sobre futuras observações.

Ele é adequado como modelo preditivo intermediário para comparar com M1 e
preparar a transição para modelos mais estruturados.

## 15. Limitações

M2:

- não é modelo físico final;
- não estima diretamente `Rp/Rs`;
- não usa limb darkening;
- não modela geometria orbital;
- não estima ingresso, egresso ou duração como parâmetros físicos;
- não usa Gaussian Process;
- não incorpora TESS, ETD ou múltiplas missões;
- não substitui M3.

## 16. Próximos Passos

O próximo modelo recomendado é M3: um modelo trapezoidal ou físico aproximado
que estime explicitamente profundidade, duração e formato de ingresso/egresso.

M4 deve ficar para a comparação formal entre M1, M2 e M3.
