# 31 - Diagnósticos Estatísticos e Tabelas da EDA

## 1. Objetivo

Este documento descreve as tabelas derivadas pela EDA e o significado das
métricas calculadas.

As tabelas são diagnósticas. Elas não representam resultado inferencial.

## 2. Tabela Resumo

Arquivo:

```text
tables/gold_eda/hat_p_7_b/gold_eda_summary.csv
```

Essa tabela possui uma linha e consolida os principais diagnósticos.

## 3. Principais Valores

| Métrica | Valor |
|---|---:|
| Planeta | `HAT-P-7 b` |
| Missão | `Kepler` |
| Linhas na curva primária | `6.163` |
| Linhas após filtro de qualidade | `3.909` |
| Linhas na curva faseada | `3.909` |
| Linhas na janela Gold atual | `1.664` |
| Tempo mínimo | `120,53881583872862` |
| Tempo máximo | `258,46743138637976` |
| Fase mínima na janela | `-0,4850831437298972` |
| Fase máxima na janela | `0,4849464913942332` |
| Valores ausentes em `flux` | `0` |
| Valores ausentes em `flux_err` | `0` |
| Pontos com `quality == 0` na curva primária | `3.909` |
| Pontos com `quality != 0` na curva primária | `2.254` |
| Duração de trânsito em dias | `0,16175666666666666` |
| Janela recomendada pela EDA | `0,15` dias |

## 4. Estatísticas de Fluxo

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| `flux_min` | `1027023,6` |
| `flux_max` | `1041236,94` |
| `flux_median` | `1034872,5` |
| `flux_mean` | `1036739,1433052885` |
| `flux_std` | `4012,547787789801` |

Interpretação:

- existe variação clara de fluxo dentro da janela;
- a queda de fluxo próxima da fase zero é visualmente identificável;
- a dispersão ainda inclui baseline e estrutura observacional, não apenas ruído branco.

## 5. Estatísticas de `flux_err`

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| `flux_err_median` | `25,8860865` |
| `flux_err_mean` | `26,102194072115385` |
| `flux_err_std` | `0,25819710596197804` |
| Ausências em `flux_err` | `0` |

Interpretação:

`flux_err` está disponível e numericamente consistente para uma likelihood
gaussiana preliminar. A modelagem futura ainda deve avaliar se essa incerteza
é suficiente para explicar os resíduos ou se será necessário incluir termo
extra de dispersão.

## 6. Profundidade Visual Aproximada

A profundidade visual aproximada da janela Gold atual foi:

```text
0,0065010087865026486
```

Em unidades de fluxo:

```text
6765,960000000079
```

Ela foi calculada como:

```text
(mediana fora do trânsito - mediana dentro do trânsito) / mediana fora do trânsito
```

com:

| Métrica | Valor |
|---|---:|
| Pontos dentro do núcleo do trânsito | `287` |
| Pontos fora do núcleo do trânsito | `1.377` |
| Mediana dentro do trânsito | `1033989,44` |
| Mediana fora do trânsito | `1040755,4` |
| Dispersão fora do trânsito | `3334,470461905991` |

Essa métrica é apenas exploratória.

## 7. Comparação de Janelas

Arquivo:

```text
tables/gold_eda/hat_p_7_b/window_comparison_summary.csv
```

Janelas avaliadas:

```text
±0,50 dias
±0,25 dias
±0,15 dias
±0,10 dias
±0,05 dias
```

Resumo:

| Janela | Pontos | Pontos fora do núcleo | Profundidade visual |
|---:|---:|---:|---:|
| `0,50` | `1.711` | `1.424` | `0,0064917` |
| `0,25` | `854` | `567` | `0,0065077` |
| `0,15` | `516` | `229` | `0,0065348` |
| `0,10` | `335` | `48` | `0,0061648` |
| `0,05` | `179` | `0` | indisponível |

## 8. Critério de Recomendação

O script recomenda a menor janela que satisfaça:

- meia largura pelo menos `1,5` vezes a meia duração do trânsito;
- pelo menos `200` pontos;
- pelo menos `50` pontos fora do núcleo do trânsito;
- profundidade visual calculável.

Com esse critério, a recomendação foi:

```text
±0,15 dias
```

## 9. Binning Visual

Arquivo:

```text
tables/gold_eda/hat_p_7_b/transit_window_binned_summary.csv
```

Essa tabela divide a janela de trânsito em bins de fase e calcula:

- mediana do fluxo;
- primeiro quartil;
- terceiro quartil;
- desvio padrão;
- quantidade de pontos;
- ponto médio do bin;
- erro padrão visual do bin.

Ela foi usada apenas para visualização.

## 10. Limitações

As tabelas não:

- normalizam fluxo;
- ajustam modelo;
- removem outliers;
- estimam posterior;
- comparam com literatura;
- validam resíduos.

Elas documentam a condição do dataset antes da modelagem.
