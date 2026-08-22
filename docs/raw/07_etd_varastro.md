# 07. ETD / VarAstro

## Fonte

Fonte pública:

```text
https://var.astro.cz/en/Home/ETD
https://var.astro.cz/en/Exoplanets
```

## Objetivo da coleta ETD

O objetivo foi tentar obter dados públicos terrestres de trânsitos de exoplanetas.

A coleta respeitou as restrições:

- sem login;
- sem Selenium;
- sem automação de navegador;
- sem bypass de proteção;
- sem uso de dados privados;
- com delay entre requisições;
- com User-Agent explícito;
- com registro das URLs consultadas.

## Estrutura de diretórios

```text
data/raw/etd_varastro/
  html_snapshots/
  extracted_metadata/
  downloaded_lightcurves/
  manifests/
```

## Fluxo de coleta

Para cada planeta:

1. consultar a página pública do catálogo;
2. salvar HTML da busca;
3. usar o endpoint público anônimo usado pelo DataTable do próprio site;
4. salvar JSON de resultado da busca;
5. identificar o ID do planeta no VarAstro;
6. salvar HTML da página de detalhe;
7. consultar endpoint público de observações;
8. verificar se há registros marcados como privados;
9. salvar JSON bruto de observações;
10. extrair metadados para CSV;
11. baixar até cinco curvas JSON públicas;
12. registrar manifesto por planeta.

## Delay entre requisições

Foi usado:

```text
ETD_REQUEST_DELAY_SECONDS = 2.0
```

Isso reduz agressividade e respeita boas práticas de consulta.

## Token anônimo público

O site público VarAstro entrega um cookie anônimo de acesso para navegação pública.

O pipeline não realizou login. Ele apenas usou o fluxo anônimo que a própria página pública usa para consultar os endpoints de catálogo e observações.

Isso foi necessário porque a tabela pública do catálogo é carregada via JavaScript.

## Snapshots HTML

Pasta:

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/
```

Arquivos:

```text
catalog_search.html
catalog_search_results.json
planet_detail.html
```

### `catalog_search.html`

Snapshot da página pública:

```text
https://var.astro.cz/en/Exoplanets?name=<planet_name>
```

Esse HTML registra o estado da página de busca, incluindo scripts, formulários e links públicos.

### `catalog_search_results.json`

Resposta bruta do endpoint público usado pelo DataTable:

```text
/api/Search/Exoplanets?pageId=1&pageSize=20&name=<planet_name>
```

Esse JSON contém o ID interno do planeta no VarAstro e metadados de catálogo.

### `planet_detail.html`

Snapshot da página pública de detalhe:

```text
https://var.astro.cz/en/Exoplanets/{id}
```

Ele registra:

- parâmetros exibidos pelo portal;
- link para lista de observações;
- contagens de trânsitos;
- scripts e endpoints públicos usados pela página.

## Metadados extraídos

Pasta:

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/
```

Arquivos principais:

```text
observations.csv
observations_api_<hash>.csv
observations_raw.json
notes.md
notes_api_<hash>.md
```

### `observations_raw.json`

Resposta bruta do endpoint público:

```text
/api/OcGate/Exoplanets/{id}
```

Esse JSON contém a lista pública de trânsitos/observações associadas ao planeta.

Antes de salvar, o pipeline verifica se algum registro tem:

```text
isPrivate = true
```

Na coleta validada:

```text
registros privados retornados: 0
```

para todos os planetas.

### `observations_api_<hash>.csv`

CSV extraído a partir do JSON público de observações.

Campos:

```text
planet
epoch
mid_transit_time
duration
depth
quality
filter
observer
light_curve_url
source_url
table_index
row_index
raw_metadata_json
```

Importante:

- esse CSV é metadado extraído;
- o JSON bruto continua salvo em `observations_raw.json`;
- valores não foram estimados;
- `raw_metadata_json` preserva a linha original serializada.

## Contagem de observações públicas ETD

| Planeta | Observações públicas em `observations_raw.json` | Registros privados |
|---|---:|---:|
| HAT-P-7 b | 60 | 0 |
| TrES-2 b | 371 | 0 |
| HD 189733 b | 218 | 0 |
| HD 209458 b | 92 | 0 |
| WASP-12 b | 376 | 0 |
| WASP-10 b | 241 | 0 |
| WASP-4 b | 80 | 0 |
| HAT-P-32 b | 212 | 0 |

## Curvas JSON públicas

Pasta:

```text
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/
```

Limite aplicado:

```text
MAX_ETD_LIGHTCURVES_PER_PLANET = 5
```

Foram salvas cinco respostas JSON por planeta, totalizando:

```text
40 curvas JSON públicas
```

Exemplo:

```text
data/raw/etd_varastro/downloaded_lightcurves/hat_p_32_b/01_observation_111341_transit_22572.json
```

## Endpoint das curvas JSON

Modelo:

```text
/api/charts/observation/{obsId}?origrawheader=true&airmass=true&v={dataVersion}&transid={transId}
```

Esses arquivos são respostas públicas da API usada pela página de visualização do VarAstro.

Eles podem conter:

- `timeSpan`;
- `photometry`;
- `minimas`;
- `transits`;
- `airmass`;
- `origRawHeader`;
- `magBand`.

No exemplo inspecionado, `photometry` continha pontos com:

```text
jd
mag
magError
filter
```

## Importante: diferença entre curva JSON e arquivo original do observador

Os arquivos JSON salvos são respostas da API pública de visualização.

Eles não devem ser descritos como o arquivo original enviado pelo observador, a menos que uma etapa futura confirme isso explicitamente.

Formulação recomendada:

> Foram preservadas respostas JSON públicas da API de visualização do VarAstro, contendo séries fotométricas e metadados associados, sem conversão ou transformação.

## Manifestos por planeta

Pasta:

```text
data/raw/etd_varastro/manifests/
```

Arquivos:

```text
{planet_slug}_manifest.csv
{planet_slug}_manifest_api.csv
{planet_slug}_manifest_api_<hash>.csv
```

Os arquivos com hash aparecem por causa de tentativas e reexecuções versionadas.

Campos:

```text
collected_at_utc
planet_name
host_star
source_url
local_path
file_type
product_type
status
error_message
sha256
file_size_bytes
notes
```

## Observações sobre tentativas iniciais

Na primeira tentativa, o pipeline salvou HTML e registrou ausência de curva direta em links visíveis.

Depois, foi identificado o endpoint público usado pelo próprio DataTable do portal. A coleta foi então enriquecida com:

- `catalog_search_results.json`;
- `observations_raw.json`;
- `observations_api_<hash>.csv`;
- curvas JSON públicas.

As tentativas iniciais continuam preservadas por rastreabilidade.

## O que não foi feito no ETD

Não foi feito:

- login;
- cadastro;
- raspagem agressiva;
- Selenium;
- automação de navegador;
- download de dados privados;
- tentativa de contornar autenticação;
- conversão de JSON para formato analítico final;
- normalização de curvas terrestres.

## Uso metodológico no TCC

Na metodologia, esta fonte pode ser descrita como:

> Para dados terrestres, foi consultado o portal ETD/VarAstro. A coleta utilizou páginas públicas e os endpoints anônimos consumidos pelo próprio front-end do site, com delay entre requisições e sem login. Foram preservados snapshots HTML, respostas JSON de catálogo, respostas JSON de observações públicas e até cinco respostas JSON de curvas por planeta. Registros marcados como privados foram explicitamente verificados, e nenhum registro privado foi retornado na coleta validada.

