# Documentacao Completa RAW
Documento consolidado para uso como contexto em GPT.
- Gerado em UTC: `2026-06-16T15:47:14+00:00`
- Pasta de origem: `docs/raw`
- Observacao: este arquivo e apenas uma exportacao consolidada; os documentos originais nao foram removidos nem alterados.
- Uso sugerido: copiar este Markdown como contexto quando precisar discutir esta etapa especifica do TCC.

## Arquivos Incluidos
1. `docs/raw/README.md`
2. `docs/raw/00_contexto_escopo_e_regras_raw.md`
3. `docs/raw/01_mapa_do_pipeline_e_codigo.md`
4. `docs/raw/02_configuracao_execucao_ambiente.md`
5. `docs/raw/03_manifestos_logs_checksums_reexecucao.md`
6. `docs/raw/04_nasa_exoplanet_archive.md`
7. `docs/raw/05_mast_lightkurve_astroquery.md`
8. `docs/raw/06_exomast.md`
9. `docs/raw/07_etd_varastro.md`
10. `docs/raw/08_inventario_por_planeta.md`
11. `docs/raw/09_validacao_e_qualidade.md`
12. `docs/raw/10_como_usar_na_metodologia.md`
13. `docs/raw/11_dicionario_de_arquivos_e_campos.md`

---

# Arquivo 1: `docs/raw/README.md`

```text
Origem: docs/raw/README.md
```

# Documentação RAW

Esta pasta contém a documentação da camada **RAW** do datalake local.

A RAW é a camada de coleta e preservação dos dados públicos brutos. Ela guarda respostas e arquivos como foram obtidos das fontes, acompanhados de manifestos, logs e checksums.

## Escopo

A RAW cobre:

- NASA Exoplanet Archive;
- MAST / Lightkurve / Astroquery;
- Exo.MAST;
- ETD / VarAstro.

Ela não executa:

- limpeza;
- normalização;
- faseamento;
- remoção de outliers;
- modelagem;
- inferência bayesiana;
- criação de Silver ou Gold.

## Como ler

Os arquivos estão numerados em ordem sugerida:

1. [00_contexto_escopo_e_regras_raw.md](00_contexto_escopo_e_regras_raw.md)  
   Escopo, regras e limites da RAW.

2. [01_mapa_do_pipeline_e_codigo.md](01_mapa_do_pipeline_e_codigo.md)  
   Scripts, módulos e arquitetura do pipeline RAW.

3. [02_configuracao_execucao_ambiente.md](02_configuracao_execucao_ambiente.md)  
   Ambiente, dependências e comandos.

4. [03_manifestos_logs_checksums_reexecucao.md](03_manifestos_logs_checksums_reexecucao.md)  
   Manifestos, logs, checksums e reexecução.

5. [04_nasa_exoplanet_archive.md](04_nasa_exoplanet_archive.md)  
   Coleta NASA via TAP.

6. [05_mast_lightkurve_astroquery.md](05_mast_lightkurve_astroquery.md)  
   Busca e download de curvas MAST.

7. [06_exomast.md](06_exomast.md)  
   Metadados Exo.MAST.

8. [07_etd_varastro.md](07_etd_varastro.md)  
   Coleta ETD / VarAstro.

9. [08_inventario_por_planeta.md](08_inventario_por_planeta.md)  
   Inventário RAW por planeta.

10. [09_validacao_e_qualidade.md](09_validacao_e_qualidade.md)  
    Validação da coleta RAW.

11. [10_como_usar_na_metodologia.md](10_como_usar_na_metodologia.md)  
    Como aproveitar a RAW na metodologia.

12. [11_dicionario_de_arquivos_e_campos.md](11_dicionario_de_arquivos_e_campos.md)  
    Dicionário de arquivos e campos RAW.

## Saída principal documentada

```text
data/raw/
```

Manifesto global:

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```

---

# Arquivo 2: `docs/raw/00_contexto_escopo_e_regras_raw.md`

```text
Origem: docs/raw/00_contexto_escopo_e_regras_raw.md
```

# 00. Contexto, Escopo e Regras da Camada RAW

## Contexto acadêmico

O projeto de pesquisa se chama:

**Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional**

O objetivo geral do TCC é investigar como a inferência bayesiana pode ser aplicada à estimação de parâmetros físicos em sistemas astrofísicos sob incerteza observacional, com ênfase em curvas de luz de trânsitos de exoplanetas.

Esta etapa, porém, não implementa a inferência bayesiana. Ela prepara apenas a base bruta, rastreável e reproduzível de dados públicos.

## Objetivo desta etapa

O objetivo desta etapa foi criar uma camada RAW em um datalake local pequeno, salvo em:

```text
data/raw/
```

A camada RAW foi desenhada para registrar:

- dados brutos retornados por APIs públicas;
- arquivos FITS originais baixados do MAST;
- respostas JSON públicas;
- snapshots HTML de páginas consultadas;
- tabelas de busca;
- queries executadas;
- metadados de coleta;
- logs;
- manifestos;
- checksums SHA256.

## O que foi feito

Foi criado um pipeline local em Python para coletar dados de quatro grupos de fontes:

1. NASA Exoplanet Archive
2. MAST / Lightkurve / Astroquery
3. Exo.MAST
4. ETD / VarAstro

Foram considerados oito planetas candidatos:

| Prioridade | Planeta | Estrela hospedeira | Slug usado em pastas |
|---:|---|---|---|
| 1 | HAT-P-7 b | HAT-P-7 | `hat_p_7_b` |
| 2 | TrES-2 b | TrES-2 | `tres_2_b` |
| 3 | HD 189733 b | HD 189733 | `hd_189733_b` |
| 4 | HD 209458 b | HD 209458 | `hd_209458_b` |
| 5 | WASP-12 b | WASP-12 | `wasp_12_b` |
| 6 | WASP-10 b | WASP-10 | `wasp_10_b` |
| 7 | WASP-4 b | WASP-4 | `wasp_4_b` |
| 8 | HAT-P-32 b | HAT-P-32 | `hat_p_32_b` |

## O que não foi feito

Por desenho metodológico, esta etapa não faz:

- criação de `data/silver`;
- criação de `data/gold`;
- criação de `data/processed`;
- limpeza de dados;
- normalização de curvas de luz;
- remoção de outliers;
- faseamento;
- transformação estatística;
- geração de gráficos;
- modelagem física;
- inferência bayesiana;
- preenchimento de valores ausentes;
- criação de dados sintéticos;
- estimativa de parâmetros;
- escrita do texto final do TCC.

## Princípio RAW adotado

O princípio adotado foi:

> salvar o que a fonte pública retornou, registrar como foi obtido, e evitar modificar o conteúdo bruto.

Isso significa que:

- CSVs do NASA TAP foram salvos como retornados pelo endpoint;
- FITS do MAST foram salvos como produtos originais baixados pelo Lightkurve;
- JSONs de Exo.MAST foram salvos sem alteração;
- HTMLs do ETD/VarAstro foram salvos como snapshots públicos;
- JSONs de curva do ETD/VarAstro foram salvos como respostas públicas da API de visualização;
- extrações tabulares auxiliares foram salvas separadamente e marcadas como metadados extraídos.

## Estrutura RAW desejada e criada

A estrutura principal criada foi:

```text
data/
  raw/
    nasa_exoplanet_archive/
      pscomppars/
      ps/
      manifests/
    mast/
      lightkurve/
      astroquery/
      manifests/
    exomast/
      manifests/
    etd_varastro/
      html_snapshots/
      extracted_metadata/
      downloaded_lightcurves/
      manifests/
    _manifests/
    _logs/
```

Durante uma revisão posterior, três CSVs manuais antigos que ficavam soltos na raiz de `data/raw` foram removidos.

Esses arquivos:

- não estavam registrados no manifesto RAW;
- não eram usados pela Silver;
- não eram usados pela Gold;
- não seguiam a estrutura padronizada por fonte;
- haviam sido baixados manualmente antes da definição do pipeline.

A coleta estruturada considerada para metodologia é a que está organizada nas subpastas por fonte e registrada em:

```text
data/raw/_manifests/raw_data_manifest.csv
```

## Política de não sobrescrita

O pipeline evita sobrescrever artefatos existentes.

Quando um arquivo bruto já existe:

- ele é mantido;
- a coleta registra `skipped_existing`;
- o checksum do arquivo existente é registrado novamente no manifesto;
- quando um sidecar de metadados ou query difere de uma tentativa anterior, é criado um arquivo versionado por hash.

Exemplo de arquivos versionados por hash:

```text
query_query_b819ea7b4acd.sql
metadata_query_6a5ddfbed4d8.json
observations_api_a469dcaa60ba.csv
notes_api_ac5e86d3e2c2.md
```

Essa política mantém a rastreabilidade de tentativas anteriores sem apagar o histórico.

---

# Arquivo 3: `docs/raw/01_mapa_do_pipeline_e_codigo.md`

```text
Origem: docs/raw/01_mapa_do_pipeline_e_codigo.md
```

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

---

# Arquivo 4: `docs/raw/02_configuracao_execucao_ambiente.md`

```text
Origem: docs/raw/02_configuracao_execucao_ambiente.md
```

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

---

# Arquivo 5: `docs/raw/03_manifestos_logs_checksums_reexecucao.md`

```text
Origem: docs/raw/03_manifestos_logs_checksums_reexecucao.md
```

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

---

# Arquivo 6: `docs/raw/04_nasa_exoplanet_archive.md`

```text
Origem: docs/raw/04_nasa_exoplanet_archive.md
```

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

As colunas desejadas foram configuradas em `scripts/raw_data_config.py`:

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

---

# Arquivo 7: `docs/raw/05_mast_lightkurve_astroquery.md`

```text
Origem: docs/raw/05_mast_lightkurve_astroquery.md
```

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

---

# Arquivo 8: `docs/raw/06_exomast.md`

```text
Origem: docs/raw/06_exomast.md
```

# 06. Exo.MAST

## Fonte

Fonte pública:

```text
https://exo.mast.stsci.edu/
```

API pública usada:

```text
https://exo.mast.stsci.edu/api/v0.1
```

## Papel do Exo.MAST nesta etapa

O Exo.MAST foi usado como fonte auxiliar de metadados, não como fonte principal dos FITS.

O papel dele foi:

- resolver identificadores;
- obter propriedades públicas do planeta;
- recuperar listas de TCEs quando disponíveis;
- complementar rastreabilidade entre planeta, estrela e missões.

Os arquivos de curva de luz continuaram sendo baixados via MAST/Lightkurve.

## Estrutura de diretórios

```text
data/raw/exomast/
  hat_p_7_b/
  tres_2_b/
  hd_189733_b/
  hd_209458_b/
  wasp_12_b/
  wasp_10_b/
  wasp_4_b/
  hat_p_32_b/
  manifests/
```

## Arquivos por planeta

Arquivos comuns:

```text
identifiers.json
properties.json
notes.md
```

Arquivos opcionais:

```text
kepler_tces.json
tess_tces.json
```

Eles aparecem quando a API retorna identificadores associados à missão.

## `identifiers.json`

Retorno bruto do endpoint de identificadores.

Uso:

- resolver nome canônico;
- localizar IDs de missão;
- verificar nomes alternativos;
- apoiar rastreabilidade entre catálogos.

Exemplo de caminho:

```text
data/raw/exomast/hat_p_7_b/identifiers.json
```

## `properties.json`

Retorno bruto do endpoint de propriedades do planeta.

Uso:

- registrar metadados auxiliares;
- comparar futuramente com NASA Exoplanet Archive;
- apoiar validação de nome e alvo.

Exemplo:

```text
data/raw/exomast/wasp_12_b/properties.json
```

## `kepler_tces.json`

Lista de TCEs Kepler quando há identificador Kepler.

Na coleta validada, apareceu para:

- HAT-P-7 b;
- TrES-2 b.

Exemplo:

```text
data/raw/exomast/hat_p_7_b/kepler_tces.json
```

## `tess_tces.json`

Lista de TCEs TESS quando há identificador TESS.

Na coleta validada, apareceu para todos os planetas.

Exemplo:

```text
data/raw/exomast/hd_209458_b/tess_tces.json
```

## `notes.md`

Arquivo textual por planeta.

Registra:

- que Exo.MAST foi usado como fonte auxiliar;
- que FITS originais foram coletados via MAST/Lightkurve;
- resultados de tentativa por endpoint;
- endpoint de documentação.

## Quantidade de JSONs por planeta

| Planeta | JSONs Exo.MAST | Observação |
|---|---:|---|
| HAT-P-7 b | 4 | identificadores, propriedades, Kepler TCEs, TESS TCEs |
| TrES-2 b | 4 | identificadores, propriedades, Kepler TCEs, TESS TCEs |
| HD 189733 b | 3 | identificadores, propriedades, TESS TCEs |
| HD 209458 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-12 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-10 b | 3 | identificadores, propriedades, TESS TCEs |
| WASP-4 b | 3 | identificadores, propriedades, TESS TCEs |
| HAT-P-32 b | 3 | identificadores, propriedades, TESS TCEs |

Total de JSONs Exo.MAST:

```text
26
```

## O que não foi feito no Exo.MAST

Não foram baixadas curvas de luz via Exo.MAST.

Não foi feita:

- conversão de JSON para tabela analítica;
- escolha de TCE preferencial;
- validação astrofísica;
- cruzamento com curva de luz;
- modelagem.

## Uso metodológico no TCC

Na metodologia, esta fonte pode ser descrita como:

> O Exo.MAST foi usado como portal auxiliar de metadados e identificação, por meio de sua API pública. Para cada planeta foram coletados identificadores, propriedades e, quando disponíveis, listas de TCEs associadas às missões Kepler ou TESS. Esses JSONs foram preservados na camada RAW sem transformação e servem como apoio à rastreabilidade entre catálogos e produtos observacionais.

---

# Arquivo 9: `docs/raw/07_etd_varastro.md`

```text
Origem: docs/raw/07_etd_varastro.md
```

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

---

# Arquivo 10: `docs/raw/08_inventario_por_planeta.md`

```text
Origem: docs/raw/08_inventario_por_planeta.md
```

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

---

# Arquivo 11: `docs/raw/09_validacao_e_qualidade.md`

```text
Origem: docs/raw/09_validacao_e_qualidade.md
```

# 09. Validação e Qualidade da Coleta

## Objetivo da validação

A validação final teve como objetivo confirmar que:

- o comando principal funciona;
- as fontes foram processadas;
- os manifestos existem;
- os arquivos locais existem;
- os checksums batem;
- os dados principais foram coletados;
- a documentação e o README descrevem a reprodução.

## Comando principal validado

Comando:

```bash
.venv/bin/python scripts/download_raw_data.py
```

Resultado lógico da execução final:

```text
source_level_failures=0
```

## Validação do manifesto

Arquivos:

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```

Resultado:

```text
manifest_rows: 749
json_rows: 749
missing_local_files: 0
blank_checksums: 0
checksum_mismatches: 0
```

Interpretação:

- todo `local_path` registrado aponta para arquivo existente;
- todo arquivo local registrado tem SHA256;
- nenhum SHA256 divergiu do conteúdo atual.

## Validação de dependências

Foi executado:

```bash
.venv/bin/python -m pip check
```

Resultado:

```text
No broken requirements found.
```

Também foram importadas as bibliotecas principais:

```text
pandas
requests
astropy
astroquery
lightkurve
bs4
lxml
tqdm
```

Resultado:

```text
dependency imports: OK
```

Observações:

- o Lightkurve emitiu warning opcional sobre `oktopus`, relacionado a submódulo não usado nesta etapa;
- o Matplotlib informou cache temporário em `/tmp`, o que não afetou a coleta.

## Validação de estrutura

Diretórios principais presentes:

```text
data/raw/_logs
data/raw/_manifests
data/raw/nasa_exoplanet_archive
data/raw/mast
data/raw/exomast
data/raw/etd_varastro
```

Subestruturas presentes:

```text
data/raw/nasa_exoplanet_archive/pscomppars
data/raw/nasa_exoplanet_archive/ps
data/raw/nasa_exoplanet_archive/manifests
data/raw/mast/lightkurve
data/raw/mast/astroquery
data/raw/mast/manifests
data/raw/exomast/manifests
data/raw/etd_varastro/html_snapshots
data/raw/etd_varastro/extracted_metadata
data/raw/etd_varastro/downloaded_lightcurves
data/raw/etd_varastro/manifests
```

## Contagens finais

| Métrica | Valor |
|---|---:|
| Tamanho aproximado de `data/raw` | 82 MB |
| Arquivos em `data/raw` | 402 |
| Respostas NASA por planeta | 16 |
| Snapshot geral NASA | 1 |
| Tabelas de busca MAST | 24 |
| FITS MAST/Lightkurve | 30 |
| Snapshots HTML ETD | 16 |
| Curvas JSON ETD | 40 |
| JSONs Exo.MAST | 26 |
| Registros no snapshot NASA de planetas em trânsito | 4.653 |

## Validação NASA

Critérios:

- `raw_data_manifest.csv` existe;
- `pscomppars` existe para todos os planetas;
- `ps` existe para todos os planetas;
- snapshot geral existe;
- queries e metadados existem;
- checksums registrados.

Resultado:

- todos os oito planetas têm `pscomppars/response.csv`;
- todos os oito planetas têm `ps/response.csv`;
- snapshot geral existe em `all_transiting_planets_snapshot.csv`;
- schema TAP salvo para `pscomppars` e `ps`;
- checksums válidos.

## Validação MAST

Critérios:

- cada planeta tem busca por Kepler, K2 e TESS;
- cada busca gerou `search_results.csv`;
- downloads respeitaram limite;
- FITS estão registrados no manifesto;
- checksums válidos.

Resultado:

- 24 tabelas de busca;
- 30 FITS;
- K2 sem resultados para todos;
- Kepler com resultados para HAT-P-7 b e TrES-2 b;
- TESS com resultados para todos os planetas.

## Validação Exo.MAST

Critérios:

- cada planeta tem diretório em `data/raw/exomast`;
- cada planeta tem `identifiers.json`;
- cada planeta tem `properties.json`;
- TCEs salvos quando disponíveis;
- notas salvas.

Resultado:

- 26 JSONs;
- todos os planetas têm identificadores e propriedades;
- HAT-P-7 b e TrES-2 b têm Kepler TCEs;
- todos têm TESS TCEs.

## Validação ETD/VarAstro

Critérios:

- HTML salvo;
- JSON de busca salvo;
- página de detalhe salva;
- observações públicas salvas;
- verificação de registros privados;
- curvas JSON limitadas;
- notas e manifestos por planeta.

Resultado:

- 16 HTMLs;
- 8 JSONs de busca;
- 8 JSONs de observações públicas;
- 1.650 observações públicas consolidadas;
- zero registros privados retornados;
- 40 curvas JSON públicas;
- checksums válidos.

## Execução final sem falhas

Na execução final completa:

```text
NASA: finalizada
MAST: finalizada
Exo.MAST: finalizada
ETD/VarAstro: finalizada
source_level_failures: 0
```

## Sobre falhas históricas registradas

O manifesto contém 33 registros `failed`.

Eles são históricos e ocorreram durante:

- tentativa inicial com rede bloqueada;
- exploração inicial do ETD antes da identificação do endpoint público correto;
- tentativa de link HTML que retornou página em vez de arquivo.

Esses registros não invalidam a coleta final. Eles documentam o processo de descoberta e reexecução.

## O que ainda precisa ser validado na Silver

A camada RAW garante presença e rastreabilidade, mas não garante adequação analítica.

Na Silver será necessário:

- ler FITS e validar colunas;
- verificar unidades de tempo;
- padronizar escalas temporais;
- validar flags de qualidade;
- verificar duplicidades;
- separar observações por missão/setor/quarter;
- harmonizar IDs de planeta e estrela;
- avaliar quais curvas são adequadas para modelagem;
- documentar critérios de exclusão.

---

# Arquivo 12: `docs/raw/10_como_usar_na_metodologia.md`

```text
Origem: docs/raw/10_como_usar_na_metodologia.md
```

# 10. Como Usar Esta Documentação na Metodologia do TCC

## Objetivo deste documento

Este arquivo reorganiza a documentação técnica em uma linguagem mais próxima de metodologia acadêmica.

Ele não é o texto final do TCC. É uma base para escrever a seção metodológica depois.

## Formulação geral da etapa RAW

Uma formulação possível:

> Foi construída uma camada RAW em um datalake local para preservar dados públicos brutos e metadados de coleta relacionados a sistemas planetários em trânsito. A coleta foi implementada em Python, com scripts reexecutáveis, registro de logs, manifestos globais, checksums SHA256 e controle de não sobrescrita. Nesta etapa não foram realizadas limpeza, normalização, faseamento, remoção de outliers, geração de gráficos ou inferência estatística.

## Formulação sobre seleção dos planetas

Uma formulação possível:

> A coleta inicial considerou oito planetas candidatos, escolhidos por sua relevância para estudos de trânsitos e pela disponibilidade esperada de dados públicos: HAT-P-7 b, TrES-2 b, HD 189733 b, HD 209458 b, WASP-12 b, WASP-10 b, WASP-4 b e HAT-P-32 b. Para cada planeta foi definida a respectiva estrela hospedeira, utilizada nas consultas aos arquivos de curvas de luz espaciais.

## Formulação sobre NASA Exoplanet Archive

Uma formulação possível:

> Os parâmetros catalográficos planetários e estelares foram coletados do NASA Exoplanet Archive por meio do endpoint TAP síncrono. Foram consultadas as tabelas `pscomppars` e `ps`, com seleção dinâmica de colunas baseada no esquema disponível no momento da coleta. Para cada planeta, as respostas CSV retornadas pela API foram salvas sem transformação na camada RAW, acompanhadas das queries ADQL, metadados da requisição e checksums SHA256.

Complemento possível:

> Além das consultas individuais por planeta, foi salvo um snapshot da tabela `pscomppars` contendo planetas descobertos por trânsito, com período orbital não nulo e raio planetário ou profundidade de trânsito disponível. Esse snapshot foi preservado como referência bruta para eventual seleção futura de alvos, sem constituir ainda uma camada analítica.

## Formulação sobre MAST/Lightkurve

Uma formulação possível:

> As curvas de luz espaciais foram buscadas no MAST por meio da biblioteca Lightkurve, utilizando a estrela hospedeira como alvo de busca. Para cada planeta foram realizadas buscas independentes nas missões Kepler, K2 e TESS. As tabelas completas de resultados foram preservadas em CSV para rastreabilidade. Para evitar volume excessivo, foi baixado um subconjunto controlado de até três produtos FITS por planeta e missão, priorizando produtos de pipelines oficiais e exposições mais longas. Os arquivos FITS foram preservados em formato original, sem leitura ou transformação analítica na camada RAW.

Complemento possível:

> O fallback com Astroquery foi implementado para cenários de falha do Lightkurve, mas não foi necessário na execução validada, pois as buscas e downloads via Lightkurve foram concluídos.

## Formulação sobre Exo.MAST

Uma formulação possível:

> O Exo.MAST foi utilizado como fonte auxiliar de metadados e identificação. Para cada planeta foram coletados JSONs públicos contendo identificadores, propriedades e listas de TCEs quando disponíveis. Esses arquivos foram preservados sem alteração, servindo como apoio à rastreabilidade entre catálogos, identificadores de missão e produtos observacionais.

## Formulação sobre ETD/VarAstro

Uma formulação possível:

> Para dados terrestres de trânsito, foi consultado o portal ETD/VarAstro. A coleta utilizou páginas públicas e endpoints anônimos consumidos pelo próprio front-end do site, sem login, sem automação de navegador e com delay entre requisições. Para cada planeta foram salvos snapshots HTML, respostas JSON de busca, páginas públicas de detalhe, respostas JSON de observações e até cinco respostas JSON de curvas públicas. Os registros retornados foram verificados quanto ao campo `isPrivate`, e nenhum registro privado foi retornado na coleta validada.

Complemento importante:

> As curvas do ETD/VarAstro salvas nesta etapa são respostas JSON da API pública de visualização do portal, contendo séries fotométricas e metadados associados. Elas não devem ser descritas como os arquivos originais enviados pelos observadores sem validação adicional.

## Formulação sobre manifestos e checksums

Uma formulação possível:

> A rastreabilidade foi garantida por um manifesto global em CSV e JSON, contendo data/hora UTC da coleta, fonte, URL de origem, planeta, estrela hospedeira, missão, tipo de produto, caminho local, status, mensagem de erro, tamanho do arquivo e checksum SHA256. Ao final da validação, todos os arquivos locais registrados no manifesto possuíam checksum preenchido e consistente com o conteúdo em disco.

## Formulação sobre reexecução

Uma formulação possível:

> O pipeline foi desenvolvido para ser reexecutável. Arquivos previamente baixados não são sobrescritos; nesses casos, o evento é registrado como `skipped_existing`. Quando sidecars de queries ou metadados diferem entre execuções, novas versões identificadas por hash são criadas. Falhas pontuais são registradas em log e manifesto, sem interromper a coleta das demais fontes ou planetas.

## Formulação sobre limitações da etapa RAW

Uma formulação possível:

> Por se tratar da camada RAW, os dados foram preservados com mínima intervenção. Assim, inconsistências de esquema, diferenças de unidades, múltiplas referências catalográficas, flags de qualidade, duplicidades e variações entre missões não foram resolvidas nesta etapa. Essas questões serão tratadas em uma futura camada Silver, antes de qualquer modelagem ou inferência bayesiana.

## Formulação sobre ausência de processamento analítico

Uma formulação possível:

> Nenhuma curva de luz foi normalizada, faseada, filtrada, agregada ou modelada nesta etapa. A coleta teve caráter exclusivamente documental e operacional, com foco em preservação, rastreabilidade e reprodutibilidade dos dados públicos brutos.

## Números que podem ser citados

Números da coleta validada:

| Item | Quantidade |
|---|---:|
| Planetas candidatos | 8 |
| Arquivos em `data/raw` | 402 |
| Tamanho aproximado de `data/raw` | 82 MB |
| Registros no manifesto global | 749 |
| FITS MAST/Lightkurve | 30 |
| Curvas JSON ETD/VarAstro | 40 |
| Tabelas de busca MAST | 24 |
| Snapshots HTML ETD | 16 |
| JSONs Exo.MAST | 26 |
| Observações públicas ETD consolidadas | 1.650 |
| Registros privados ETD retornados | 0 |
| Divergências de checksum | 0 |

## Cuidados ao escrever a metodologia

Evite dizer:

- que os dados foram limpos;
- que as curvas foram normalizadas;
- que houve inferência;
- que os JSONs do ETD são necessariamente arquivos originais dos observadores;
- que a seleção Gold já foi feita;
- que HAT-P-7 b já foi definitivamente escolhido como único alvo final.

Prefira dizer:

- que HAT-P-7 b é candidato principal inicial;
- que a camada RAW foi construída para múltiplos planetas;
- que a etapa preserva dados públicos brutos;
- que a seleção analítica será feita depois;
- que a Silver ainda será responsável por padronização e validação.

## Próximos passos metodológicos naturais

Para a camada Silver:

1. Ler FITS e inspecionar HDUs/colunas.
2. Padronizar identificadores de planeta e estrela.
3. Harmonizar escalas de tempo.
4. Selecionar flags de qualidade.
5. Separar curvas por missão, setor, quarter ou campanha.
6. Definir critérios de exclusão.
7. Preparar curvas para análise exploratória.

Para a camada Gold:

1. Escolher planeta-alvo.
2. Definir fonte ou combinação de fontes.
3. Selecionar curvas específicas.
4. Construir dataset analítico final.
5. Preparar entrada para modelagem bayesiana.

---

# Arquivo 13: `docs/raw/11_dicionario_de_arquivos_e_campos.md`

```text
Origem: docs/raw/11_dicionario_de_arquivos_e_campos.md
```

# 11. Dicionário de Arquivos, Campos e Localização das Informações

## Objetivo

Este documento é um mapa rápido para localizar informações na camada RAW.

Ele responde:

- onde está cada tipo de arquivo;
- que informação cada arquivo contém;
- se o arquivo é bruto ou extraído;
- qual fonte originou o conteúdo;
- quais campos principais podem ser encontrados.

## Classificação usada

| Classificação | Significado |
|---|---|
| Bruto | Conteúdo salvo como retornado pela fonte ou biblioteca de download |
| Sidecar | Arquivo criado pelo pipeline para explicar a coleta |
| Extraído | Tabela derivada de HTML/JSON público para facilitar rastreabilidade |
| Manifesto | Arquivo de controle com status, caminho, checksum e metadados |
| Log | Registro textual da execução |

## Manifesto global

### Caminho

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```

### Classificação

Manifesto.

### Conteúdo

Contém todos os eventos de coleta registrados pelo pipeline.

### Campos

| Campo | Descrição |
|---|---|
| `collected_at_utc` | Data/hora UTC do evento |
| `source_name` | Fonte lógica |
| `source_url` | URL de origem |
| `planet_name` | Planeta associado |
| `host_star` | Estrela hospedeira |
| `local_path` | Caminho local do arquivo |
| `file_name` | Nome do arquivo |
| `file_type` | Tipo/extensão |
| `mission` | Missão, quando aplicável |
| `product_type` | Produto lógico |
| `query_or_search_term` | Query ou busca |
| `status` | Resultado do evento |
| `error_message` | Erro, se houver |
| `sha256` | Checksum do arquivo local |
| `file_size_bytes` | Tamanho em bytes |
| `notes` | Notas adicionais |

## Log global

### Caminho

```text
data/raw/_logs/download_raw_data.log
```

### Classificação

Log.

### Conteúdo

Registra início, fim, fontes, planetas, missões, arquivos baixados, arquivos pulados, erros e warnings.

## NASA: parâmetros compostos `pscomppars`

### Caminho por planeta

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/response.csv
```

### Classificação

Bruto.

### Conteúdo

CSV retornado pelo endpoint TAP da NASA.

### Campos principais

| Campo | Conteúdo |
|---|---|
| `pl_name` | Nome do planeta |
| `hostname` | Estrela hospedeira |
| `discoverymethod` | Método de descoberta |
| `disc_facility` | Instalação de descoberta |
| `pl_orbper` | Período orbital |
| `pl_orbpererr1` | Erro superior do período |
| `pl_orbpererr2` | Erro inferior do período |
| `pl_tranmid` | Tempo de meio trânsito |
| `pl_tranmiderr1` | Erro superior do meio trânsito |
| `pl_tranmiderr2` | Erro inferior do meio trânsito |
| `pl_trandur` | Duração do trânsito |
| `pl_trandurerr1` | Erro superior da duração |
| `pl_trandurerr2` | Erro inferior da duração |
| `pl_trandep` | Profundidade do trânsito |
| `pl_trandeperr1` | Erro superior da profundidade |
| `pl_trandeperr2` | Erro inferior da profundidade |
| `pl_rade` | Raio planetário em raios terrestres |
| `pl_radeerr1` | Erro superior do raio em raios terrestres |
| `pl_radeerr2` | Erro inferior do raio em raios terrestres |
| `pl_radj` | Raio planetário em raios de Júpiter |
| `st_rad` | Raio estelar |
| `st_raderr1` | Erro superior do raio estelar |
| `st_raderr2` | Erro inferior do raio estelar |
| `st_teff` | Temperatura efetiva estelar |
| `st_mass` | Massa estelar |
| `sy_dist` | Distância do sistema |

## NASA: tabela `ps`

### Caminho por planeta

```text
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/response.csv
```

### Classificação

Bruto.

### Conteúdo

CSV retornado pelo endpoint TAP da NASA com múltiplas linhas possíveis por planeta.

### Como interpretar

Enquanto `pscomppars` retornou uma linha por planeta, `ps` retornou múltiplas linhas por planeta, refletindo diferentes entradas/referências/soluções catalográficas.

## NASA: queries

### Caminho

```text
data/raw/nasa_exoplanet_archive/pscomppars/{planet_slug}/query.sql
data/raw/nasa_exoplanet_archive/ps/{planet_slug}/query.sql
```

ou versões:

```text
query_query_<hash>.sql
```

### Classificação

Sidecar.

### Conteúdo

ADQL executada ou tentativa histórica.

## NASA: metadados

### Caminho

```text
metadata.json
metadata_query_<hash>.json
```

### Classificação

Sidecar.

### Conteúdo

Registra:

- query;
- planeta;
- estrela;
- tabela;
- status;
- colunas selecionadas;
- URL de requisição;
- número estimado de linhas, quando disponível.

## NASA: snapshot de planetas em trânsito

### Caminho

```text
data/raw/nasa_exoplanet_archive/pscomppars/all_transiting_planets_snapshot.csv
```

### Classificação

Bruto filtrado por query.

### Conteúdo

CSV retornado pela NASA com planetas de descoberta por trânsito, período orbital não nulo e raio planetário ou profundidade disponível.

## MAST: tabela de busca

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/search_results.csv
```

### Classificação

Bruto de busca.

### Conteúdo

Tabela retornada por `lightkurve.search_lightcurve`.

### Campos comuns

| Campo | Descrição |
|---|---|
| `mission` | Produto/missão |
| `year` | Ano ou identificador temporal |
| `author` | Autor/pipeline do produto |
| `exptime` | Tempo de exposição |
| `target_name` | Nome do alvo |
| `distance` | Distância angular da busca |
| `productFilename` | Nome do produto |
| `dataURI` | URI de download no MAST |

## MAST: FITS de curva de luz

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/mastDownload/
```

### Classificação

Bruto.

### Conteúdo

Arquivos FITS originais baixados via Lightkurve.

### Como interpretar

Não foram abertos nem transformados nesta etapa. A leitura dos HDUs e colunas deve ocorrer na Silver.

## MAST: manifesto de download por missão

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/download_manifest.csv
```

### Classificação

Manifesto local da fonte.

### Campos

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

## MAST: metadata por missão

### Caminho

```text
data/raw/mast/lightkurve/{planet_slug}/{mission}/metadata.json
```

### Classificação

Sidecar.

### Conteúdo

Resumo da busca:

- planeta;
- estrela;
- missão;
- termo de busca;
- quantidade de resultados;
- limite de download;
- quantidade selecionada;
- política de seleção.

## Exo.MAST: identificadores

### Caminho

```text
data/raw/exomast/{planet_slug}/identifiers.json
```

### Classificação

Bruto.

### Conteúdo

Resposta JSON da API pública de identificadores.

### Uso

- nome canônico;
- IDs de missão;
- vínculo com Kepler/TESS.

## Exo.MAST: propriedades

### Caminho

```text
data/raw/exomast/{planet_slug}/properties.json
```

### Classificação

Bruto.

### Conteúdo

Propriedades públicas retornadas pela API Exo.MAST.

## Exo.MAST: TCEs

### Caminho

```text
data/raw/exomast/{planet_slug}/kepler_tces.json
data/raw/exomast/{planet_slug}/tess_tces.json
```

### Classificação

Bruto.

### Conteúdo

Listas de TCEs associadas ao planeta ou alvo quando a API fornece identificador correspondente.

## ETD: snapshot HTML da busca

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/catalog_search.html
```

### Classificação

Bruto.

### Conteúdo

HTML público da página do catálogo de exoplanetas.

## ETD: JSON de resultado da busca

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/catalog_search_results.json
```

### Classificação

Bruto.

### Conteúdo

JSON retornado pelo endpoint público:

```text
/api/Search/Exoplanets
```

Campos úteis:

- ID interno do planeta;
- nome;
- status;
- profundidade;
- duração;
- período;
- contagem de trânsitos.

## ETD: página de detalhe

### Caminho

```text
data/raw/etd_varastro/html_snapshots/{planet_slug}/planet_detail.html
```

### Classificação

Bruto.

### Conteúdo

HTML público da página do planeta no VarAstro.

## ETD: observações brutas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_raw.json
```

### Classificação

Bruto.

### Conteúdo

Resposta pública do endpoint:

```text
/api/OcGate/Exoplanets/{id}
```

Campos comuns em cada trânsito:

| Campo | Descrição |
|---|---|
| `band` | Banda/filtro fotométrico |
| `dataVersion` | Versão dos dados no VarAstro |
| `depth` | Profundidade |
| `depthErr` | Erro da profundidade |
| `dqi` | Indicador de qualidade |
| `duration` | Duração |
| `durationErr` | Erro da duração |
| `epoch` | Época |
| `hjdMid` | Meio trânsito em HJD |
| `jdMidErr` | Erro do meio trânsito |
| `obsId` | ID da observação |
| `observer` | Observador |
| `reference` | Referência |
| `referenceUrl` | URL de referência |
| `transId` | ID do trânsito |
| `isPrivate` | Indicador de privacidade |

## ETD: observações extraídas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_api_<hash>.csv
```

### Classificação

Extraído.

### Conteúdo

Tabela CSV derivada de `observations_raw.json`, mantendo a linha original serializada em `raw_metadata_json`.

## ETD: curvas JSON públicas

### Caminho

```text
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/NN_observation_{obsId}_transit_{transId}.json
```

### Classificação

Bruto.

### Conteúdo

Resposta pública do endpoint:

```text
/api/charts/observation/{obsId}
```

Campos observados:

```text
timeSpan
photometry
minimas
transits
airmass
origRawHeader
magBand
```

Dentro de `photometry`, foram observados:

```text
jd
mag
magError
filter
```

## ETD: notas

### Caminho

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/notes.md
data/raw/etd_varastro/extracted_metadata/{planet_slug}/notes_api_<hash>.md
```

### Classificação

Sidecar.

### Conteúdo

Explica:

- URLs consultadas;
- número de linhas extraídas;
- número de curvas selecionadas;
- limites;
- erros;
- limitações.

## ETD: manifesto por planeta

### Caminho

```text
data/raw/etd_varastro/manifests/{planet_slug}_manifest*.csv
```

### Classificação

Manifesto local da fonte.

### Conteúdo

Registra arquivos ETD/VarAstro por planeta, com status, checksum, tamanho e notas.

## Arquivos soltos na raiz de `data/raw`

### Situação atual

Não há arquivos CSV soltos na raiz de `data/raw`.

### Decisão de limpeza

Três arquivos manuais antigos foram removidos durante revisão posterior, porque:

- não estavam registrados no manifesto RAW;
- não tinham checksums controlados pelo pipeline;
- não eram usados pela Silver;
- não eram usados pela Gold;
- duplicavam ou antecediam coletas depois feitas de forma estruturada.

### Interpretação

A camada RAW válida para rastreabilidade é composta pelos arquivos nas subpastas por fonte e pelo manifesto global:

```text
data/raw/_manifests/raw_data_manifest.csv
```

---
