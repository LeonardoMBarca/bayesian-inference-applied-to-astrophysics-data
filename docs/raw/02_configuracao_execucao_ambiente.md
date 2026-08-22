# 02. Configuração, Execução e Ambiente

## Arquivo de dependências

As dependências foram declaradas em:

```text
requirements.txt
```

Conteúdo:

```text
pandas>=2.2
requests>=2.31
astropy>=6.0
astroquery>=0.4.7
lightkurve>=2.5
beautifulsoup4>=4.12
lxml>=5.0
tqdm>=4.66
```

## Ambiente usado na validação

O ambiente local validado usou:

```text
Python 3.12.3
```

O ambiente virtual ficou em:

```text
.venv/
```

Observação: o sistema não tinha `ensurepip` disponível inicialmente. Por isso, durante a validação local, o `pip` foi instalado no `.venv` usando a instalação Conda local como bootstrap. Depois disso, o próprio `.venv/bin/python -m pip` passou a funcionar.

## Instalação recomendada

Fluxo padrão:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Fluxo alternativo com Conda:

```bash
conda create --prefix .venv python=3.12 pip
conda activate ./.venv
python -m pip install -r requirements.txt
```

## Comando principal

Executa todas as coletas:

```bash
python scripts/download_raw_data.py
```

No ambiente validado:

```bash
.venv/bin/python scripts/download_raw_data.py
```

## Comandos separados

NASA Exoplanet Archive:

```bash
python scripts/download_nasa_exoplanet_archive.py
```

MAST/Lightkurve e Exo.MAST:

```bash
python scripts/download_mast_lightcurves.py
```

ETD/VarAstro:

```bash
python scripts/download_etd_varastro.py
```

## Configurações dos planetas

Os planetas foram definidos em `scripts/raw_data_config.py`.

```python
PLANETS = [
    {"planet_name": "HAT-P-7 b", "host_star": "HAT-P-7", "priority": 1},
    {"planet_name": "TrES-2 b", "host_star": "TrES-2", "priority": 2},
    {"planet_name": "HD 189733 b", "host_star": "HD 189733", "priority": 3},
    {"planet_name": "HD 209458 b", "host_star": "HD 209458", "priority": 4},
    {"planet_name": "WASP-12 b", "host_star": "WASP-12", "priority": 5},
    {"planet_name": "WASP-10 b", "host_star": "WASP-10", "priority": 6},
    {"planet_name": "WASP-4 b", "host_star": "WASP-4", "priority": 7},
    {"planet_name": "HAT-P-32 b", "host_star": "HAT-P-32", "priority": 8},
]
```

## Configurações de limites

Foram aplicados limites para evitar volumes desnecessários.

```python
MAX_LIGHTCURVES_PER_MISSION = 3
MAX_ASTROQUERY_PRODUCTS_PER_MISSION = 3
MAX_ETD_LIGHTCURVES_PER_PLANET = 5
```

Interpretação:

- até três FITS por planeta e missão no MAST;
- até três produtos por missão no fallback Astroquery;
- até cinco curvas JSON públicas por planeta no ETD/VarAstro.

## Configurações de rede

```python
REQUEST_TIMEOUT_SECONDS = 60
ETD_REQUEST_DELAY_SECONDS = 2.0
HTTP_RETRY_COUNT = 3
HTTP_BACKOFF_FACTOR = 1.0
```

Interpretação:

- timeout de 60 segundos por requisição;
- retry para erros transitórios HTTP;
- delay de 2 segundos entre requisições ETD/VarAstro;
- User-Agent acadêmico explícito.

## User-Agent

O User-Agent configurado foi:

```text
MBA-TCC-Raw-Astronomy-Ingestion/1.0 (Leonardo Moraes Barca; academic research; public data only)
```

Esse User-Agent deixa claro:

- finalidade acadêmica;
- coleta de dados públicos;
- identificação do pipeline.

## Diretório base da coleta

O diretório base foi:

```python
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
```

Ou seja:

```text
data/raw/
```

## Observação sobre rede e sandbox

Durante a validação, uma primeira execução isolada da NASA falhou por bloqueio de DNS no sandbox. Essa falha foi registrada corretamente no manifesto e no log. Em seguida, a coleta foi repetida com acesso de rede autorizado e os CSVs foram baixados com sucesso.

Isso é metodologicamente útil porque prova que:

- erros não derrubam o pipeline;
- falhas ficam documentadas;
- a reexecução é possível;
- os arquivos já baixados são preservados.

