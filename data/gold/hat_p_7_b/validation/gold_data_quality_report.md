# Relatório de Qualidade da Gold Inicial

## 1. Planeta Escolhido

```text
HAT-P-7 b
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
Quality-filtered flux is phase-folded with segment identity preserved, then divided by the out-of-transit median of each source FITS segment. No polynomial detrending is applied because PDCSAP_FLUX is already systematics-corrected; before/after segment diagnostics are persisted.
```

## 4. Quantidade de Linhas

| planet_name | mission | rows_primary | rows_quality_filtered | rows_phase_folded | rows_segment_normalized | rows_transit_window | dataset_id | segment_count | cadence_types | median_exposure_seconds | time_min | time_max | flux_min | flux_max | flux_median | flux_std | flux_err_median | quality_zero_count | quality_nonzero_count | selected_flux_source | period_used | transit_midpoint_used | transit_duration_used | warnings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HAT-P-7 b | Kepler | 6163 | 3909 | 3909 | 3909 | 1027 | hat_p_7_b-7ab50a2fe12341b7 | 3 | long | 1765.462885941888 | 120.53881583872862 | 258.46743138637976 | 1027023.6 | 1041324.94 | 1040914.9 | 3530.9448155449695 | 25.875484 | 3909 | 2254 | pdcsap_flux | 2.20474 | 121.35857200017199 | 3.88216 | NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0. |

## 5. Filtros Aplicados

Foram aplicadas transformações explícitas e rastreáveis:

- seleção de colunas relevantes;
- remoção de linhas sem `time`;
- remoção de linhas sem fluxo;
- filtro `quality == 0` na curva filtrada;
- seleção da cadência exigida pela configuração autoritativa do alvo;
- criação de fase orbital quando a escala temporal foi reconciliada;
- normalização separada de cada `segment_id` pela mediana fora do trânsito;
- preservação do FITS de origem e do tempo de exposição;
- seleção de janela em torno do trânsito.

Não houve concatenação seguida de normalização global. Não foi aplicado
detrending polinomial adicional: a hipótese registrada é usar `PDCSAP_FLUX` e
remover apenas offsets multiplicativos entre segmentos.

## 6. Problemas de Tempo e Fase

Warnings registrados:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.
```

## 7. Limitações

- A Gold não executa modelagem física nem inferência bayesiana; isso pertence ao M5.
- A normalização por mediana não modela tendências temporais residuais.
- O dataset registra jitter instrumental/estelar somente como limitação; não o remove.
- A janela de trânsito é uma seleção configurada, não um ajuste.

## 8. Recomendação Para Modelagem

Usar como entrada principal:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

O M5 deve verificar `preprocessing_status=segment_normalized`, `dataset_id`,
identidade do alvo, exposição e checksums antes de inferir.
