# 19. Dicionário de Arquivos e Campos da Camada Silver

## Objetivo deste documento

Este documento funciona como mapa de localização da camada Silver.

Ele responde:

- onde cada arquivo Silver está;
- que informação cada arquivo contém;
- quais campos principais existem;
- quais campos preservam proveniência;
- como cada tabela deve ser interpretada.

## Manifesto Silver

### Caminho

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

### Conteúdo

Registra todos os artefatos Silver criados na execução.

### Campos principais

| Campo | Descrição |
|---|---|
| `created_at_utc` | Data UTC do registro |
| `silver_layer` | Nome da camada |
| `source_raw_manifest_path` | Manifesto RAW usado |
| `source_raw_path` | Arquivo RAW de origem |
| `source_name` | Fonte |
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `mission` | Missão |
| `raw_file_type` | Tipo RAW |
| `silver_file_path` | Caminho Silver |
| `silver_file_name` | Nome Silver |
| `silver_file_type` | Tipo Silver |
| `transformation_type` | Transformação |
| `row_count` | Linhas |
| `column_count` | Colunas |
| `status` | Status |
| `error_message` | Erro |
| `sha256` | Checksum Silver |
| `file_size_bytes` | Tamanho |
| `notes` | Notas |

## NASA `pscomppars_selected_planets.csv`

### Caminho

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
```

### Conteúdo

Uma linha por planeta configurado, com parâmetros compostos NASA.

### Campos científicos

| Campo | Descrição |
|---|---|
| `planet_name` | Nome do planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug do planeta |
| `discovery_method` | Método de descoberta |
| `discovery_facility` | Instalação de descoberta |
| `orbital_period_days` | Período orbital em dias |
| `orbital_period_err_plus` | Erro superior do período |
| `orbital_period_err_minus` | Erro inferior do período |
| `transit_midpoint` | Meio do trânsito |
| `transit_midpoint_err_plus` | Erro superior do meio do trânsito |
| `transit_midpoint_err_minus` | Erro inferior do meio do trânsito |
| `transit_duration_hours` | Duração do trânsito |
| `transit_duration_err_plus` | Erro superior da duração |
| `transit_duration_err_minus` | Erro inferior da duração |
| `transit_depth` | Profundidade do trânsito |
| `transit_depth_err_plus` | Erro superior da profundidade |
| `transit_depth_err_minus` | Erro inferior da profundidade |
| `planet_radius_earth` | Raio planetário em raios terrestres |
| `planet_radius_earth_err_plus` | Erro superior do raio terrestre |
| `planet_radius_earth_err_minus` | Erro inferior do raio terrestre |
| `planet_radius_jupiter` | Raio planetário em raios de Júpiter |
| `stellar_radius_solar` | Raio estelar em raios solares |
| `stellar_radius_solar_err_plus` | Erro superior do raio estelar |
| `stellar_radius_solar_err_minus` | Erro inferior do raio estelar |
| `stellar_teff` | Temperatura efetiva estelar |
| `stellar_mass_solar` | Massa estelar |
| `system_distance_pc` | Distância do sistema em parsecs |

### Campos de origem

| Campo | Descrição |
|---|---|
| `source_name` | Fonte |
| `source_raw_path` | CSV RAW usado |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do arquivo RAW |
| `silver_created_at_utc` | Data UTC de criação |

## NASA `ps_all_solutions.csv`

### Caminho

```text
data/silver/catalogs/nasa/ps_all_solutions.csv
```

### Conteúdo

Todas as linhas NASA `ps` por planeta.

### Campos adicionados

| Campo | Descrição |
|---|---|
| `planet_name` | Nome padronizado |
| `host_star` | Estrela padronizada |
| `planet_slug` | Slug |
| `solution_row_index` | Índice da solução dentro do CSV RAW |
| `source_name` | Fonte |
| `source_raw_path` | Arquivo RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome RAW |
| `silver_created_at_utc` | Data UTC de criação |

As demais colunas são preservadas da tabela NASA `ps`.

## NASA snapshot geral

### Caminho

```text
data/silver/catalogs/nasa/all_transiting_planets_snapshot.csv
```

### Conteúdo

Snapshot de planetas em trânsito com proveniência Silver.

### Uso

Contexto e exploração. Não é Gold.

## Exo.MAST

### Caminhos

```text
data/silver/catalogs/exomast/exomast_identifiers.csv
data/silver/catalogs/exomast/exomast_properties.csv
data/silver/catalogs/exomast/exomast_tces.csv
```

### Campos obrigatórios

| Campo | Descrição |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `exomast_file_type` | Tipo do JSON |
| `source_name` | Fonte |
| `source_raw_path` | Arquivo RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome RAW |
| `raw_metadata_json` | JSON original compacto |
| `silver_created_at_utc` | Data UTC |

As demais colunas vêm do flattening do JSON.

## MAST lightcurves

### Caminho por planeta e missão

```text
data/silver/lightcurves/mast/{planet_slug}/{mission}_lightcurve.csv
```

### Campos principais

| Campo | Descrição |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | FITS RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do FITS |
| `mission` | Missão |
| `source_fits_file` | Nome do FITS |
| `hdu_name` | Nome da HDU |
| `hdu_index` | Índice da HDU |
| `time` | Tempo fornecido pelo FITS |
| `time_unit` | Unidade de tempo |
| `time_reference` | Referência temporal |
| `sap_flux` | SAP_FLUX |
| `sap_flux_err` | SAP_FLUX_ERR |
| `pdcsap_flux` | PDCSAP_FLUX |
| `pdcsap_flux_err` | PDCSAP_FLUX_ERR |
| `quality` | QUALITY ou SAP_QUALITY |
| `cadence_number` | CADENCENO |
| `mom_centr1` | Centroide |
| `mom_centr2` | Centroide |
| `pos_corr1` | Correção de posição |
| `pos_corr2` | Correção de posição |
| `quarter` | Quarter Kepler |
| `sector` | Setor TESS |
| `campaign` | Campanha K2, se existisse |
| `camera` | Câmera |
| `ccd` | CCD |
| `object` | Objeto no header |
| `telescope` | Telescópio |
| `instrument` | Instrumento |
| `data_origin` | Autor ou criador do produto |
| `quality_is_zero` | Flag auxiliar |
| `quality_is_missing` | Flag auxiliar |
| `has_pdcsap_flux` | Presença de PDCSAP |
| `has_sap_flux` | Presença de SAP |
| `silver_created_at_utc` | Data UTC |

## MAST metadata

### Caminho

```text
data/silver/lightcurves/mast/mast_fits_metadata.csv
```

### Conteúdo

Uma linha por FITS.

Campos:

- identificação;
- proveniência;
- tamanho;
- checksum;
- HDUs;
- colunas disponíveis;
- colunas ausentes;
- intervalo de tempo;
- contagens de qualidade;
- status da extração.

## ETD observations

### Caminho

```text
data/silver/etd/etd_observations.csv
```

### Conteúdo

Observações públicas de trânsito.

Campos principais:

- `obs_id`;
- `trans_id`;
- `epoch`;
- `hjd_mid`;
- `jd_mid_err`;
- `duration`;
- `duration_err`;
- `depth`;
- `depth_err`;
- `dqi`;
- `band`;
- `observer`;
- `reference`;
- `reference_url`;
- `data_version`;
- `is_private`;
- `raw_metadata_json`.

## ETD points

### Caminho

```text
data/silver/etd/etd_lightcurve_points.csv
```

### Conteúdo

Pontos fotométricos das curvas públicas.

Campos principais:

- `obs_id`;
- `trans_id`;
- `point_index`;
- `jd`;
- `mag`;
- `mag_error`;
- `filter`;
- `airmass`;
- `mag_band`;
- `source_json_file`.

## ETD metadata

### Caminho

```text
data/silver/etd/etd_lightcurve_metadata.csv
```

### Conteúdo

Uma linha por JSON de curva.

Campos principais:

- `point_count`;
- `has_photometry`;
- `has_airmass`;
- `has_minimas`;
- `has_transits`;
- `mag_band`;
- `time_span`;
- `orig_raw_header_present`;
- `status`;
- `error_message`.

## Validações

### Caminhos

```text
data/silver/validation/raw_manifest_summary.csv
data/silver/validation/raw_manifest_validation.json
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/validation/silver_etd_summary.csv
data/silver/validation/silver_column_presence_report.csv
```

### Uso

Esses arquivos são a base para:

- auditoria;
- inventário;
- comparação entre planetas;
- seleção futura de Gold;
- descrição metodológica.
