# 03. Manifestos, Logs, Checksums e Reexecução

## Manifesto global

O manifesto global em CSV está em:

```text
data/raw/_manifests/raw_data_manifest.csv
```

A versão JSON está em:

```text
data/raw/_manifests/raw_data_manifest.json
```

Ambos representam a mesma visão acumulada da coleta.

## Quantidade de registros no manifesto

Na auditoria final:

```text
raw_data_manifest.csv: 749 linhas de dados
raw_data_manifest.json: 749 registros
```

## Colunas do manifesto

As colunas são:

| Coluna | Significado |
|---|---|
| `collected_at_utc` | Data/hora UTC do evento de coleta ou registro |
| `source_name` | Nome lógico da fonte |
| `source_url` | URL consultada ou URL de origem do arquivo |
| `planet_name` | Nome do planeta, quando aplicável |
| `host_star` | Estrela hospedeira, quando aplicável |
| `local_path` | Caminho local relativo ao projeto |
| `file_name` | Nome do arquivo local |
| `file_type` | Extensão ou tipo lógico do arquivo |
| `mission` | Missão astronômica, quando aplicável |
| `product_type` | Tipo de produto coletado |
| `query_or_search_term` | Query, termo de busca ou identificador usado |
| `status` | Resultado do evento |
| `error_message` | Mensagem de erro, se houver |
| `sha256` | Checksum SHA256 do arquivo local |
| `file_size_bytes` | Tamanho do arquivo em bytes |
| `notes` | Observações adicionais |

## Contagem por fonte

| Fonte | Registros no manifesto |
|---|---:|
| ETD / VarAstro | 320 |
| MAST / Lightkurve | 204 |
| NASA Exoplanet Archive | 157 |
| Exo.MAST | 68 |

## Contagem por status

| Status | Registros |
|---|---:|
| `downloaded` | 369 |
| `skipped_existing` | 317 |
| `failed` | 33 |
| `downloaded_or_cached` | 30 |

## Interpretação dos status

### `downloaded`

Arquivo novo salvo pelo pipeline.

Exemplos:

- CSV do NASA TAP;
- HTML do ETD;
- JSON do Exo.MAST;
- JSON de curva ETD;
- manifesto por fonte.

### `downloaded_or_cached`

Usado para FITS do MAST baixados por Lightkurve. O Lightkurve pode retornar um arquivo já presente em cache local da pasta definida. O pipeline registra o caminho e calcula SHA256 da mesma forma.

### `skipped_existing`

Arquivo já existia e não foi substituído.

Esse status é esperado em reexecuções.

### `failed`

Falha registrada sem interromper o pipeline.

As falhas observadas ocorreram principalmente durante:

- tentativa inicial com rede bloqueada pela sandbox;
- exploração inicial do ETD antes de usar o endpoint público correto.

A execução final completa não apresentou falhas de fonte.

## Contagem por tipo de produto

Produtos mais frequentes no manifesto:

| Produto | Registros |
|---|---:|
| `ground_based_light_curve_api_json` | 80 |
| `light_curve` | 60 |
| `collection_notes` | 56 |
| `tap_query` | 51 |
| `collection_metadata` | 51 |
| `search_results` | 48 |
| `download_manifest` | 48 |
| `search_metadata` | 48 |
| `catalog_search_snapshot` | 40 |
| `extracted_public_metadata` | 40 |
| `source_manifest` | 40 |
| `pscomppars` | 24 |
| `ps` | 24 |
| `catalog_search_api_response` | 24 |
| `planet_detail_snapshot` | 24 |
| `tce_list` | 20 |
| `planet_identifiers` | 16 |
| `planet_properties` | 16 |
| `public_transit_observations_api_response` | 16 |
| `tap_schema` | 4 |
| `pscomppars_transiting_snapshot` | 3 |

## Logs

O log principal está em:

```text
data/raw/_logs/download_raw_data.log
```

O log registra:

- início da execução;
- fim da execução;
- fontes processadas;
- planetas processados;
- missões processadas;
- arquivos baixados;
- arquivos pulados;
- erros;
- warnings.

Trecho lógico da execução final:

```text
RAW pipeline started ... sources=nasa,mast,exomast,etd
Starting NASA Exoplanet Archive collection
Finished NASA Exoplanet Archive collection
Starting MAST light-curve collection
Finished MAST light-curve collection
Starting Exo.MAST metadata collection
Finished Exo.MAST metadata collection
Starting ETD / VarAstro collection
Finished ETD / VarAstro collection
RAW pipeline finished ... source_level_failures=0
```

## Checksums SHA256

Cada arquivo registrado no manifesto com `local_path` tem:

- SHA256;
- tamanho em bytes;
- caminho local;
- nome do arquivo.

Validação final:

```text
Arquivos locais ausentes no manifesto: 0
Checksums em branco para arquivos locais: 0
Divergências de checksum: 0
```

## Reexecução

O pipeline é reexecutável.

Comportamento esperado:

1. Se o arquivo ainda não existe, baixa e registra `downloaded`.
2. Se o arquivo existe, não substitui e registra `skipped_existing`.
3. Se um sidecar mudou, cria versão com hash.
4. Se uma fonte falhar, registra `failed` e continua.
5. Ao final, regrava atomicamente o manifesto global como visão acumulada.

## Escrita atômica

O pipeline escreve arquivos por meio de arquivos temporários `.part` e depois usa substituição atômica quando adequado.

Isso reduz o risco de:

- arquivo truncado;
- manifesto incompleto;
- escrita interrompida;
- inconsistência entre conteúdo e checksum.

## Por que manter falhas no manifesto?

Manter falhas é parte da rastreabilidade.

Em metodologia de coleta, isso ajuda a demonstrar:

- quais fontes foram tentadas;
- quando falharam;
- por que falharam;
- como a coleta foi repetida;
- qual execução final foi bem-sucedida.

As falhas não significam ausência de dados finais. Elas indicam tentativas históricas preservadas.

