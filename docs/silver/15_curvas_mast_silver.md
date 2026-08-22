# 15. Curvas de Luz MAST na Camada Silver

## Objetivo deste documento

Este documento descreve como os arquivos FITS baixados do MAST/Lightkurve na RAW foram lidos e transformados em tabelas CSV na Silver.

Fonte:

```text
MAST / Lightkurve
```

Entradas RAW:

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/mastDownload/
```

Saídas Silver:

```text
data/silver/lightcurves/mast/{planet_slug}/{mission}_lightcurve.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
```

## Princípio da extração

A Silver abriu os arquivos FITS e extraiu a tabela de curva de luz.

Não foram feitos:

- normalização;
- filtragem por qualidade;
- remoção de NaN;
- remoção de outliers;
- conversão de tempo para fase orbital;
- combinação analítica de missões;
- seleção de trânsito;
- modelagem.

Os valores foram apenas lidos, padronizados em colunas e gravados em CSV.

## Biblioteca usada

Foi usada:

```python
astropy.io.fits
```

A escolha é adequada porque:

- FITS é formato astronômico nativo;
- `astropy` preserva acesso a HDUs, headers e tabelas;
- permite extrair metadados sem alterar o arquivo original.

## Identificação da HDU tabular

Para cada FITS:

1. Abre o arquivo com `fits.open`.
2. Percorre HDUs.
3. Procura uma `BinTableHDU`.
4. Dá preferência a HDU com `TIME` e alguma coluna de fluxo.
5. Usa a primeira tabela compatível.
6. Registra `hdu_index` e `hdu_name`.

## Colunas preferidas

Foram procuradas:

| Coluna FITS | Uso na Silver |
|---|---|
| `TIME` | Tempo da observação |
| `SAP_FLUX` | Fluxo SAP |
| `SAP_FLUX_ERR` | Erro do fluxo SAP |
| `PDCSAP_FLUX` | Fluxo corrigido pelo pipeline |
| `PDCSAP_FLUX_ERR` | Erro do fluxo corrigido |
| `QUALITY` | Flag de qualidade TESS |
| `SAP_QUALITY` | Flag de qualidade Kepler |
| `CADENCENO` | Número da cadência |
| `MOM_CENTR1` | Centroide |
| `MOM_CENTR2` | Centroide |
| `POS_CORR1` | Correção de posição |
| `POS_CORR2` | Correção de posição |

## Tratamento de `QUALITY` e `SAP_QUALITY`

Foi observado que:

- FITS TESS usam `QUALITY`;
- FITS Kepler usam `SAP_QUALITY`.

A Silver usa:

1. `QUALITY`, quando existe;
2. `SAP_QUALITY`, como fallback;
3. valor ausente, caso nenhuma exista.

Esse valor padronizado é gravado em:

```text
quality
```

Além disso, são criadas:

| Coluna | Significado |
|---|---|
| `quality_is_zero` | `quality == 0` |
| `quality_is_missing` | qualidade ausente |
| `has_pdcsap_flux` | linha possui `PDCSAP_FLUX` |
| `has_sap_flux` | linha possui `SAP_FLUX` |

Importante: essas colunas são auxiliares. Nenhuma linha foi removida.

## Metadados extraídos do header

Quando disponíveis, foram extraídos:

| Header FITS | Coluna Silver |
|---|---|
| `TELESCOP` | `telescope` |
| `INSTRUME` | `instrument` |
| `OBJECT` | `object` |
| `QUARTER` | `quarter` |
| `SECTOR` | `sector` |
| `CAMPAIGN` | `campaign` |
| `CAMERA` | `camera` |
| `CCD` | `ccd` |
| `BJDREFI` | `time_reference` |
| `BJDREFF` | `time_reference` |
| `TIMEUNIT` | `time_unit` |
| `TIMESYS` | `time_reference` |
| `TSTART` | metadata FITS |
| `TSTOP` | metadata FITS |
| `DATE-OBS` | metadata FITS |
| `DATE-END` | metadata FITS |
| `AUTHOR` / `CREATOR` | `data_origin` |

## Arquivos de curva criados

Foram criados 10 CSVs de curva:

```text
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/hat_p_7_b/tess_lightcurve.csv
data/silver/lightcurves/mast/tres_2_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/tres_2_b/tess_lightcurve.csv
data/silver/lightcurves/mast/hd_189733_b/tess_lightcurve.csv
data/silver/lightcurves/mast/hd_209458_b/tess_lightcurve.csv
data/silver/lightcurves/mast/wasp_12_b/tess_lightcurve.csv
data/silver/lightcurves/mast/wasp_10_b/tess_lightcurve.csv
data/silver/lightcurves/mast/wasp_4_b/tess_lightcurve.csv
data/silver/lightcurves/mast/hat_p_32_b/tess_lightcurve.csv
```

## Cobertura por planeta

| Planeta | FITS | Linhas de curva | Missões disponíveis |
|---|---:|---:|---|
| HAT-P-7 b | 6 | 64.872 | Kepler, TESS |
| TrES-2 b | 6 | 63.836 | Kepler, TESS |
| HD 189733 b | 3 | 57.213 | TESS |
| HD 209458 b | 3 | 159.179 | TESS |
| WASP-12 b | 3 | 54.224 | TESS |
| WASP-10 b | 3 | 145.851 | TESS |
| WASP-4 b | 3 | 56.783 | TESS |
| HAT-P-32 b | 3 | 140.907 | TESS |

## Resumo de qualidade por planeta e missão

| Planeta | Missão | FITS | Linhas | `quality == 0` | `quality != 0` | Qualidade ausente |
|---|---|---:|---:|---:|---:|---:|
| HAT-P-7 b | Kepler | 3 | 6.469 | 3.909 | 2.560 | 0 |
| HAT-P-7 b | TESS | 3 | 58.403 | 50.166 | 8.237 | 0 |
| TrES-2 b | Kepler | 3 | 6.469 | 5.358 | 1.111 | 0 |
| TrES-2 b | TESS | 3 | 57.367 | 53.458 | 3.909 | 0 |
| HD 189733 b | TESS | 3 | 57.213 | 50.529 | 6.684 | 0 |
| HD 209458 b | TESS | 3 | 159.179 | 150.556 | 8.623 | 0 |
| WASP-12 b | TESS | 3 | 54.224 | 47.909 | 6.315 | 0 |
| WASP-10 b | TESS | 3 | 145.851 | 139.812 | 6.039 | 0 |
| WASP-4 b | TESS | 3 | 56.783 | 47.763 | 9.020 | 0 |
| HAT-P-32 b | TESS | 3 | 140.907 | 134.444 | 6.463 | 0 |

## Colunas FITS encontradas com maior frequência

As seguintes colunas apareceram nos 30 FITS:

- `TIME`;
- `TIMECORR`;
- `CADENCENO`;
- `SAP_FLUX`;
- `SAP_FLUX_ERR`;
- `SAP_BKG`;
- `SAP_BKG_ERR`;
- `PDCSAP_FLUX`;
- `PDCSAP_FLUX_ERR`;
- `PSF_CENTR1`;
- `PSF_CENTR1_ERR`;
- `PSF_CENTR2`;
- `PSF_CENTR2_ERR`;
- `MOM_CENTR1`;
- `MOM_CENTR1_ERR`;
- `MOM_CENTR2`;
- `MOM_CENTR2_ERR`;
- `POS_CORR1`;
- `POS_CORR2`.

## Colunas preferidas ausentes

Ausências observadas:

| Coluna | Ausência |
|---|---:|
| `SAP_QUALITY` | 24 FITS |
| `QUALITY` | 6 FITS |

Interpretação:

- os 24 FITS sem `SAP_QUALITY` são produtos TESS;
- os 6 FITS sem `QUALITY` são produtos Kepler;
- o fallback implementado preserva a flag de qualidade em ambos os casos.

## Tabela `mast_fits_metadata.csv`

Caminho:

```text
data/silver/lightcurves/mast/mast_fits_metadata.csv
```

Linhas:

```text
30
```

Uma linha por FITS.

Campos principais:

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `mission` | Kepler ou TESS |
| `source_fits_file` | Nome do FITS |
| `source_raw_path` | Caminho RAW |
| `sha256` | Checksum do FITS |
| `hdu_count` | Número de HDUs |
| `extracted_rows` | Linhas extraídas |
| `available_columns` | Colunas encontradas |
| `missing_preferred_columns` | Colunas preferidas ausentes |
| `time_min` | Menor tempo |
| `time_max` | Maior tempo |
| `quality_zero_count` | Linhas com qualidade zero |
| `quality_nonzero_count` | Linhas com qualidade não zero |
| `has_pdcsap_flux` | Presença de `PDCSAP_FLUX` |
| `has_sap_flux` | Presença de `SAP_FLUX` |
| `status` | Resultado da extração |
| `error_message` | Erro, se houver |

## Limitações

- CSVs de curva são maiores que os FITS por serem tabulares em texto.
- Não há compactação automática dos CSVs Silver.
- Não foi feita seleção de cadência.
- Não foi feita seleção de setores, quarters ou janelas de trânsito.
- Não foi feita avaliação científica da qualidade dos pontos.
- A presença de `quality == 0` não significa que a curva já está pronta para Gold.

## Uso futuro

As tabelas MAST Silver permitem:

- inspecionar disponibilidade de dados por planeta;
- comparar Kepler e TESS;
- escolher candidato Gold;
- avaliar quantidade de pontos com flags;
- preparar etapa futura de filtragem, normalização e faseamento;
- rastrear cada ponto até o FITS original.
