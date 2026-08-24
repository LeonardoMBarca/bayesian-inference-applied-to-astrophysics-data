# Relatório de Qualidade da Gold Inicial

## 1. Planeta Escolhido

```text
Kepler-10 b
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
| Kepler-10 b | Kepler | 124459 | 115363 | 115363 | 115363 | 40836 | kepler_10_b-06a6ce6b0b39f5b4 | 3 | short | 58.84876286472961 | 200.3240850096772 | 349.50591258537315 | 523908.56 | 564278.94 | 527040.25 | 14810.46252162781 | 112.135345 | 115363 | 9096 | pdcsap_flux | 0.8374907 | 201.086870000232 | 1.811 | NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0. |

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
data/gold/kepler_10_b/modeling/transit_window_lightcurve.csv
```

O M5 deve verificar `preprocessing_status=segment_normalized`, `dataset_id`,
identidade do alvo, exposição e checksums antes de inferir.
