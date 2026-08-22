# 05. MAST, Lightkurve e Astroquery

## Fontes

Fontes públicas:

```text
https://mast.stsci.edu/
https://exo.mast.stsci.edu/
```

Biblioteca principal usada para curvas de luz:

```text
lightkurve
```

Biblioteca de fallback:

```text
astroquery.mast.Observations
```

## Objetivo da coleta MAST

O objetivo foi buscar e baixar curvas de luz públicas das estrelas hospedeiras dos planetas candidatos.

As missões tentadas foram:

```text
Kepler
K2
TESS
```

Cada busca foi feita pela estrela hospedeira, não pelo nome do planeta, pois os produtos de curva de luz do MAST são associados ao alvo/estrela observada.

## Estrutura de diretórios

```text
data/raw/mast/
  lightkurve/
  astroquery/
  manifests/
```

Na execução validada, os dados efetivos ficaram em:

```text
data/raw/mast/lightkurve/
```

O fallback Astroquery não precisou baixar produtos, pois o Lightkurve funcionou.

## Estrutura por planeta e missão

Exemplo:

```text
data/raw/mast/lightkurve/hat_p_7_b/
  kepler/
    search_results.csv
    download_manifest.csv
    metadata.json
    mastDownload/
      Kepler/
        ...
  k2/
    search_results.csv
    download_manifest.csv
    metadata.json
  tess/
    search_results.csv
    download_manifest.csv
    metadata.json
    mastDownload/
      TESS/
        ...
```

## Arquivos por missão

Para cada planeta e missão, o pipeline salva:

```text
search_results.csv
download_manifest.csv
metadata.json
```

Quando há FITS baixado, ele fica dentro da estrutura `mastDownload` criada pelo Lightkurve.

Exemplo:

```text
data/raw/mast/lightkurve/hat_p_7_b/kepler/mastDownload/Kepler/kplr010666592_lc_Q111111111111111111/
```

## `search_results.csv`

É a tabela completa retornada por:

```python
lightkurve.search_lightcurve(host_star, mission=mission)
```

Ela é salva mesmo quando não há produtos.

Campos típicos:

- `mission`;
- `year`;
- `author`;
- `exptime`;
- `target_name`;
- `distance`;
- `productFilename`;
- `dataURI`.

Uso metodológico:

- demonstrar quais produtos foram encontrados;
- registrar missões sem dados;
- justificar seleção de subconjunto;
- permitir auditoria posterior.

## `download_manifest.csv`

Registra os produtos escolhidos para download.

Campos:

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

## `metadata.json`

Resume a busca por planeta/missão.

Registra:

- planeta;
- estrela hospedeira;
- missão;
- termo de busca;
- quantidade de resultados;
- quantidade de produtos selecionados;
- limite aplicado;
- política de seleção;
- status final.

## Política de seleção dos FITS

Para evitar download excessivo, foi aplicado:

```text
MAX_LIGHTCURVES_PER_MISSION = 3
```

A seleção favoreceu:

1. autores oficiais/pipeline reconhecido, como SPOC, Kepler e K2;
2. exposições mais longas, para controlar volume;
3. limite máximo de três por planeta/missão.

Essa política é conservadora: baixa um subconjunto suficiente para iniciar exploração futura sem transformar a etapa RAW em um espelho massivo do MAST.

## Contagem de buscas por missão

| Planeta | Kepler search rows | K2 search rows | TESS search rows |
|---|---:|---:|---:|
| HAT-P-7 b | 69 | 0 | 48 |
| TrES-2 b | 54 | 0 | 49 |
| HD 189733 b | 0 | 0 | 14 |
| HD 209458 b | 0 | 0 | 8 |
| WASP-12 b | 0 | 0 | 26 |
| WASP-10 b | 0 | 0 | 7 |
| WASP-4 b | 0 | 0 | 29 |
| HAT-P-32 b | 0 | 0 | 9 |

## FITS baixados por planeta

| Planeta | Kepler FITS | K2 FITS | TESS FITS | Total FITS |
|---|---:|---:|---:|---:|
| HAT-P-7 b | 3 | 0 | 3 | 6 |
| TrES-2 b | 3 | 0 | 3 | 6 |
| HD 189733 b | 0 | 0 | 3 | 3 |
| HD 209458 b | 0 | 0 | 3 | 3 |
| WASP-12 b | 0 | 0 | 3 | 3 |
| WASP-10 b | 0 | 0 | 3 | 3 |
| WASP-4 b | 0 | 0 | 3 | 3 |
| HAT-P-32 b | 0 | 0 | 3 | 3 |
| **Total** | **6** | **0** | **24** | **30** |

## Missões sem dados

Resultado observado:

- K2 retornou zero produtos para todos os planetas;
- Kepler retornou produtos para HAT-P-7 b e TrES-2 b;
- TESS retornou produtos para todos os planetas.

Isso não significa que a fonte MAST falhou. Significa apenas que, pela busca realizada por estrela hospedeira e missão, não havia produtos retornados para aquela missão.

## Exemplos de FITS baixados

HAT-P-7 b, Kepler:

```text
data/raw/mast/lightkurve/hat_p_7_b/kepler/mastDownload/Kepler/kplr010666592_lc_Q111111111111111111/
```

HAT-P-7 b, TESS:

```text
data/raw/mast/lightkurve/hat_p_7_b/tess/mastDownload/TESS/
```

TrES-2 b, Kepler:

```text
data/raw/mast/lightkurve/tres_2_b/kepler/mastDownload/Kepler/
```

WASP-12 b, TESS:

```text
data/raw/mast/lightkurve/wasp_12_b/tess/mastDownload/TESS/
```

## O que há dentro de um FITS

O pipeline não abre nem processa o conteúdo científico dos FITS nesta etapa.

Em geral, esses arquivos podem conter:

- cabeçalhos FITS;
- metadados da observação;
- tempo;
- fluxo;
- erro do fluxo;
- flags de qualidade;
- colunas específicas da missão.

A leitura dessas estruturas deve ficar para a camada Silver.

## O que não foi feito com as curvas

Nenhum FITS foi:

- convertido para CSV;
- normalizado;
- filtrado por qualidade;
- corrigido manualmente;
- faseado;
- agregado;
- plotado;
- usado para inferência.

## Fallback Astroquery

O código contém fallback com:

```python
astroquery.mast.Observations
```

Ele seria usado se o Lightkurve falhasse.

Na execução validada:

- Lightkurve funcionou;
- Astroquery não precisou baixar produtos;
- a pasta `data/raw/mast/astroquery` existe por estrutura, mas não é a fonte dos FITS coletados.

## Uso metodológico no TCC

Na metodologia, esta fonte pode ser descrita como:

> As curvas de luz espaciais foram coletadas a partir do MAST por meio da biblioteca Lightkurve, buscando produtos associados à estrela hospedeira de cada planeta. Para cada planeta foram testadas as missões Kepler, K2 e TESS. As tabelas completas de busca foram preservadas em CSV e um subconjunto limitado de até três produtos por missão foi baixado em formato FITS original, sem abertura ou transformação analítica na camada RAW.

