# 16. ETD / VarAstro na Camada Silver

## Objetivo deste documento

Este documento descreve como os dados terrestres públicos do ETD / VarAstro foram consolidados na camada Silver.

Entradas RAW:

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_raw.json
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_api_*.csv
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/*.json
```

Saídas Silver:

```text
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_points.csv
data/silver/etd/etd_lightcurve_metadata.csv
```

## Natureza dos dados ETD

Os dados ETD coletados na RAW são respostas públicas da API de visualização do portal.

Limitação importante:

```text
As curvas ETD salvas na RAW são JSONs públicos retornados pela API de visualização, não necessariamente os arquivos originais enviados pelos observadores.
```

Essa limitação foi preservada na documentação e deve aparecer na metodologia.

## `etd_observations.csv`

Caminho:

```text
data/silver/etd/etd_observations.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 1.650 |
| Colunas | 25 |

## Campos de observação

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | JSON/CSV RAW de origem |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do arquivo RAW |
| `obs_id` | Identificador de observação, quando disponível |
| `trans_id` | Identificador de trânsito, quando disponível |
| `epoch` | Época do trânsito |
| `hjd_mid` | Meio do trânsito em HJD |
| `jd_mid_err` | Incerteza do meio do trânsito |
| `duration` | Duração |
| `duration_err` | Incerteza da duração |
| `depth` | Profundidade |
| `depth_err` | Incerteza da profundidade |
| `dqi` | Data Quality Index informado pelo ETD |
| `band` | Filtro/banda |
| `observer` | Observador |
| `reference` | Referência textual |
| `reference_url` | URL de referência |
| `data_version` | Versão de dado |
| `is_private` | Indicador de privacidade |
| `raw_metadata_json` | Registro original compacto |
| `silver_created_at_utc` | Data UTC de criação |

## Tratamento de registros privados

A regra implementada foi:

1. Ler registros públicos e privados retornados pelo JSON, se existirem.
2. Contar registros privados.
3. Não incluir registros privados em `etd_observations.csv`.
4. Registrar contagem na validação.

Resultado validado:

```text
private_records_count = 0 para todos os planetas
```

## Observações por planeta

| Planeta | Observações públicas | Registros privados |
|---|---:|---:|
| HAT-P-7 b | 60 | 0 |
| TrES-2 b | 371 | 0 |
| HD 189733 b | 218 | 0 |
| HD 209458 b | 92 | 0 |
| WASP-12 b | 376 | 0 |
| WASP-10 b | 241 | 0 |
| WASP-4 b | 80 | 0 |
| HAT-P-32 b | 212 | 0 |

## `etd_lightcurve_points.csv`

Caminho:

```text
data/silver/etd/etd_lightcurve_points.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 8.752 |
| Colunas | 18 |

## Campos de pontos fotométricos

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | JSON RAW da curva |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do JSON RAW |
| `obs_id` | ID da observação |
| `trans_id` | ID do trânsito |
| `point_index` | Índice do ponto dentro da curva |
| `jd` | Tempo em JD |
| `mag` | Magnitude |
| `mag_error` | Erro da magnitude |
| `filter` | Filtro do ponto, quando disponível |
| `airmass` | Massa de ar alinhada por índice ou tempo |
| `mag_band` | Banda global informada no JSON |
| `source_json_file` | Nome do JSON de curva |
| `silver_created_at_utc` | Data UTC de criação |

## Pontos fotométricos por planeta

| Planeta | Curvas JSON | Pontos |
|---|---:|---:|
| HAT-P-7 b | 5 | 1.243 |
| TrES-2 b | 5 | 1.180 |
| HD 189733 b | 5 | 1.262 |
| HD 209458 b | 5 | 1.625 |
| WASP-12 b | 5 | 793 |
| WASP-10 b | 5 | 322 |
| WASP-4 b | 5 | 1.039 |
| HAT-P-32 b | 5 | 1.288 |

## Filtros observados

| Planeta | Filtros/bandas observados |
|---|---|
| HAT-P-7 b | `Clear`, `R`, `SLOAN 'r`, `V to IR` |
| TrES-2 b | `Clear`, `L`, `R`, `clear`, `r` |
| HD 189733 b | `Clear`, `R`, `i` |
| HD 209458 b | `Clear`, `I`, `R` |
| WASP-12 b | `CBB`, `Clear`, `Luminance`, `R`, `V to IR` |
| WASP-10 b | `Clear`, `IR-UV`, `L`, `R` |
| WASP-4 b | `Clear`, `Luminance`, `V` |
| HAT-P-32 b | `CV`, `IR`, `Sloan r'`, `V`, `r` |

## `etd_lightcurve_metadata.csv`

Caminho:

```text
data/silver/etd/etd_lightcurve_metadata.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 40 |
| Colunas | 21 |

Uma linha por JSON público de curva.

Campos:

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `source_json_file` | Arquivo JSON |
| `source_raw_path` | Caminho RAW |
| `obs_id` | ID da observação |
| `trans_id` | ID do trânsito |
| `point_count` | Quantidade de pontos |
| `has_photometry` | Presença do bloco `photometry` |
| `has_airmass` | Presença do bloco `airmass` |
| `has_minimas` | Presença do bloco `minimas` |
| `has_transits` | Presença do bloco `transits` |
| `mag_band` | Banda global |
| `time_span` | Intervalo de tempo |
| `orig_raw_header_present` | Presença de header original |
| `status` | Resultado |
| `error_message` | Erro, se houver |

## Decisões de implementação

### Magnitude preservada

A Silver manteve `mag` como magnitude.

Não foi feita conversão para fluxo.

Justificativa:

- a conversão envolve decisão científica;
- a etapa Silver deve evitar transformação analítica;
- a comparação com curvas espaciais deve ficar para etapa posterior.

### Airmass

Quando o bloco `airmass` existe e tem o mesmo comprimento da fotometria, a Silver alinha por índice.

Se necessário, também tenta alinhar por tempo.

Quando não há alinhamento claro, deixa vazio.

### `obs_id` e `trans_id`

Os IDs foram extraídos do nome do arquivo JSON quando presentes.

Exemplo:

```text
01_observation_94348_transit_12787.json
```

vira:

```text
obs_id = 94348
trans_id = 12787
```

## Validação ETD

Arquivo:

```text
data/silver/validation/silver_etd_summary.csv
```

Ele resume:

- observações por planeta;
- registros privados;
- curvas baixadas;
- pontos fotométricos;
- filtros observados;
- DQI mínimo e máximo.

## Limitações

- Curvas são JSONs públicos da API de visualização.
- Não há garantia de equivalência com o arquivo original do observador.
- Filtros podem vir com grafias heterogêneas.
- A qualidade DQI foi preservada, mas não usada para filtrar dados.
- Magnitude não foi convertida em fluxo.
- Não há harmonização temporal com MAST.

## Uso futuro

Na Gold, os dados ETD podem ser usados para:

- comparação qualitativa com curvas espaciais;
- validação externa de épocas de trânsito;
- estudo de incerteza observacional terrestre;
- seleção de curvas com DQI aceitável;
- análise de consistência temporal.

Essas decisões não foram tomadas na Silver.
