# M4 - Comparação de Modelos - HAT-P-7 b

> Snapshot histórico; o ranking não satisfaz automaticamente o contrato formal atual.

## 1. Objetivo do M4

O M4 compara os modelos M1, M2 e M3 já ajustados para HAT-P-7 b. Ele não cria
um novo modelo bayesiano e não altera RAW, Silver, Gold ou os artefatos dos
modelos anteriores.

Perguntas centrais:

- como os pressupostos de cada modelo afetam a profundidade inferida;
- qual modelo descreve melhor o formato observado do trânsito;
- qual modelo apresenta melhor comportamento preditivo;
- qual modelo oferece melhor equilíbrio entre interpretabilidade e
  flexibilidade;
- qual modelo deve ser usado como resultado principal preliminar.

## 2. Modelos Comparados

| Modelo | Papel | Hipótese principal |
|---|---|---|
| M1 | Baseline | Trânsito box-shaped com meia largura fixa |
| M2 | Descrição preditiva | Fluxo suave em função da fase por bases radiais |
| M3 | Resultado preliminar | Trânsito trapezoidal aproximado |

## 3. Critérios de Comparação

Foram comparados:

- profundidade e `Rp/Rs`, quando definidos;
- diagnósticos MCMC;
- resíduos;
- métricas preditivas simples;
- cobertura de intervalos preditivos de 94%;
- equilíbrio entre interpretabilidade física e flexibilidade.

## 4. Comparação de Parâmetros

Arquivo:

```text
tables/model_comparison/hat_p_7_b/parameter_comparison.csv
```

| Modelo | Tipo de profundidade | Profundidade média | HDI 3% | HDI 97% | Rp/Rs médio |
|---|---|---:|---:|---:|---:|
| M1 | direta | 0.00525258 | 0.00464576 | 0.00587726 | 0.07243869 |
| M2 | exploratória | 0.00721029 | 0.00637213 | 0.00809741 | não estimado diretamente |
| M3 | direta aproximada | 0.00656620 | 0.00594692 | 0.00716767 | 0.08100761 |

Figura:

![Comparação de profundidade](../figures/model_comparison/hat_p_7_b/01_depth_comparison.png)

![Comparação de Rp/Rs](../figures/model_comparison/hat_p_7_b/02_rp_rs_comparison.png)

## 5. Comparação de Diagnósticos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/diagnostic_comparison.csv
```

| Modelo | R-hat máximo | ESS mínimo | Divergências | Status |
|---|---:|---:|---:|---|
| M1 | 1.00088086 | 4553.60 | 0 | good |
| M2 | 1.00292448 | 2269.80 | 0 | good |
| M3 | 1.00107423 | 4212.34 | 0 | good |

Figura:

![Comparação de diagnósticos](../figures/model_comparison/hat_p_7_b/06_diagnostic_comparison.png)

## 6. Comparação Preditiva

Arquivo:

```text
tables/model_comparison/hat_p_7_b/predictive_metric_comparison.csv
```

| Modelo | RMSE | MAE | Desvio padrão dos resíduos | Cobertura 94% |
|---|---:|---:|---:|---:|
| M1 | 0.00358754 | 0.00327957 | 0.00359102 | 0.961240 |
| M2 | 0.00317888 | 0.00312563 | 0.00318197 | 1.000000 |
| M3 | 0.00317499 | 0.00315311 | 0.00317806 | 1.000000 |

Figura:

![Intervalos preditivos](../figures/model_comparison/hat_p_7_b/05_predictive_interval_comparison.png)

## 7. Comparação Visual dos Ajustes

Figura:

![Comparação dos ajustes](../figures/model_comparison/hat_p_7_b/03_model_fit_comparison.png)

Leitura:

- M1 é transparente, mas rígido;
- M2 acompanha uma forma suave, mas sua profundidade é derivada de modo
  exploratório;
- M3 captura uma forma intermediária, com ingresso e egresso explícitos.

## 8. Resíduos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/residual_comparison.csv
```

Figura:

![Comparação de resíduos](../figures/model_comparison/hat_p_7_b/04_residual_comparison.png)

## 9. LOO/WAIC

Arquivo:

```text
tables/model_comparison/hat_p_7_b/loo_waic_comparison.csv
```

Status:

```text
M1: unavailable, M2: unavailable, M3: unavailable
```

Os arquivos `trace.nc` atuais não contêm grupo `log_likelihood`, portanto
LOO/WAIC não foram forçados nesta etapa. O M4 registra essa limitação em vez
de inventar valores.

## 10. Discussão dos Pressupostos

A profundidade muda porque cada modelo define a forma do trânsito de maneira
diferente:

- M1 usa uma caixa fixa e estima uma profundidade média;
- M2 usa uma curva suave e deriva uma profundidade exploratória pela diferença
  entre baseline de borda e mínimo da curva;
- M3 estima profundidade dentro de uma forma trapezoidal com centro, duração e
  ingresso/egresso.

O `predicted_depth` do M2 não deve ser comparado diretamente como parâmetro
físico equivalente ao `depth` de M1/M3. Ele é útil como diagnóstico de forma,
não como estimativa final de `Rp/Rs`.

## 11. Recomendação de Modelo Principal Preliminar

Arquivo:

```text
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
```

Modelo recomendado:

```text
M3
```

Justificativa:

M3 é recomendado como resultado principal preliminar porque combina bons
diagnósticos, profundidade direta, `Rp/Rs` derivado, duração total aproximada
e ingresso/egresso. M1 deve permanecer como baseline de referência e M2 como
descrição preditiva da curva suave.

Figura conceitual:

![Mapa flexibilidade interpretabilidade](../figures/model_comparison/hat_p_7_b/07_model_complexity_interpretability_map.png)

## 12. Limitações

Mesmo com a recomendação de M3, ainda não há caracterização física final.

Limitações principais:

- nenhum modelo usa limb darkening;
- nenhum modelo usa Mandel & Agol;
- nenhum modelo usa geometria orbital completa;
- LOO/WAIC não foram calculados porque os traces não têm log likelihood;
- todos os modelos usam apenas Kepler para HAT-P-7 b;
- M2 não estima `Rp/Rs` diretamente;
- M3 ainda é uma aproximação trapezoidal.

## 13. Próximos Passos

O próximo passo natural é um modelo físico completo ou semi-físico:

- gerar log likelihood nos próximos modelos para comparação formal;
- considerar `batman` ou formulação Mandel & Agol;
- incluir limb darkening com priors informativos;
- avaliar integração por tempo de exposição;
- comparar modelos com posterior predictive checks e, se possível, LOO/WAIC.
