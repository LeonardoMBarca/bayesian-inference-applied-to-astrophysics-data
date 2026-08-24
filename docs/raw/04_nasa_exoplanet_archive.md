# 04. NASA Exoplanet Archive

## Fonte

Fonte pública:

```text
https://exoplanetarchive.ipac.caltech.edu/
```

Endpoint programático usado:

```text
https://exoplanetarchive.ipac.caltech.edu/TAP/sync
```

Tipo de acesso:

- TAP síncrono;
- queries ADQL;
- retorno em CSV;
- sem autenticação;
- sem scraping.

## Objetivo da coleta NASA

A coleta NASA teve como objetivo registrar parâmetros catalográficos planetários e estelares para todos os planetas candidatos.

Foram consultadas duas tabelas:

```text
pscomppars
ps
```

Também foi baixado um snapshot geral de planetas confirmados em trânsito.

## Estrutura de diretórios

```text
data/raw/nasa_exoplanet_archive/
  pscomppars/
  ps/
  manifests/
```

### Diretório `pscomppars`

Contém:

- uma pasta por planeta;
- `response.csv` por planeta;
- `query.sql` ou versão hash da query;
- `metadata.json` ou versão hash do metadata;
- snapshot geral `all_transiting_planets_snapshot.csv`.

Exemplo:

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_7_b/
  response.csv
  query.sql
  query_query_b819ea7b4acd.sql
  metadata.json
  metadata_query_6a5ddfbed4d8.json
```

Observação: alguns arquivos `query.sql` e `metadata.json` refletem tentativas iniciais com rede bloqueada. As versões com hash registram a query/metadado da execução posterior com dados coletados.

### Diretório `ps`

Contém a mesma lógica de organização, mas para a tabela `ps`.

Exemplo:

```text
data/raw/nasa_exoplanet_archive/ps/tres_2_b/
  response.csv
  query.sql
  query_query_1dfccb533bd7.sql
  metadata.json
  metadata_query_f3cd9e55759d.json
```

### Diretório `manifests`

Contém snapshots de esquema TAP:

```text
data/raw/nasa_exoplanet_archive/manifests/ps_schema.csv
data/raw/nasa_exoplanet_archive/manifests/pscomppars_schema.csv
```

Esses arquivos foram usados para adaptar dinamicamente as colunas solicitadas.

## Por que consultar o esquema TAP?

O NASA Exoplanet Archive pode alterar colunas ao longo do tempo.

Para evitar falha por coluna inexistente, o pipeline primeiro consultou:

```sql
SELECT column_name
FROM TAP_SCHEMA.columns
WHERE table_name = 'pscomppars'
```

e:

```sql
SELECT column_name
FROM TAP_SCHEMA.columns
WHERE table_name = 'ps'
```

Depois, manteve apenas as colunas configuradas que realmente existiam no esquema atual.

## Colunas desejadas

As colunas desejadas são configuradas em `src/raw_ingestion/config.py`
(`scripts/raw_data_config.py` permanece como compatibilidade):

```text
pl_name
hostname
discoverymethod
disc_facility
pl_orbper
pl_orbpererr1
pl_orbpererr2
pl_tranmid
pl_tranmiderr1
pl_tranmiderr2
pl_trandur
pl_trandurerr1
pl_trandurerr2
pl_trandep
pl_trandeperr1
pl_trandeperr2
pl_rade
pl_radeerr1
pl_radeerr2
pl_radj
st_rad
st_raderr1
st_raderr2
st_teff
st_mass
sy_dist
rowupdate
releasedate
```

Na execução validada, o cabeçalho final de `pscomppars` para HAT-P-7 b foi:

```text
pl_name,hostname,discoverymethod,disc_facility,pl_orbper,pl_orbpererr1,pl_orbpererr2,pl_tranmid,pl_tranmiderr1,pl_tranmiderr2,pl_trandur,pl_trandurerr1,pl_trandurerr2,pl_trandep,pl_trandeperr1,pl_trandeperr2,pl_rade,pl_radeerr1,pl_radeerr2,pl_radj,st_rad,st_raderr1,st_raderr2,st_teff,st_mass,sy_dist
```

As colunas `rowupdate` e `releasedate` estavam na lista desejada, mas não aparecem nesse cabeçalho final porque a seleção foi adaptada ao esquema disponível.

## Query por planeta

Modelo lógico:

```sql
SELECT <colunas_disponiveis>
FROM pscomppars
WHERE pl_name = '<nome_do_planeta>'
```

Exemplo para HAT-P-7 b:

```sql
SELECT pl_name, hostname, discoverymethod, disc_facility, pl_orbper, pl_orbpererr1, pl_orbpererr2, pl_tranmid, pl_tranmiderr1, pl_tranmiderr2, pl_trandur, pl_trandurerr1, pl_trandurerr2, pl_trandep, pl_trandeperr1, pl_trandeperr2, pl_rade, pl_radeerr1, pl_radeerr2, pl_radj, st_rad, st_raderr1, st_raderr2, st_teff, st_mass, sy_dist
FROM pscomppars
WHERE pl_name = 'HAT-P-7 b'
```

O arquivo bruto correspondente fica em:

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_7_b/response.csv
```

## Diferença entre `pscomppars` e `ps`

### `pscomppars`

Foi usado como tabela principal de parâmetros compostos.

Resultado observado:

- um registro por planeta candidato.

Uso futuro provável:

- base catalográfica principal para parâmetros orbitais, planetários e estelares;
- apoio na seleção da camada Gold;
- comparação com parâmetros derivados futuramente.

### `ps`

Foi usado como tabela complementar.

Resultado observado:

- múltiplas linhas por planeta;
- representa diferentes entradas/soluções/referências disponíveis no arquivo.

Uso futuro provável:

- avaliar múltiplas referências;
- rastrear variações de parâmetros publicados;
- escolher valores conforme critério metodológico da Silver/Gold.

## Contagem de registros por planeta

| Planeta | Slug | `pscomppars` | Linhas em `ps` |
|---|---|---:|---:|
| HAT-P-7 b | `hat_p_7_b` | 1 | 24 |
| TrES-2 b | `tres_2_b` | 1 | 34 |
| HD 189733 b | `hd_189733_b` | 1 | 21 |
| HD 209458 b | `hd_209458_b` | 1 | 23 |
| WASP-12 b | `wasp_12_b` | 1 | 19 |
| WASP-10 b | `wasp_10_b` | 1 | 11 |
| WASP-4 b | `wasp_4_b` | 1 | 22 |
| HAT-P-32 b | `hat_p_32_b` | 1 | 13 |

## Snapshot geral de planetas em trânsito

Arquivo:

```text
data/raw/nasa_exoplanet_archive/pscomppars/all_transiting_planets_snapshot.csv
```

Query lógica:

```sql
SELECT <colunas_disponiveis>
FROM pscomppars
WHERE discoverymethod = 'Transit'
  AND pl_orbper IS NOT NULL
  AND (pl_rade IS NOT NULL OR pl_trandep IS NOT NULL)
ORDER BY pl_name
```

Resultado:

```text
4.653 registros de dados + cabeçalho
```

Esse snapshot não é a camada Gold. Ele é apenas uma fotografia RAW filtrada de planetas em trânsito para apoiar seleção futura.

## Arquivos salvos por planeta

Para cada planeta em `pscomppars`:

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/response.csv
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/query.sql
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/metadata.json
```

Para cada planeta em `ps`:

```text
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/response.csv
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/query.sql
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/metadata.json
```

Quando houve tentativa anterior diferente, podem existir variações:

```text
query_query_<hash>.sql
metadata_query_<hash>.json
```

## Como interpretar `response.csv`

`response.csv` é o retorno bruto do TAP.

Ele não foi:

- limpo;
- normalizado;
- reordenado manualmente;
- convertido para outro schema;
- preenchido com dados estimados.

Na futura Silver, será possível:

- validar tipos;
- padronizar nomes;
- selecionar colunas;
- harmonizar unidades;
- escolher referência preferencial.

## Como interpretar `query.sql`

`query.sql` ou `query_query_<hash>.sql` documenta a consulta usada.

Isso permite:

- reproduzir a extração;
- saber quais colunas foram solicitadas;
- verificar o filtro por planeta;
- auditar mudanças de esquema.

## Como interpretar `metadata.json`

`metadata.json` ou `metadata_query_<hash>.json` registra:

- data/hora UTC;
- tabela consultada;
- planeta;
- estrela hospedeira;
- query;
- status;
- colunas selecionadas;
- URL de requisição quando aplicável;
- número estimado de linhas, quando houve download.

## Observação sobre tentativas iniciais

Alguns `metadata.json` originais registram falhas de DNS da primeira execução em sandbox. Eles foram preservados porque fazem parte do histórico de coleta.

Os arquivos com hash registram a consulta válida posterior.

Exemplo:

```text
metadata.json
metadata_query_6a5ddfbed4d8.json
```

Isso significa:

- `metadata.json`: tentativa histórica inicial;
- `metadata_query_...json`: sidecar da reexecução bem-sucedida ou de revalidação.

## Uso metodológico no TCC

Na metodologia, esta fonte pode ser descrita como:

> Os parâmetros catalográficos foram obtidos do NASA Exoplanet Archive por meio do endpoint TAP síncrono, em formato CSV, com consultas ADQL geradas programaticamente. Antes das consultas por planeta, o esquema das tabelas foi consultado para evitar dependência rígida de colunas que poderiam não estar disponíveis. Os arquivos retornados foram preservados na camada RAW, acompanhados de query, metadados, manifesto e checksum SHA256.

