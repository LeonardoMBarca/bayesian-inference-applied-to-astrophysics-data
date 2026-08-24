# 13. Mapa do Pipeline Silver e Código

## Objetivo deste documento

Este documento explica como a camada Silver foi implementada em código.

Ele descreve:

- scripts executáveis;
- módulo de configuração;
- pacote `src/silver_processing`;
- fluxo de execução;
- responsabilidades de cada arquivo;
- relação entre entradas RAW e saídas Silver.

## Visão geral do fluxo

O pipeline Silver segue esta sequência lógica:

1. Criar diretórios em `data/silver/`.
2. Ler `data/raw/_manifests/raw_data_manifest.csv`.
3. Validar existência e checksums dos arquivos RAW registrados.
4. Consolidar catálogos NASA.
5. Consolidar JSONs Exo.MAST.
6. Ler FITS MAST e extrair curvas tabulares.
7. Consolidar observações e pontos fotométricos ETD.
8. Gerar validações Silver.
9. Gerar manifesto Silver.
10. Gerar log Silver.
11. Gerar documentação técnica Silver.

## Scripts criados

### `scripts/build_silver_data.py`

Comando principal da Silver.

Executa todas as etapas:

```text
raw_validation
catalogs
lightcurves
etd
silver_validation
docs
```

Comando:

```bash
python scripts/build_silver_data.py
```

### `scripts/build_silver_catalogs.py`

Executa somente as partes catalográficas:

- validação inicial do manifesto RAW;
- NASA;
- Exo.MAST;
- validações Silver;
- documentação Silver.

Comando:

```bash
python scripts/build_silver_catalogs.py
```

### `scripts/build_silver_lightcurves.py`

Executa a parte de curvas espaciais:

- validação inicial do manifesto RAW;
- leitura dos FITS MAST;
- extração de tabelas por planeta e missão;
- metadados FITS;
- validações Silver;
- documentação Silver.

Comando:

```bash
python scripts/build_silver_lightcurves.py
```

### `scripts/build_silver_etd.py`

Executa a parte ETD:

- validação inicial do manifesto RAW;
- observações públicas;
- pontos fotométricos;
- metadados dos JSONs de curva;
- validações Silver;
- documentação Silver.

Comando:

```bash
python scripts/build_silver_etd.py
```

## Configuração

Arquivo:

```text
src/silver_processing/config.py
```

`scripts/silver_data_config.py` permanece como import de compatibilidade.

Responsabilidades:

- definir `PROJECT_ROOT`;
- definir `RAW_DATA_DIR`;
- definir `SILVER_DATA_DIR`;
- definir `RAW_MANIFEST_PATH`;
- listar planetas;
- listar slugs;
- listar estrelas hospedeiras;
- definir missões esperadas;
- definir colunas preferidas dos FITS;
- definir colunas finais das curvas MAST;
- documentar estratégia de flags de qualidade;
- documentar estratégia de metadados de tempo;
- controlar modo strict ou non-strict.

## Pacote Silver

Diretório:

```text
src/silver_processing/
```

Arquivos:

| Arquivo | Responsabilidade |
|---|---|
| `__init__.py` | Marca o pacote Python |
| `config.py` | Configuração canônica da camada Silver |
| `utils.py` | Funções comuns: paths, logging, SHA256, escrita atômica |
| `manifests.py` | Escrita do manifesto Silver |
| `validation.py` | Validação RAW e validações Silver |
| `catalogs_nasa.py` | Consolidação NASA `pscomppars`, `ps` e snapshot |
| `catalogs_exomast.py` | Flattening robusto dos JSONs Exo.MAST |
| `lightcurves_mast.py` | Leitura dos FITS e extração de curvas |
| `lightcurves_etd.py` | Consolidação ETD |
| `pipeline.py` | Orquestração do pipeline completo |

## Módulo `utils.py`

Principais funções:

| Função | Uso |
|---|---|
| `utc_now()` | Gera timestamp UTC padronizado |
| `ensure_silver_directories()` | Cria a estrutura de pastas Silver |
| `setup_logging()` | Configura log em arquivo e console |
| `sha256_file()` | Calcula checksum SHA256 |
| `relative_path()` | Gera caminho relativo ao projeto |
| `atomic_write_dataframe()` | Escreve CSV de forma atômica |
| `atomic_write_json()` | Escreve JSON de forma atômica |
| `read_raw_manifest()` | Lê o manifesto RAW |
| `raw_manifest_lookup()` | Cria índice por `local_path` |
| `get_raw_info()` | Recupera proveniência de arquivo RAW |
| `compact_json()` | Serializa JSON compacto |
| `serialize_complex_columns()` | Converte dict/list em string JSON |

## Escrita atômica

As saídas Silver são escritas usando arquivos temporários `.part` e depois substituídas por `os.replace`.

Isso reduz risco de:

- CSV truncado;
- manifesto incompleto;
- arquivo parcialmente escrito;
- inconsistência em caso de interrupção.

## Módulo `manifests.py`

Classe principal:

```text
SilverManifest
```

Responsabilidades:

- acumular registros de artefatos gerados;
- registrar falhas por arquivo ou etapa;
- calcular checksum dos arquivos Silver;
- registrar tamanho dos arquivos;
- escrever CSV e JSON do manifesto.

Saídas:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

## Módulo `validation.py`

Tem duas responsabilidades:

1. Validar a RAW antes de processar.
2. Gerar relatórios de validação da Silver.

Arquivos criados:

```text
data/silver/validation/raw_manifest_summary.csv
data/silver/validation/raw_manifest_validation.json
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/validation/silver_etd_summary.csv
data/silver/validation/silver_column_presence_report.csv
```

## Módulo `catalogs_nasa.py`

Lê:

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/response.csv
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/response.csv
data/raw/nasa_exoplanet_archive/pscomppars/all_transiting_planets_snapshot.csv
```

Cria:

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/nasa/ps_all_solutions.csv
data/silver/catalogs/nasa/all_transiting_planets_snapshot.csv
```

## Módulo `catalogs_exomast.py`

Lê:

```text
data/raw/exomast/{planet_slug}/identifiers.json
data/raw/exomast/{planet_slug}/properties.json
data/raw/exomast/{planet_slug}/kepler_tces.json
data/raw/exomast/{planet_slug}/tess_tces.json
```

Cria:

```text
data/silver/catalogs/exomast/exomast_identifiers.csv
data/silver/catalogs/exomast/exomast_properties.csv
data/silver/catalogs/exomast/exomast_tces.csv
```

## Módulo `lightcurves_mast.py`

Lê FITS em:

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/mastDownload/
```

Cria:

```text
data/silver/lightcurves/mast/{planet_slug}/{mission}_lightcurve.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
```

## Módulo `lightcurves_etd.py`

Lê:

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_raw.json
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_api_*.csv
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/*.json
```

Cria:

```text
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_points.csv
data/silver/etd/etd_lightcurve_metadata.csv
```

## Módulo `pipeline.py`

Orquestra todo o fluxo.

Etapas disponíveis:

| Etapa | Descrição |
|---|---|
| `raw_validation` | Valida manifesto e arquivos RAW |
| `catalogs` | NASA e Exo.MAST |
| `lightcurves` | FITS MAST |
| `etd` | ETD / VarAstro |
| `silver_validation` | Relatórios Silver |
| `docs` | README técnico da Silver |

## Tratamento de erros

O pipeline não derruba a execução inteira por erro isolado.

Se um arquivo falhar:

- o erro é registrado no log;
- o erro é registrado no manifesto Silver com status `failed`;
- os próximos arquivos continuam sendo processados.

Na execução validada, todos os 26 registros finais do manifesto Silver ficaram com status `created`.

## Reexecução

A Silver é reexecutável.

Ao reexecutar:

- os arquivos Silver são recriados atomicamente;
- a RAW continua sem alteração;
- o manifesto Silver é regravado como visão da execução atual;
- os logs acumulam novas execuções.

Isso é adequado porque a Silver é uma camada derivada e pode ser reconstruída a partir da RAW.
