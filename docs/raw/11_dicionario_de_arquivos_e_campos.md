# 11. Dicionário de Arquivos, Campos e Localização das Informações

## Objetivo

Este documento é um mapa rápido para localizar informações na camada RAW.

Ele responde:

- onde está cada tipo de arquivo;
- que informação cada arquivo contém;
- se o arquivo é bruto ou extraído;
- qual fonte originou o conteúdo;
- quais campos principais podem ser encontrados.

## Classificação usada

| Classificação | Significado |
|---|---|
| Bruto | Conteúdo salvo como retornado pela fonte ou biblioteca de download |
| Sidecar | Arquivo criado pelo pipeline para explicar a coleta |
| Extraído | Tabela derivada de HTML/JSON público para facilitar rastreabilidade |
| Manifesto | Arquivo de controle com status, caminho, checksum e metadados |
| Log | Registro textual da execução |

## Manifesto global

### Caminho

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```

### Classificação

Manifesto.

### Conteúdo

Contém todos os eventos de coleta registrados pelo pipeline.

### Campos

| Campo | Descrição |
|---|---|
| `collected_at_utc` | Data/hora UTC do evento |
| `source_name` | Fonte lógica |
| `source_url` | URL de origem |
| `planet_name` | Planeta associado |
| `host_star` | Estrela hospedeira |
| `local_path` | Caminho local do arquivo |
| `file_name` | Nome do arquivo |
| `file_type` | Tipo/extensão |
| `mission` | Missão, quando aplicável |
| `product_type` | Produto lógico |
| `query_or_search_term` | Query ou busca |
| `status` | Resultado do evento |
| `error_message` | Erro, se houver |
| `sha256` | Checksum do arquivo local |
| `file_size_bytes` | Tamanho em bytes |
| `notes` | Notas adicionais |

## Log global

### Caminho

```text
data/raw/_logs/download_raw_data.log
```

### Classificação

Log.

### Conteúdo

Registra início, fim, fontes, planetas, missões, arquivos baixados, arquivos pulados, erros e warnings.

## NASA: parâmetros compostos `pscomppars`

### Caminho por planeta

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/response.csv
```

### Classificação

Bruto.

### Conteúdo

CSV retornado pelo endpoint TAP da NASA.

### Campos principais

| Campo | Conteúdo |
|---|---|
| `pl_name` | Nome do planeta |
| `hostname` | Estrela hospedeira |
| `discoverymethod` | Método de descoberta |
| `disc_facility` | Instalação de descoberta |
| `pl_orbper` | Período orbital |
| `pl_orbpererr1` | Erro superior do período |
| `pl_orbpererr2` | Erro inferior do período |
| `pl_tranmid` | Tempo de meio trânsito |
| `pl_tranmiderr1` | Erro superior do meio trânsito |
| `pl_tranmiderr2` | Erro inferior do meio trânsito |
| `pl_trandur` | Duração do trânsito |
| `pl_trandurerr1` | Erro superior da duração |
| `pl_trandurerr2` | Erro inferior da duração |
| `pl_trandep` | Profundidade do trânsito |
| `pl_trandeperr1` | Erro superior da profundidade |
| `pl_trandeperr2` | Erro inferior da profundidade |
| `pl_rade` | Raio planetário em raios terrestres |
| `pl_radeerr1` | Erro superior do raio em raios terrestres |
| `pl_radeerr2` | Erro inferior do raio em raios terrestres |
| `pl_radj` | Raio planetário em raios de Júpiter |
| `st_rad` | Raio estelar |
| `st_raderr1` | Erro superior do raio estelar |
| `st_raderr2` | Erro inferior do raio estelar |
| `st_teff` | Temperatura efetiva estelar |
| `st_mass` | Massa estelar |
| `sy_dist` | Distância do sistema |

## NASA: tabela `ps`

### Caminho por planeta

```text
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/response.csv
```

### Classificação

Bruto.

### Conteúdo

CSV retornado pelo endpoint TAP da NASA com múltiplas linhas possíveis por planeta.

### Como interpretar

Enquanto `pscomppars` retornou uma linha por planeta, `ps` retornou múltiplas linhas por planeta, refletindo diferentes entradas/referências/soluções catalográficas.

## NASA: queries

### Caminho

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/query.sql
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/query.sql
```

ou versões:

```text
query_query_<hash>.sql
```

### Classificação

Sidecar.

### Conteúdo

ADQL executada ou tentativa histórica.

## NASA: metadados

### Caminho

```text
metadata.json
metadata_query_<hash>.json
```

### Classificação

Sidecar.

### Conteúdo

Registra:

- query;
- planeta;
- estrela;
- tabela;
- status;
- colunas selecionadas;
- URL de requisição;
- número estimado de linhas, quando disponível.

## NASA: snapshot de planetas em trânsito

### Caminho

```text
data/raw/nasa_exoplanet_archive/pscomppars/all_transiting_planets_snapshot.csv
```

### Classificação

Bruto filtrado por query.

### Conteúdo

CSV retornado pela NASA com planetas de descoberta por trânsito, período orbital não nulo e raio planetário ou profundidade disponível.

## MAST: tabela de busca

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/search_results.csv
```

### Classificação

Bruto de busca.

### Conteúdo

Tabela retornada por `lightkurve.search_lightcurve`.

### Campos comuns

| Campo | Descrição |
|---|---|
| `mission` | Produto/missão |
| `year` | Ano ou identificador temporal |
| `author` | Autor/pipeline do produto |
| `exptime` | Tempo de exposição |
| `target_name` | Nome do alvo |
| `distance` | Distância angular da busca |
| `productFilename` | Nome do produto |
| `dataURI` | URI de download no MAST |

## MAST: FITS de curva de luz

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/mastDownload/
```

### Classificação

Bruto.

### Conteúdo

Arquivos FITS originais baixados via Lightkurve.

### Como interpretar

Não foram abertos nem transformados nesta etapa. A leitura dos HDUs e colunas deve ocorrer na Silver.

## MAST: manifesto de download por missão

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/download_manifest.csv
```

### Classificação

Manifesto local da fonte.

### Campos

```text
collected_at_utc
planet_name
host_star
mission
author
target_name
product_filename
data_uri
local_path
status
error_message
sha256
file_size_bytes
```

## MAST: metadata por missão

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/metadata.json
```

### Classificação

Sidecar.

### Conteúdo

Resumo da busca:

- planeta;
- estrela;
- missão;
- termo de busca;
- quantidade de resultados;
- limite de download;
- quantidade selecionada;
- política de seleção.

## Exo.MAST: identificadores

### Caminho

```text
data/raw/exomast/{planet_slug}/identifiers.json
```

### Classificação

Bruto.

### Conteúdo

Resposta JSON da API pública de identificadores.

### Uso

- nome canônico;
- IDs de missão;
- vínculo com Kepler/TESS.

## Exo.MAST: propriedades

### Caminho

```text
data/raw/exomast/{planet_slug}/properties.json
```

### Classificação

Bruto.

### Conteúdo

Propriedades públicas retornadas pela API Exo.MAST.

## Exo.MAST: TCEs

### Caminho

```text
data/raw/exomast/{planet_slug}/kepler_tces.json
data/raw/exomast/{planet_slug}/tess_tces.json
```

### Classificação

Bruto.

### Conteúdo

Listas de TCEs associadas ao planeta ou alvo quando a API fornece identificador correspondente.

## ETD: snapshot HTML da busca

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/catalog_search.html
```

### Classificação

Bruto.

### Conteúdo

HTML público da página do catálogo de exoplanetas.

## ETD: JSON de resultado da busca

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/catalog_search_results.json
```

### Classificação

Bruto.

### Conteúdo

JSON retornado pelo endpoint público:

```text
/api/Search/Exoplanets
```

Campos úteis:

- ID interno do planeta;
- nome;
- status;
- profundidade;
- duração;
- período;
- contagem de trânsitos.

## ETD: página de detalhe

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/planet_detail.html
```

### Classificação

Bruto.

### Conteúdo

HTML público da página do planeta no VarAstro.

## ETD: observações brutas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_raw.json
```

### Classificação

Bruto.

### Conteúdo

Resposta pública do endpoint:

```text
/api/OcGate/Exoplanets/{id}
```

Campos comuns em cada trânsito:

| Campo | Descrição |
|---|---|
| `band` | Banda/filtro fotométrico |
| `dataVersion` | Versão dos dados no VarAstro |
| `depth` | Profundidade |
| `depthErr` | Erro da profundidade |
| `dqi` | Indicador de qualidade |
| `duration` | Duração |
| `durationErr` | Erro da duração |
| `epoch` | Época |
| `hjdMid` | Meio trânsito em HJD |
| `jdMidErr` | Erro do meio trânsito |
| `obsId` | ID da observação |
| `observer` | Observador |
| `reference` | Referência |
| `referenceUrl` | URL de referência |
| `transId` | ID do trânsito |
| `isPrivate` | Indicador de privacidade |

## ETD: observações extraídas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_api_<hash>.csv
```

### Classificação

Extraído.

### Conteúdo

Tabela CSV derivada de `observations_raw.json`, mantendo a linha original serializada em `raw_metadata_json`.

## ETD: curvas JSON públicas

### Caminho

```text
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/NN_observation_{obsId}_transit_{transId}.json
```

### Classificação

Bruto.

### Conteúdo

Resposta pública do endpoint:

```text
/api/charts/observation/{obsId}
```

Campos observados:

```text
timeSpan
photometry
minimas
transits
airmass
origRawHeader
magBand
```

Dentro de `photometry`, foram observados:

```text
jd
mag
magError
filter
```

## ETD: notas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/notes.md
data/raw/etd_varastro/extracted_metadata/{planet_slug}/notes_api_<hash>.md
```

### Classificação

Sidecar.

### Conteúdo

Explica:

- URLs consultadas;
- número de linhas extraídas;
- número de curvas selecionadas;
- limites;
- erros;
- limitações.

## ETD: manifesto por planeta

### Caminho

```text
data/raw/etd_varastro/manifests/{planet_slug}_manifest*.csv
```

### Classificação

Manifesto local da fonte.

### Conteúdo

Registra arquivos ETD/VarAstro por planeta, com status, checksum, tamanho e notas.

## Arquivos soltos na raiz de `data/raw`

### Situação atual

Não há arquivos CSV soltos na raiz de `data/raw`.

### Decisão de limpeza

Três arquivos manuais antigos foram removidos durante revisão posterior, porque:

- não estavam registrados no manifesto RAW;
- não tinham checksums controlados pelo pipeline;
- não eram usados pela Silver;
- não eram usados pela Gold;
- duplicavam ou antecediam coletas depois feitas de forma estruturada.

### Interpretação

A camada RAW válida para rastreabilidade é composta pelos arquivos nas subpastas por fonte e pelo manifesto global:

```text
data/raw/_manifests/raw_data_manifest.csv
```
