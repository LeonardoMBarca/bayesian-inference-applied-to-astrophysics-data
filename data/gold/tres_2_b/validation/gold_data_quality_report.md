# Relatório de Qualidade da Gold Inicial

## 1. Planeta Escolhido

```text
TrES-2 b
```

## 2. Missão Escolhida

```text
Kepler
```

Kepler foi escolhido por estar disponível para o planeta selecionado e por ser a primeira missão na ordem de preferência configurada.

## 3. Fonte do Fluxo

Fluxo selecionado:

```text
pdcsap_flux
```

Erro de fluxo selecionado:

```text
pdcsap_flux_err
```

Política:

```text
No normalization is applied in this initial GOLD layer. Flux values are selected from PDCSAP_FLUX when available, with SAP_FLUX fallback only if the preferred column is not usable.
```

## 4. Quantidade de Linhas

| planet_name | mission | rows_primary | rows_quality_filtered | rows_phase_folded | rows_transit_window | time_min | time_max | flux_min | flux_max | flux_median | flux_std | flux_err_median | quality_zero_count | quality_nonzero_count | selected_flux_source | period_used | transit_midpoint_used | transit_duration_used | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TrES-2 b | Kepler | 6163 | 5358 | 5358 | 919 | 120.5391194434851 | 258.46708751810365 | 397874.8 | 406827.28 | 406528.72 | 1437.6822131221104 | 17.048489 | 5358 | 805 | pdcsap_flux | 2.47063 | 122.76336000021547 | 1.74259 | NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0. |

## 5. Filtros Aplicados

Foram aplicadas somente transformações mínimas:

- seleção de colunas relevantes;
- remoção de linhas sem `time`;
- remoção de linhas sem fluxo;
- filtro `quality == 0` na curva filtrada;
- criação de fase orbital quando a escala temporal foi reconciliada;
- seleção de janela em torno do trânsito.

Não houve normalização de fluxo.

## 6. Problemas de Tempo e Fase

Warnings registrados:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.
```

## 7. Limitações

- A Gold inicial ainda não executa modelagem física.
- A Gold inicial ainda não executa inferência bayesiana.
- A Gold inicial não escolhe modelo de ruído.
- A Gold inicial não compara resultados com literatura.
- A janela de trânsito é uma seleção operacional inicial, não um ajuste.

## 8. Recomendação Para Modelagem

Usar como entrada principal:

```text
data/gold/tres_2_b/modeling/transit_window_lightcurve.csv
```

Antes da modelagem bayesiana, revisar:

- normalização;
- tratamento de incertezas;
- escolha do modelo físico;
- priors;
- diagnóstico de qualidade da curva.
