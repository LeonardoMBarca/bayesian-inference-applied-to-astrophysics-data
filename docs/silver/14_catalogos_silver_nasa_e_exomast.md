# 14. Catálogos Silver: NASA Exoplanet Archive e Exo.MAST

## Objetivo deste documento

Este documento descreve a consolidação dos catálogos astronômicos na camada Silver.

Fontes cobertas:

- NASA Exoplanet Archive;
- Exo.MAST.

O foco foi transformar arquivos RAW catalográficos em tabelas CSV padronizadas, mantendo proveniência para cada linha.

## NASA Exoplanet Archive

### Entradas RAW

Para cada planeta:

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/response.csv
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/response.csv
```

Snapshot geral:

```text
data/raw/nasa_exoplanet_archive/pscomppars/all_transiting_planets_snapshot.csv
```

### Saídas Silver

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/nasa/ps_all_solutions.csv
data/silver/catalogs/nasa/all_transiting_planets_snapshot.csv
```

## `pscomppars_selected_planets.csv`

Tabela com uma linha por planeta configurado.

Resultado final:

| Métrica | Valor |
|---|---:|
| Linhas | 8 |
| Colunas | 32 |
| Planetas com linha | 8 |

### Interpretação

A tabela `pscomppars` do NASA Exoplanet Archive contém parâmetros compostos recomendados para planetas confirmados.

Na Silver, ela foi usada como catálogo principal para parâmetros planetários e estelares iniciais.

### Mapeamento de colunas

| RAW NASA | Silver |
|---|---|
| `pl_name` | `planet_name` |
| `hostname` | `host_star` |
| `discoverymethod` | `discovery_method` |
| `disc_facility` | `discovery_facility` |
| `pl_orbper` | `orbital_period_days` |
| `pl_orbpererr1` | `orbital_period_err_plus` |
| `pl_orbpererr2` | `orbital_period_err_minus` |
| `pl_tranmid` | `transit_midpoint` |
| `pl_tranmiderr1` | `transit_midpoint_err_plus` |
| `pl_tranmiderr2` | `transit_midpoint_err_minus` |
| `pl_trandur` | `transit_duration_hours` |
| `pl_trandurerr1` | `transit_duration_err_plus` |
| `pl_trandurerr2` | `transit_duration_err_minus` |
| `pl_trandep` | `transit_depth` |
| `pl_trandeperr1` | `transit_depth_err_plus` |
| `pl_trandeperr2` | `transit_depth_err_minus` |
| `pl_rade` | `planet_radius_earth` |
| `pl_radeerr1` | `planet_radius_earth_err_plus` |
| `pl_radeerr2` | `planet_radius_earth_err_minus` |
| `pl_radj` | `planet_radius_jupiter` |
| `st_rad` | `stellar_radius_solar` |
| `st_raderr1` | `stellar_radius_solar_err_plus` |
| `st_raderr2` | `stellar_radius_solar_err_minus` |
| `st_teff` | `stellar_teff` |
| `st_mass` | `stellar_mass_solar` |
| `sy_dist` | `system_distance_pc` |

### Colunas de proveniência

Além dos campos científicos, foram adicionadas:

| Coluna | Significado |
|---|---|
| `planet_slug` | Identificador seguro usado no datalake |
| `source_name` | Fonte registrada no manifesto RAW |
| `source_raw_path` | Caminho do arquivo RAW usado |
| `source_raw_sha256` | Checksum do arquivo RAW |
| `source_raw_file_name` | Nome do arquivo RAW |
| `silver_created_at_utc` | Momento UTC de criação da linha Silver |

## `ps_all_solutions.csv`

Tabela com todas as linhas da tabela NASA `ps` para os planetas configurados.

Resultado final:

| Métrica | Valor |
|---|---:|
| Linhas | 167 |
| Colunas | 37 |

### Linhas por planeta

| Planeta | Linhas `ps` |
|---|---:|
| HAT-P-7 b | 24 |
| TrES-2 b | 34 |
| HD 189733 b | 21 |
| HD 209458 b | 23 |
| WASP-12 b | 19 |
| WASP-10 b | 11 |
| WASP-4 b | 22 |
| HAT-P-32 b | 13 |

### Decisão metodológica

Nenhuma linha foi escolhida como "melhor solução".

A Silver apenas consolidou todas as soluções catalográficas disponíveis, adicionando:

- `planet_name`;
- `host_star`;
- `planet_slug`;
- `solution_row_index`;
- proveniência RAW;
- timestamp de criação Silver.

A escolha de uma solução para modelagem ou comparação científica deve ocorrer em etapa posterior.

## `all_transiting_planets_snapshot.csv`

Snapshot geral da NASA para planetas em trânsito.

Resultado final:

| Métrica | Valor |
|---|---:|
| Linhas | 4.653 |
| Colunas | 31 |

### Uso pretendido

Essa tabela serve para:

- contextualizar o universo de planetas em trânsito;
- comparar disponibilidade catalográfica;
- apoiar exploração posterior.

Ela não foi transformada em dataset Gold e não define o planeta final do estudo.

## Exo.MAST

### Entradas RAW

Arquivos possíveis por planeta:

```text
data/raw/exomast/{planet_slug}/identifiers.json
data/raw/exomast/{planet_slug}/properties.json
data/raw/exomast/{planet_slug}/kepler_tces.json
data/raw/exomast/{planet_slug}/tess_tces.json
```

### Saídas Silver

```text
data/silver/catalogs/exomast/exomast_identifiers.csv
data/silver/catalogs/exomast/exomast_properties.csv
data/silver/catalogs/exomast/exomast_tces.csv
```

## Estratégia de flattening

Os JSONs Exo.MAST podem variar de estrutura.

A Silver adotou uma estratégia robusta:

1. Se o JSON é lista, cada elemento vira uma linha.
2. Se o JSON é dicionário com chave `TCE`, a lista `TCE` vira tabela.
3. Se o JSON é dicionário com `results` ou `data`, essa lista é expandida.
4. Se o JSON é dicionário simples, o dicionário vira uma linha.
5. Colunas complexas ainda aninhadas são serializadas como JSON compacto.
6. O conteúdo original compacto é preservado em `raw_metadata_json`.

## Tabelas Exo.MAST criadas

| Tabela | Linhas | Colunas | Conteúdo |
|---|---:|---:|---|
| `exomast_identifiers.csv` | 8 | 20 | Identificadores por planeta |
| `exomast_properties.csv` | 34 | 183 | Propriedades retornadas pelo portal |
| `exomast_tces.csv` | 10 | 12 | TCEs Kepler/TESS |

## Cobertura Exo.MAST por planeta

| Planeta | JSONs Exo.MAST |
|---|---:|
| HAT-P-7 b | 4 |
| TrES-2 b | 4 |
| HD 189733 b | 3 |
| HD 209458 b | 3 |
| WASP-12 b | 3 |
| WASP-10 b | 3 |
| WASP-4 b | 3 |
| HAT-P-32 b | 3 |

HAT-P-7 b e TrES-2 b possuem JSONs de TCEs Kepler e TESS. Os demais possuem TESS, mas não apresentaram `kepler_tces.json` na RAW.

## Campos obrigatórios Exo.MAST

Cada tabela Exo.MAST Silver preserva:

| Campo | Significado |
|---|---|
| `planet_name` | Nome do planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug usado no datalake |
| `exomast_file_type` | Tipo de JSON de origem |
| `source_name` | Fonte |
| `source_raw_path` | Caminho RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Arquivo RAW |
| `raw_metadata_json` | JSON original compacto |
| `silver_created_at_utc` | Momento de criação |

## Limitações

- A Silver não interpreta fisicamente TCEs.
- A Silver não cruza TCEs com trânsitos individuais.
- A Silver não resolve conflitos entre NASA e Exo.MAST.
- A Silver não usa Exo.MAST para baixar FITS.
- A Silver não escolhe missões ou setores para Gold.

## Uso futuro

Essas tabelas podem apoiar:

- identificação cruzada de alvos;
- conferência de propriedades do sistema;
- seleção preliminar de missões;
- descrição de rastreabilidade na metodologia;
- comparação entre catálogos antes da modelagem.
