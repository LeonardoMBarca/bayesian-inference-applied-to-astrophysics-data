# 01. Mapa do Pipeline e do Código

## Visão geral

O pipeline foi implementado em Python com uma arquitetura simples:

- scripts em `scripts/` para execução direta;
- módulos reutilizáveis em `src/raw_ingestion/`;
- configuração central em `scripts/raw_data_config.py`;
- dados salvos em `data/raw`;
- documentação operacional em `README.md` e nesta pasta `docs/`.

O comando principal é:

```bash
python scripts/download_raw_data.py
```

No ambiente local usado durante a validação:

```bash
.venv/bin/python scripts/download_raw_data.py
```

## Scripts de entrada

### `scripts/download_raw_data.py`

Executa todas as fontes:

```python
run_pipeline(config, ("nasa", "mast", "exomast", "etd"))
```

Fontes acionadas:

1. NASA Exoplanet Archive
2. MAST / Lightkurve
3. Exo.MAST
4. ETD / VarAstro

### `scripts/download_nasa_exoplanet_archive.py`

Executa apenas:

```python
run_pipeline(config, ("nasa",))
```

É usado para baixar:

- tabelas por planeta em `pscomppars`;
- tabelas por planeta em `ps`;
- snapshot geral de planetas em trânsito.

### `scripts/download_mast_lightcurves.py`

Executa:

```python
run_pipeline(config, ("mast", "exomast"))
```

Ou seja:

- MAST via Lightkurve;
- fallback Astroquery, se necessário;
- Exo.MAST para metadados auxiliares.

### `scripts/download_etd_varastro.py`

Executa apenas:

```python
run_pipeline(config, ("etd",))
```

É usado para:

- salvar HTML público do VarAstro;
- consultar endpoints públicos anônimos;
- extrair metadados de observações;
- baixar até cinco curvas JSON públicas por planeta.

## Configuração central

Arquivo:

```text
scripts/raw_data_config.py
```

Responsabilidades:

- lista de planetas;
- estrela hospedeira por planeta;
- prioridade de execução;
- missões preferidas;
- limites de download;
- URLs das fontes;
- timeout HTTP;
- delay para ETD;
- User-Agent;
- colunas desejadas do NASA Exoplanet Archive.

Configurações principais:

```text
PREFERRED_MISSIONS = ("Kepler", "K2", "TESS")
MAX_LIGHTCURVES_PER_MISSION = 3
MAX_ASTROQUERY_PRODUCTS_PER_MISSION = 3
MAX_ETD_LIGHTCURVES_PER_PLANET = 5
REQUEST_TIMEOUT_SECONDS = 60
ETD_REQUEST_DELAY_SECONDS = 2.0
```

## Módulos em `src/raw_ingestion`

### `src/raw_ingestion/pipeline.py`

Orquestra a execução.

Responsabilidades:

- criar diretórios RAW;
- configurar logging;
- criar sessão HTTP com retry;
- carregar manifesto global;
- executar cada coletor;
- capturar falhas no nível da fonte;
- salvar manifesto após cada fonte;
- fechar a sessão HTTP.

Coletores registrados:

```python
COLLECTORS = {
    "nasa": collect_nasa_exoplanet_archive,
    "mast": collect_mast_lightcurves,
    "exomast": collect_exomast,
    "etd": collect_etd_varastro,
}
```

### `src/raw_ingestion/utils.py`

Contém utilitários compartilhados.

Responsabilidades:

- criação das pastas RAW;
- criação de sessão HTTP com retry;
- logging;
- slug seguro para nomes de pasta;
- escrita atômica;
- política de não sobrescrita;
- cálculo de SHA256;
- geração de CSV em memória;
- registro no manifesto global;
- versionamento de sidecars por hash.

Funções e classes principais:

```text
ensure_raw_directories
setup_logging
build_http_session
sha256_file
safe_slug
atomic_write_bytes
atomic_write_text
atomic_write_json
versioned_path
RawDataManifest
save_artifact
register_error
```

### `src/raw_ingestion/nasa_exoplanet_archive.py`

Coletor do NASA Exoplanet Archive.

Responsabilidades:

- consultar esquema TAP;
- selecionar dinamicamente colunas existentes;
- consultar `pscomppars`;
- consultar `ps`;
- salvar `response.csv`, `query.sql`, `metadata.json`;
- salvar snapshot geral de planetas em trânsito;
- registrar erros sem derrubar o pipeline.

### `src/raw_ingestion/mast.py`

Coletor MAST.

Responsabilidades:

- usar `lightkurve.search_lightcurve`;
- buscar por estrela hospedeira;
- executar buscas por missão: Kepler, K2 e TESS;
- salvar tabelas de busca;
- selecionar no máximo três produtos por planeta/missão;
- baixar FITS originais via Lightkurve;
- gerar manifestos por planeta/missão;
- usar Astroquery como fallback se Lightkurve falhar.

### `src/raw_ingestion/exomast.py`

Coletor Exo.MAST.

Responsabilidades:

- consultar identificadores;
- consultar propriedades;
- consultar TCEs Kepler/TESS quando houver identificador;
- salvar JSONs sem alteração;
- registrar notas por planeta.

### `src/raw_ingestion/etd.py`

Coletor ETD/VarAstro.

Responsabilidades:

- consultar página pública do catálogo;
- salvar HTML de busca;
- usar o endpoint público anônimo usado pelo próprio DataTable do site;
- salvar JSON de busca;
- salvar página pública de detalhe do planeta;
- consultar o endpoint público de observações;
- verificar que não há registros marcados como privados;
- salvar observações brutas em JSON;
- extrair metadados tabulares em CSV;
- baixar até cinco curvas JSON públicas por planeta;
- respeitar delay entre requisições.

## Fluxo resumido de execução

```text
download_raw_data.py
  -> run_pipeline
    -> ensure_raw_directories
    -> setup_logging
    -> RawDataManifest
    -> collect_nasa_exoplanet_archive
    -> collect_mast_lightcurves
    -> collect_exomast
    -> collect_etd_varastro
    -> manifest.flush
```

## Tratamento de erros

O pipeline foi desenhado para não parar por falhas pontuais.

Exemplos de falhas tratadas:

- DNS indisponível;
- endpoint retornando HTML em vez de CSV;
- biblioteca opcional ausente;
- produto MAST sem caminho local;
- endpoint ETD sem curva direta;
- erro por planeta;
- erro por missão.

Quando ocorre erro:

1. o erro é registrado no log;
2. uma linha `failed` é adicionada ao manifesto;
3. o pipeline continua para o próximo planeta, missão ou fonte.

