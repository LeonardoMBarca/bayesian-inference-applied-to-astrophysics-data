# 27 - Dicionário de Arquivos e Campos Gold

## 1. Objetivo

Este documento responde a duas perguntas práticas:

1. Onde está cada informação da Gold?
2. Como cada informação está estruturada?

## 2. Seleção Gold

### 2.1 `gold_candidate_scorecard.csv`

Caminho:

```text
data/gold/selection/gold_candidate_scorecard.csv
```

Uma linha por planeta candidato.

Campos principais:

| Campo | Significado |
|---|---|
| `planet_name` | Nome do planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug usado em caminhos |
| `has_kepler` | Indica se há dados Kepler |
| `has_tess` | Indica se há dados TESS |
| `has_k2` | Indica se há dados K2 |
| `kepler_fits_count` | Quantidade de FITS Kepler |
| `tess_fits_count` | Quantidade de FITS TESS |
| `total_mast_rows` | Total de linhas MAST na Silver |
| `total_quality_zero_rows` | Linhas com `quality == 0` |
| `total_quality_nonzero_rows` | Linhas com `quality != 0` |
| `pdcsap_flux_available` | Disponibilidade de `PDCSAP_FLUX` |
| `sap_flux_available` | Disponibilidade de `SAP_FLUX` |
| `orbital_period_available` | Presença de período orbital |
| `transit_midpoint_available` | Presença de tempo central |
| `transit_duration_available` | Presença de duração |
| `transit_depth_available` | Presença de profundidade |
| `etd_observation_count` | Observações ETD consolidadas |
| `etd_curve_count` | Curvas ETD públicas baixadas |
| `etd_photometry_points` | Pontos fotométricos ETD |
| `score_availability` | Pontuação de disponibilidade |
| `score_quality` | Pontuação de qualidade |
| `score_catalog_completeness` | Pontuação catalográfica |
| `score_total` | Soma das pontuações |
| `recommended_role` | Papel recomendado |
| `notes` | Justificativas compactas |

### 2.2 `selected_gold_target.json`

Caminho:

```text
data/gold/selection/selected_gold_target.json
```

Campos:

| Campo | Valor da execução |
|---|---|
| `selected_planet_name` | `HAT-P-7 b` |
| `selected_host_star` | `HAT-P-7` |
| `selected_planet_slug` | `hat_p_7_b` |
| `selected_primary_mission` | `Kepler` |
| `selected_flux_column` | `pdcsap_flux` |
| `selected_flux_err_column` | `pdcsap_flux_err` |
| `selection_reason` | Justificativa textual |
| `created_at_utc` | Data/hora UTC |

## 3. Catálogo de Referência

Arquivo:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
```

Uma linha para HAT-P-7 b.

Campos:

```text
planet_name
host_star
planet_slug
orbital_period_days
transit_midpoint
transit_duration_hours
transit_depth
planet_radius_earth
planet_radius_jupiter
stellar_radius_solar
stellar_mass_solar
stellar_teff
system_distance_pc
source_raw_path
silver_source_path
gold_created_at_utc
```

## 4. Curva Primária

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
```

Linhas:

```text
6.163
```

Campos:

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `mission` | Missão usada |
| `time` | Tempo Kepler/BKJD |
| `flux` | Fluxo selecionado |
| `flux_err` | Erro do fluxo selecionado |
| `flux_source` | Coluna original usada |
| `quality` | Flag de qualidade |
| `quality_is_zero` | Indicador booleano |
| `cadence_number` | Número de cadência |
| `source_silver_path` | Arquivo Silver de origem |
| `source_raw_path` | FITS RAW de origem |
| `source_fits_file` | Nome do FITS |
| `gold_created_at_utc` | Data/hora UTC |

## 5. Curva Filtrada Por Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
```

Linhas:

```text
3.909
```

Possui as mesmas colunas da curva primária, mas mantém apenas:

```python
quality == 0
```

## 6. Curva Faseada

Arquivo:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
```

Linhas:

```text
3.909
```

Campos principais:

```text
planet_name
host_star
planet_slug
mission
time
phase
flux
flux_err
quality
flux_source
orbital_period_days
transit_midpoint_used
phase_formula
source_gold_lightcurve
gold_created_at_utc
```

## 7. Janela de Trânsito

Arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas:

```text
1.664
```

Campos adicionais em relação à curva faseada:

```text
in_transit_window
transit_window_half_width_days
transit_duration_hours_used
```

Esse é o arquivo Gold principal para a próxima etapa.

## 8. Validação

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

Uma linha com resumo técnico da Gold.

Campos:

```text
planet_name
mission
rows_primary
rows_quality_filtered
rows_phase_folded
rows_transit_window
time_min
time_max
flux_min
flux_max
flux_median
flux_std
flux_err_median
quality_zero_count
quality_nonzero_count
selected_flux_source
period_used
transit_midpoint_used
transit_duration_used
warnings
```

## 9. Manifesto

Arquivo:

```text
data/gold/manifests/gold_data_manifest.csv
```

Usado para auditoria dos arquivos criados.

Campos essenciais:

```text
gold_file_path
transformation_type
row_count
column_count
status
sha256
file_size_bytes
notes
```

## 10. Relatórios Markdown Dentro da Gold

Arquivos:

```text
data/gold/selection/gold_candidate_report.md
data/gold/hat_p_7_b/validation/gold_data_quality_report.md
data/gold/hat_p_7_b/docs/README_gold.md
```

Eles são artefatos da execução Gold.

A documentação completa, organizada por tópico, é esta pasta:

```text
docs/gold/
```
