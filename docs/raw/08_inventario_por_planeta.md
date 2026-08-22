# 08. Inventário por Planeta

## Objetivo deste inventário

Este documento consolida o que foi coletado para cada planeta candidato.

Ele responde:

- quais arquivos existem;
- quais fontes retornaram dados;
- quantos produtos foram encontrados;
- quantos FITS foram baixados;
- quantas observações ETD públicas foram registradas;
- onde procurar cada tipo de informação.

## Resumo geral

| Planeta | NASA `pscomppars` | NASA `ps` linhas | MAST FITS | Exo.MAST JSONs | ETD observações | ETD curvas JSON |
|---|---:|---:|---:|---:|---:|---:|
| HAT-P-7 b | 1 | 24 | 6 | 4 | 60 | 5 |
| TrES-2 b | 1 | 34 | 6 | 4 | 371 | 5 |
| HD 189733 b | 1 | 21 | 3 | 3 | 218 | 5 |
| HD 209458 b | 1 | 23 | 3 | 3 | 92 | 5 |
| WASP-12 b | 1 | 19 | 3 | 3 | 376 | 5 |
| WASP-10 b | 1 | 11 | 3 | 3 | 241 | 5 |
| WASP-4 b | 1 | 22 | 3 | 3 | 80 | 5 |
| HAT-P-32 b | 1 | 13 | 3 | 3 | 212 | 5 |

## HAT-P-7 b

Slug:

```text
hat_p_7_b
```

Estrela hospedeira:

```text
HAT-P-7
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_7_b/response.csv
data/raw/nasa_exoplanet_archive/ps/hat_p_7_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 24 linhas.

### MAST/Lightkurve

```text
data/raw/mast/lightkurve/hat_p_7_b/kepler/
data/raw/mast/lightkurve/hat_p_7_b/k2/
data/raw/mast/lightkurve/hat_p_7_b/tess/
```

Resultados de busca:

- Kepler: 69 linhas;
- K2: 0 linhas;
- TESS: 48 linhas.

FITS baixados:

- Kepler: 3;
- TESS: 3;
- total: 6.

### Exo.MAST

```text
data/raw/exomast/hat_p_7_b/
```

Arquivos:

```text
identifiers.json
properties.json
kepler_tces.json
tess_tces.json
notes.md
```

### ETD/VarAstro

```text
data/raw/etd_varastro/html_snapshots/hat_p_7_b/
data/raw/etd_varastro/extracted_metadata/hat_p_7_b/
data/raw/etd_varastro/downloaded_lightcurves/hat_p_7_b/
```

Resultados:

- observações públicas: 60;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_94348_transit_12787.json
02_observation_93941_transit_12377.json
03_observation_93940_transit_12376.json
04_observation_106903_transit_20350.json
05_observation_107381_transit_20679.json
```

## TrES-2 b

Slug:

```text
tres_2_b
```

Estrela hospedeira:

```text
TrES-2
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/tres_2_b/response.csv
data/raw/nasa_exoplanet_archive/ps/tres_2_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 34 linhas.

### MAST/Lightkurve

```text
data/raw/mast/lightkurve/tres_2_b/kepler/
data/raw/mast/lightkurve/tres_2_b/k2/
data/raw/mast/lightkurve/tres_2_b/tess/
```

Resultados de busca:

- Kepler: 54 linhas;
- K2: 0 linhas;
- TESS: 49 linhas.

FITS baixados:

- Kepler: 3;
- TESS: 3;
- total: 6.

### Exo.MAST

```text
data/raw/exomast/tres_2_b/
```

Arquivos:

```text
identifiers.json
properties.json
kepler_tces.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 371;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_109868_transit_21839.json
02_observation_109743_transit_21790.json
03_observation_109559_transit_21795.json
04_observation_98495_transit_20194.json
05_observation_94271_transit_12710.json
```

## HD 189733 b

Slug:

```text
hd_189733_b
```

Estrela hospedeira:

```text
HD 189733
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/hd_189733_b/response.csv
data/raw/nasa_exoplanet_archive/ps/hd_189733_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 21 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 14 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/hd_189733_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 218;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_110560_transit_22197.json
02_observation_110000_transit_21914.json
03_observation_110069_transit_21925.json
04_observation_109228_transit_21560.json
05_observation_94274_transit_12713.json
```

## HD 209458 b

Slug:

```text
hd_209458_b
```

Estrela hospedeira:

```text
HD 209458
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/hd_209458_b/response.csv
data/raw/nasa_exoplanet_archive/ps/hd_209458_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 23 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 8 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/hd_209458_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 92;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_110656_transit_22235.json
02_observation_94180_transit_12619.json
03_observation_93797_transit_12233.json
04_observation_92401_transit_10826.json
05_observation_93014_transit_11445.json
```

## WASP-12 b

Slug:

```text
wasp_12_b
```

Estrela hospedeira:

```text
WASP-12
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/wasp_12_b/response.csv
data/raw/nasa_exoplanet_archive/ps/wasp_12_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 19 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 26 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/wasp_12_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 376;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_112362_transit_23075.json
02_observation_112218_transit_23028.json
03_observation_112163_transit_23006.json
04_observation_111853_transit_22830.json
05_observation_111766_transit_22790.json
```

## WASP-10 b

Slug:

```text
wasp_10_b
```

Estrela hospedeira:

```text
WASP-10
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/wasp_10_b/response.csv
data/raw/nasa_exoplanet_archive/ps/wasp_10_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 11 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 7 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/wasp_10_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 241;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_111532_transit_22675.json
02_observation_110182_transit_21989.json
03_observation_107114_transit_20495.json
04_observation_98654_transit_20318.json
05_observation_98657_transit_20311.json
```

## WASP-4 b

Slug:

```text
wasp_4_b
```

Estrela hospedeira:

```text
WASP-4
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/wasp_4_b/response.csv
data/raw/nasa_exoplanet_archive/ps/wasp_4_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 22 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 29 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/wasp_4_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 80;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_106863_transit_20322.json
02_observation_111591_transit_22705.json
03_observation_94145_transit_12583.json
04_observation_92847_transit_11278.json
05_observation_92260_transit_10684.json
```

## HAT-P-32 b

Slug:

```text
hat_p_32_b
```

Estrela hospedeira:

```text
HAT-P-32
```

### NASA

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_32_b/response.csv
data/raw/nasa_exoplanet_archive/ps/hat_p_32_b/response.csv
```

Resultados:

- `pscomppars`: 1 linha;
- `ps`: 13 linhas.

### MAST/Lightkurve

Resultados de busca:

- Kepler: 0 linhas;
- K2: 0 linhas;
- TESS: 9 linhas.

FITS baixados:

- TESS: 3.

### Exo.MAST

```text
data/raw/exomast/hat_p_32_b/
```

Arquivos:

```text
identifiers.json
properties.json
tess_tces.json
notes.md
```

### ETD/VarAstro

Resultados:

- observações públicas: 212;
- registros privados retornados: 0;
- curvas JSON públicas salvas: 5.

Arquivos de curva:

```text
01_observation_111341_transit_22572.json
02_observation_111051_transit_22462.json
03_observation_110849_transit_22316.json
04_observation_107460_transit_20719.json
05_observation_107204_transit_20550.json
```

## Arquivos manuais antigos removidos

Antes da estrutura nova, existiam três CSVs soltos em `data/raw`.

Eles foram removidos durante revisão posterior porque não faziam parte do pipeline rastreável:

- não estavam no manifesto RAW;
- não eram usados pelas camadas Silver ou Gold;
- não seguiam a organização por fonte;
- foram baixados manualmente antes da definição do fluxo atual.

Interpretação:

- o inventário por planeta deve considerar as subpastas estruturadas;
- o manifesto RAW permanece a fonte primária de rastreabilidade;
- a limpeza não removeu nenhum arquivo registrado no manifesto.

## Resumo de disponibilidade

Nenhum dos oito planetas ficou sem dados de uma fonte inteira.

Resumo:

- NASA: todos têm `pscomppars` e `ps`;
- MAST: todos têm pelo menos TESS ou Kepler/TESS;
- Exo.MAST: todos têm metadados;
- ETD/VarAstro: todos têm observações públicas e cinco curvas JSON.

Lacunas por missão MAST:

- K2: nenhum produto retornado;
- Kepler: somente HAT-P-7 b e TrES-2 b retornaram produtos;
- TESS: todos retornaram produtos.
