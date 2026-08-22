# Documentacao Completa Silver
Documento consolidado para uso como contexto em GPT.
- Gerado em UTC: `2026-06-16T15:47:14+00:00`
- Pasta de origem: `docs/silver`
- Observacao: este arquivo e apenas uma exportacao consolidada; os documentos originais nao foram removidos nem alterados.
- Uso sugerido: copiar este Markdown como contexto quando precisar discutir esta etapa especifica do TCC.

## Arquivos Incluidos
1. `docs/silver/README.md`
2. `docs/silver/12_contexto_escopo_e_regras_silver.md`
3. `docs/silver/13_mapa_do_pipeline_silver_e_codigo.md`
4. `docs/silver/14_catalogos_silver_nasa_e_exomast.md`
5. `docs/silver/15_curvas_mast_silver.md`
6. `docs/silver/16_etd_varastro_silver.md`
7. `docs/silver/17_manifestos_logs_validacoes_silver.md`
8. `docs/silver/18_inventario_silver_por_planeta.md`
9. `docs/silver/19_dicionario_de_arquivos_e_campos_silver.md`
10. `docs/silver/20_como_usar_silver_na_metodologia.md`

---

# Arquivo 1: `docs/silver/README.md`

```text
Origem: docs/silver/README.md
```

# Documentação Silver

Esta pasta contém a documentação da camada **Silver** do datalake local.

A Silver lê exclusivamente a RAW, valida os artefatos brutos e gera tabelas padronizadas, auditáveis e rastreáveis em `data/silver/`.

## Escopo

A Silver cobre:

- validação do manifesto RAW;
- consolidação de catálogos NASA;
- tabularização de JSONs Exo.MAST;
- leitura dos FITS MAST;
- extração de curvas de luz tabulares;
- consolidação de observações ETD;
- extração de pontos fotométricos ETD;
- criação de manifestos, logs e validações.

Ela não executa:

- criação de Gold;
- normalização final de curvas;
- faseamento orbital;
- remoção de outliers;
- filtragem por qualidade;
- conversão de magnitude para fluxo;
- modelagem física;
- inferência bayesiana.

## Como ler

Os arquivos estão numerados em ordem sugerida:

1. [12_contexto_escopo_e_regras_silver.md](12_contexto_escopo_e_regras_silver.md)  
   Papel da Silver, regras de imutabilidade da RAW e limites da etapa.

2. [13_mapa_do_pipeline_silver_e_codigo.md](13_mapa_do_pipeline_silver_e_codigo.md)  
   Scripts, módulos e fluxo de execução Silver.

3. [14_catalogos_silver_nasa_e_exomast.md](14_catalogos_silver_nasa_e_exomast.md)  
   Catálogos NASA e Exo.MAST.

4. [15_curvas_mast_silver.md](15_curvas_mast_silver.md)  
   Leitura dos FITS MAST e geração das curvas tabulares.

5. [16_etd_varastro_silver.md](16_etd_varastro_silver.md)  
   Observações ETD, curvas JSON públicas e pontos fotométricos.

6. [17_manifestos_logs_validacoes_silver.md](17_manifestos_logs_validacoes_silver.md)  
   Manifestos, logs, checksums e validações Silver.

7. [18_inventario_silver_por_planeta.md](18_inventario_silver_por_planeta.md)  
   Inventário Silver por planeta.

8. [19_dicionario_de_arquivos_e_campos_silver.md](19_dicionario_de_arquivos_e_campos_silver.md)  
   Dicionário de arquivos e campos Silver.

9. [20_como_usar_silver_na_metodologia.md](20_como_usar_silver_na_metodologia.md)  
   Como aproveitar a Silver na metodologia.

## Saída principal documentada

```text
data/silver/
```

Manifesto Silver:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

Documentação técnica mantida no repositório:

```text
docs/silver/
```

---

# Arquivo 2: `docs/silver/12_contexto_escopo_e_regras_silver.md`

```text
Origem: docs/silver/12_contexto_escopo_e_regras_silver.md
```

# 12. Contexto, Escopo e Regras da Camada Silver

## Objetivo deste documento

Este documento descreve a implementação da camada **Silver** do datalake local do projeto:

**Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional**

- Aluno: Leonardo Moraes Barca
- Orientadora: Patrícia Belfiore Fávero
- Curso: MBA em Data Science e Analytics
- Etapa documentada: transformação tabular, validação e padronização técnica dos dados brutos já coletados.

A documentação aqui registrada foi escrita para servir como base técnica para a futura seção de metodologia do TCC.

## Papel da Silver no datalake

O datalake local foi organizado em camadas:

| Camada | Papel | Status |
|---|---|---|
| RAW | Preservar dados públicos como coletados | Implementada |
| Silver | Validar, tabularizar e padronizar dados brutos | Implementada |
| Gold | Construir dataset analítico final para um planeta específico | Não implementada |

A Silver fica em:

```text
data/silver/
```

Ela lê dados de:

```text
data/raw/
```

e não altera a RAW.

## Princípio central

A RAW foi tratada como imutável.

Durante a implementação e execução da Silver, não foram feitos:

- alteração de arquivos em `data/raw/`;
- remoção de arquivos em `data/raw/`;
- movimentação de arquivos em `data/raw/`;
- renomeação de arquivos em `data/raw/`;
- sobrescrita de arquivos em `data/raw/`;
- novo download de dados externos;
- chamada de rede.

A verificação final comparou checksums da RAW antes e depois da construção da Silver. O resultado não indicou diferenças.

## Objetivo técnico da Silver

A Silver transforma os artefatos RAW em tabelas CSV padronizadas, auditáveis e reexecutáveis.

Ela foi criada para responder às seguintes perguntas:

1. Quais dados brutos foram usados?
2. Onde cada linha Silver se conecta ao arquivo RAW original?
3. Quais planetas possuem catálogos consolidados?
4. Quais planetas possuem curvas MAST em formato tabular?
5. Quais observações e curvas públicas ETD foram consolidadas?
6. Quais colunas estão presentes ou ausentes nos produtos FITS?
7. Quais validações foram executadas antes de qualquer análise científica?

## Fontes usadas pela Silver

A Silver usou somente os dados já existentes na RAW.

| Fonte | Entrada RAW | Saída Silver |
|---|---|---|
| NASA Exoplanet Archive | CSVs `pscomppars`, `ps` e snapshot geral | Catálogos NASA padronizados |
| Exo.MAST | JSONs de identificadores, propriedades e TCEs | Tabelas achatadas |
| MAST / Lightkurve | FITS originais de Kepler e TESS | Curvas de luz tabulares e metadados FITS |
| ETD / VarAstro | JSONs/CSVs públicos de observações e curvas | Observações, pontos fotométricos e metadados |

## O que foi padronizado

Foram padronizados:

- nomes de planetas;
- slugs dos planetas;
- estrelas hospedeiras;
- nomes de colunas catalográficas;
- campos principais de curvas de luz;
- metadados de missão;
- metadados de origem;
- checksums dos artefatos Silver;
- manifestos e logs da execução.

## O que não foi padronizado cientificamente

A Silver não transforma os dados em uma base analítica final.

Por isso, não foram feitos:

- normalização de fluxo;
- conversão de magnitude para fluxo;
- faseamento orbital;
- seleção definitiva de janela de trânsito;
- remoção de outliers;
- filtragem por flags de qualidade;
- interpolação;
- imputação de valores ausentes;
- escolha de solução orbital preferida;
- ajuste de curva de luz;
- inferência bayesiana.

## Por que manter a Silver sem modelagem

A separação é metodologicamente importante.

A Silver demonstra:

- rastreabilidade;
- reprodutibilidade;
- controle de qualidade inicial;
- separação entre dado bruto e dado preparado;
- preservação de incertezas e ausências;
- ausência de decisões analíticas prematuras.

Esses pontos são relevantes para um TCC que pretende discutir inferência sob incerteza observacional, porque deixam claro que a etapa de organização dos dados não introduziu inferências, filtros ou preenchimentos antes da modelagem.

## Planetas cobertos

A configuração Silver manteve os oito planetas candidatos da RAW:

| Planeta | Estrela | Slug |
|---|---|---|
| HAT-P-7 b | HAT-P-7 | `hat_p_7_b` |
| TrES-2 b | TrES-2 | `tres_2_b` |
| HD 189733 b | HD 189733 | `hd_189733_b` |
| HD 209458 b | HD 209458 | `hd_209458_b` |
| WASP-12 b | WASP-12 | `wasp_12_b` |
| WASP-10 b | WASP-10 | `wasp_10_b` |
| WASP-4 b | WASP-4 | `wasp_4_b` |
| HAT-P-32 b | HAT-P-32 | `hat_p_32_b` |

## Diretórios criados

Estrutura Silver principal:

```text
data/silver/
├── catalogs/
│   ├── nasa/
│   └── exomast/
├── lightcurves/
│   ├── mast/
│   └── etd/
├── etd/
├── validation/
├── manifests/
├── logs/
└── docs/
```

Observação: a pasta `data/silver/lightcurves/etd/` foi criada para manter separação conceitual, mas as tabelas ETD consolidadas foram gravadas em `data/silver/etd/`, conforme definido na especificação da tarefa.

## Comando principal

Pipeline completo:

```bash
python scripts/build_silver_data.py
```

No ambiente desta execução, foi usado:

```bash
.venv/bin/python scripts/build_silver_data.py
```

Isso ocorreu porque o comando `python` não estava disponível no PATH fora do ambiente virtual. Após ativar o ambiente com `source .venv/bin/activate`, o comando documentado com `python` é o esperado.

## Resultado geral da execução

Resumo validado:

| Métrica | Valor |
|---|---:|
| Registros lidos no manifesto RAW | 749 |
| Arquivos RAW locais únicos validados | 399 |
| Arquivos RAW ausentes | 0 |
| Divergências de checksum RAW | 0 |
| FITS MAST processados | 30 |
| Curvas MAST tabularizadas | 10 |
| Observações ETD consolidadas | 1.650 |
| Pontos fotométricos ETD extraídos | 8.752 |
| Arquivos Silver criados | 29 |
| Registros no manifesto Silver | 26 |
| Divergências de checksum Silver | 0 |

## Status da Gold

A Gold não foi criada.

A Silver apenas indica disponibilidade de dados. Com base na disponibilidade, HAT-P-7 b e TrES-2 b são candidatos fortes para a futura Gold porque possuem curvas Kepler e TESS. HAT-P-7 b permanece como candidato principal inicial.

---

# Arquivo 3: `docs/silver/13_mapa_do_pipeline_silver_e_codigo.md`

```text
Origem: docs/silver/13_mapa_do_pipeline_silver_e_codigo.md
```

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
scripts/silver_data_config.py
```

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
| `config.py` | Loader simples da configuração |
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

---

# Arquivo 4: `docs/silver/14_catalogos_silver_nasa_e_exomast.md`

```text
Origem: docs/silver/14_catalogos_silver_nasa_e_exomast.md
```

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

---

# Arquivo 5: `docs/silver/15_curvas_mast_silver.md`

```text
Origem: docs/silver/15_curvas_mast_silver.md
```

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

---

# Arquivo 6: `docs/silver/16_etd_varastro_silver.md`

```text
Origem: docs/silver/16_etd_varastro_silver.md
```

# 16. ETD / VarAstro na Camada Silver

## Objetivo deste documento

Este documento descreve como os dados terrestres públicos do ETD / VarAstro foram consolidados na camada Silver.

Entradas RAW:

```text
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_raw.json
data/raw/etd_varastro/extracted_metadata/{planet_slug}/observations_api_*.csv
data/raw/etd_varastro/downloaded_lightcurves/{planet_slug}/*.json
```

Saídas Silver:

```text
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_points.csv
data/silver/etd/etd_lightcurve_metadata.csv
```

## Natureza dos dados ETD

Os dados ETD coletados na RAW são respostas públicas da API de visualização do portal.

Limitação importante:

```text
As curvas ETD salvas na RAW são JSONs públicos retornados pela API de visualização, não necessariamente os arquivos originais enviados pelos observadores.
```

Essa limitação foi preservada na documentação e deve aparecer na metodologia.

## `etd_observations.csv`

Caminho:

```text
data/silver/etd/etd_observations.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 1.650 |
| Colunas | 25 |

## Campos de observação

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | JSON/CSV RAW de origem |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do arquivo RAW |
| `obs_id` | Identificador de observação, quando disponível |
| `trans_id` | Identificador de trânsito, quando disponível |
| `epoch` | Época do trânsito |
| `hjd_mid` | Meio do trânsito em HJD |
| `jd_mid_err` | Incerteza do meio do trânsito |
| `duration` | Duração |
| `duration_err` | Incerteza da duração |
| `depth` | Profundidade |
| `depth_err` | Incerteza da profundidade |
| `dqi` | Data Quality Index informado pelo ETD |
| `band` | Filtro/banda |
| `observer` | Observador |
| `reference` | Referência textual |
| `reference_url` | URL de referência |
| `data_version` | Versão de dado |
| `is_private` | Indicador de privacidade |
| `raw_metadata_json` | Registro original compacto |
| `silver_created_at_utc` | Data UTC de criação |

## Tratamento de registros privados

A regra implementada foi:

1. Ler registros públicos e privados retornados pelo JSON, se existirem.
2. Contar registros privados.
3. Não incluir registros privados em `etd_observations.csv`.
4. Registrar contagem na validação.

Resultado validado:

```text
private_records_count = 0 para todos os planetas
```

## Observações por planeta

| Planeta | Observações públicas | Registros privados |
|---|---:|---:|
| HAT-P-7 b | 60 | 0 |
| TrES-2 b | 371 | 0 |
| HD 189733 b | 218 | 0 |
| HD 209458 b | 92 | 0 |
| WASP-12 b | 376 | 0 |
| WASP-10 b | 241 | 0 |
| WASP-4 b | 80 | 0 |
| HAT-P-32 b | 212 | 0 |

## `etd_lightcurve_points.csv`

Caminho:

```text
data/silver/etd/etd_lightcurve_points.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 8.752 |
| Colunas | 18 |

## Campos de pontos fotométricos

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | JSON RAW da curva |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do JSON RAW |
| `obs_id` | ID da observação |
| `trans_id` | ID do trânsito |
| `point_index` | Índice do ponto dentro da curva |
| `jd` | Tempo em JD |
| `mag` | Magnitude |
| `mag_error` | Erro da magnitude |
| `filter` | Filtro do ponto, quando disponível |
| `airmass` | Massa de ar alinhada por índice ou tempo |
| `mag_band` | Banda global informada no JSON |
| `source_json_file` | Nome do JSON de curva |
| `silver_created_at_utc` | Data UTC de criação |

## Pontos fotométricos por planeta

| Planeta | Curvas JSON | Pontos |
|---|---:|---:|
| HAT-P-7 b | 5 | 1.243 |
| TrES-2 b | 5 | 1.180 |
| HD 189733 b | 5 | 1.262 |
| HD 209458 b | 5 | 1.625 |
| WASP-12 b | 5 | 793 |
| WASP-10 b | 5 | 322 |
| WASP-4 b | 5 | 1.039 |
| HAT-P-32 b | 5 | 1.288 |

## Filtros observados

| Planeta | Filtros/bandas observados |
|---|---|
| HAT-P-7 b | `Clear`, `R`, `SLOAN 'r`, `V to IR` |
| TrES-2 b | `Clear`, `L`, `R`, `clear`, `r` |
| HD 189733 b | `Clear`, `R`, `i` |
| HD 209458 b | `Clear`, `I`, `R` |
| WASP-12 b | `CBB`, `Clear`, `Luminance`, `R`, `V to IR` |
| WASP-10 b | `Clear`, `IR-UV`, `L`, `R` |
| WASP-4 b | `Clear`, `Luminance`, `V` |
| HAT-P-32 b | `CV`, `IR`, `Sloan r'`, `V`, `r` |

## `etd_lightcurve_metadata.csv`

Caminho:

```text
data/silver/etd/etd_lightcurve_metadata.csv
```

Resultado:

| Métrica | Valor |
|---|---:|
| Linhas | 40 |
| Colunas | 21 |

Uma linha por JSON público de curva.

Campos:

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `source_json_file` | Arquivo JSON |
| `source_raw_path` | Caminho RAW |
| `obs_id` | ID da observação |
| `trans_id` | ID do trânsito |
| `point_count` | Quantidade de pontos |
| `has_photometry` | Presença do bloco `photometry` |
| `has_airmass` | Presença do bloco `airmass` |
| `has_minimas` | Presença do bloco `minimas` |
| `has_transits` | Presença do bloco `transits` |
| `mag_band` | Banda global |
| `time_span` | Intervalo de tempo |
| `orig_raw_header_present` | Presença de header original |
| `status` | Resultado |
| `error_message` | Erro, se houver |

## Decisões de implementação

### Magnitude preservada

A Silver manteve `mag` como magnitude.

Não foi feita conversão para fluxo.

Justificativa:

- a conversão envolve decisão científica;
- a etapa Silver deve evitar transformação analítica;
- a comparação com curvas espaciais deve ficar para etapa posterior.

### Airmass

Quando o bloco `airmass` existe e tem o mesmo comprimento da fotometria, a Silver alinha por índice.

Se necessário, também tenta alinhar por tempo.

Quando não há alinhamento claro, deixa vazio.

### `obs_id` e `trans_id`

Os IDs foram extraídos do nome do arquivo JSON quando presentes.

Exemplo:

```text
01_observation_94348_transit_12787.json
```

vira:

```text
obs_id = 94348
trans_id = 12787
```

## Validação ETD

Arquivo:

```text
data/silver/validation/silver_etd_summary.csv
```

Ele resume:

- observações por planeta;
- registros privados;
- curvas baixadas;
- pontos fotométricos;
- filtros observados;
- DQI mínimo e máximo.

## Limitações

- Curvas são JSONs públicos da API de visualização.
- Não há garantia de equivalência com o arquivo original do observador.
- Filtros podem vir com grafias heterogêneas.
- A qualidade DQI foi preservada, mas não usada para filtrar dados.
- Magnitude não foi convertida em fluxo.
- Não há harmonização temporal com MAST.

## Uso futuro

Na Gold, os dados ETD podem ser usados para:

- comparação qualitativa com curvas espaciais;
- validação externa de épocas de trânsito;
- estudo de incerteza observacional terrestre;
- seleção de curvas com DQI aceitável;
- análise de consistência temporal.

Essas decisões não foram tomadas na Silver.

---

# Arquivo 7: `docs/silver/17_manifestos_logs_validacoes_silver.md`

```text
Origem: docs/silver/17_manifestos_logs_validacoes_silver.md
```

# 17. Manifestos, Logs e Validações da Camada Silver

## Objetivo deste documento

Este documento descreve os mecanismos de controle da camada Silver:

- manifesto Silver;
- logs de execução;
- validação do manifesto RAW;
- validações das tabelas Silver;
- checksums;
- reprodutibilidade.

## Manifesto Silver

Arquivos:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

Resultado final:

| Métrica | Valor |
|---|---:|
| Registros no manifesto Silver | 26 |
| Registros com status `created` | 26 |
| Registros com status `failed` | 0 |
| Checksums Silver verificados | 26 |
| Divergências de checksum Silver | 0 |
| Arquivos Silver ausentes no manifesto | 0 |

## Colunas do manifesto Silver

| Coluna | Significado |
|---|---|
| `created_at_utc` | Data/hora UTC do registro |
| `silver_layer` | Camada registrada, sempre `silver` |
| `source_raw_manifest_path` | Caminho do manifesto RAW usado |
| `source_raw_path` | Caminho RAW associado, quando aplicável |
| `source_name` | Fonte lógica |
| `planet_name` | Planeta associado, quando aplicável |
| `host_star` | Estrela hospedeira, quando aplicável |
| `mission` | Missão, quando aplicável |
| `raw_file_type` | Tipo do arquivo RAW |
| `silver_file_path` | Caminho do artefato Silver |
| `silver_file_name` | Nome do arquivo Silver |
| `silver_file_type` | Tipo/extensão do arquivo Silver |
| `transformation_type` | Tipo lógico de transformação |
| `row_count` | Número de linhas criadas |
| `column_count` | Número de colunas criadas |
| `status` | Resultado da criação |
| `error_message` | Erro, se houver |
| `sha256` | Checksum SHA256 do arquivo Silver |
| `file_size_bytes` | Tamanho do arquivo Silver |
| `notes` | Observações |

## Tipos de transformação registrados

| Transformação | Quantidade |
|---|---:|
| `mast_fits_to_silver_lightcurve` | 10 |
| `raw_manifest_validation_summary` | 1 |
| `raw_manifest_validation_detail` | 1 |
| `nasa_pscomppars_selected_planets` | 1 |
| `nasa_ps_all_solutions` | 1 |
| `nasa_all_transiting_planets_snapshot` | 1 |
| `exomast_identifiers` | 1 |
| `exomast_properties` | 1 |
| `exomast_tces` | 1 |
| `mast_fits_metadata` | 1 |
| `etd_observations` | 1 |
| `etd_lightcurve_points` | 1 |
| `etd_lightcurve_metadata` | 1 |
| `silver_summary_by_planet` | 1 |
| `silver_mast_quality_summary` | 1 |
| `silver_etd_summary` | 1 |
| `silver_column_presence_report` | 1 |

## Log Silver

Arquivo:

```text
data/silver/logs/build_silver_data.log
```

O log registra:

- início do pipeline;
- etapas executadas;
- validação da RAW;
- processamento NASA;
- processamento Exo.MAST;
- processamento de cada FITS MAST;
- processamento ETD;
- criação de validações;
- escrita da documentação;
- fim do pipeline.

## Validação do manifesto RAW

Arquivos:

```text
data/silver/validation/raw_manifest_summary.csv
data/silver/validation/raw_manifest_validation.json
```

### Resultado validado

| Métrica | Valor |
|---|---:|
| Registros no manifesto RAW | 749 |
| Arquivos RAW locais únicos validados | 399 |
| Arquivos RAW ausentes | 0 |
| Arquivos com checksum verificado | 399 |
| Divergências de checksum RAW | 0 |

### Registros `failed` da RAW

A RAW preserva falhas históricas por rastreabilidade.

A Silver não trata essas falhas como erro fatal.

Regra:

- registros RAW com `status = failed` são aceitos;
- arquivos locais existentes são validados;
- ausência de arquivo em registro histórico de falha não derruba a execução.

## Validações Silver criadas

### `silver_summary_by_planet.csv`

Caminho:

```text
data/silver/validation/silver_summary_by_planet.csv
```

Linhas:

```text
8
```

Resumo por planeta:

- linhas NASA `pscomppars`;
- linhas NASA `ps`;
- quantidade de FITS MAST;
- quantidade de linhas de curvas MAST;
- missões disponíveis;
- quantidade de JSONs Exo.MAST;
- observações ETD;
- curvas JSON ETD;
- pontos ETD.

### `silver_mast_quality_summary.csv`

Caminho:

```text
data/silver/validation/silver_mast_quality_summary.csv
```

Linhas:

```text
10
```

Resumo por planeta e missão:

- FITS processados;
- linhas extraídas;
- linhas com `quality == 0`;
- linhas com `quality != 0`;
- linhas com qualidade ausente;
- contagens não nulas de `PDCSAP_FLUX`;
- contagens não nulas de `SAP_FLUX`;
- intervalo de tempo.

### `silver_etd_summary.csv`

Caminho:

```text
data/silver/validation/silver_etd_summary.csv
```

Linhas:

```text
8
```

Resumo por planeta:

- observações públicas;
- registros privados;
- curvas JSON;
- pontos fotométricos;
- filtros observados;
- DQI mínimo;
- DQI máximo.

### `silver_column_presence_report.csv`

Caminho:

```text
data/silver/validation/silver_column_presence_report.csv
```

Relatório de presença de colunas esperadas em:

- NASA;
- Exo.MAST;
- MAST metadata;
- ETD observações;
- ETD pontos;
- ETD metadata;
- colunas preferidas dos FITS.

## Reprodutibilidade

A Silver é reprodutível porque:

1. Tem configuração versionável em `scripts/silver_data_config.py`.
2. Lê a RAW por manifesto.
3. Usa caminhos locais.
4. Não depende de rede.
5. Usa escrita atômica.
6. Calcula checksums.
7. Registra logs.
8. Gera manifesto próprio.
9. Preserva proveniência linha a linha.

## Como verificar manualmente

Executar:

```bash
python scripts/build_silver_data.py
```

Verificar existência:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/logs/build_silver_data.log
data/silver/validation/raw_manifest_validation.json
data/silver/validation/silver_summary_by_planet.csv
```

Verificar que a RAW não foi alterada:

```text
Comparar checksums de data/raw antes e depois da execução.
```

Na execução validada, a comparação não apresentou diferenças.

## Interpretação metodológica

Essa etapa demonstra controle de qualidade inicial.

Ela documenta:

- quais arquivos entraram no processamento;
- como a integridade foi conferida;
- quais tabelas foram geradas;
- quais limitações permanecem;
- por que a análise estatística ainda não começou.

Isso ajuda a separar claramente coleta, preparação e modelagem no TCC.

---

# Arquivo 8: `docs/silver/18_inventario_silver_por_planeta.md`

```text
Origem: docs/silver/18_inventario_silver_por_planeta.md
```

# 18. Inventário Silver por Planeta

## Objetivo deste documento

Este documento resume a disponibilidade de dados Silver por planeta.

Ele responde:

- quais planetas possuem NASA consolidada;
- quais planetas possuem Exo.MAST tabularizado;
- quais planetas possuem curvas MAST tabulares;
- quais missões aparecem por planeta;
- quantas observações ETD foram consolidadas;
- quantos pontos fotométricos ETD foram extraídos.

## Resumo geral

| Planeta | NASA `pscomppars` | NASA `ps` | FITS MAST | Linhas MAST | Missões MAST | Exo.MAST JSONs | Obs. ETD | Curvas ETD | Pontos ETD |
|---|---:|---:|---:|---:|---|---:|---:|---:|---:|
| HAT-P-7 b | 1 | 24 | 6 | 64.872 | Kepler, TESS | 4 | 60 | 5 | 1.243 |
| TrES-2 b | 1 | 34 | 6 | 63.836 | Kepler, TESS | 4 | 371 | 5 | 1.180 |
| HD 189733 b | 1 | 21 | 3 | 57.213 | TESS | 3 | 218 | 5 | 1.262 |
| HD 209458 b | 1 | 23 | 3 | 159.179 | TESS | 3 | 92 | 5 | 1.625 |
| WASP-12 b | 1 | 19 | 3 | 54.224 | TESS | 3 | 376 | 5 | 793 |
| WASP-10 b | 1 | 11 | 3 | 145.851 | TESS | 3 | 241 | 5 | 322 |
| WASP-4 b | 1 | 22 | 3 | 56.783 | TESS | 3 | 80 | 5 | 1.039 |
| HAT-P-32 b | 1 | 13 | 3 | 140.907 | TESS | 3 | 212 | 5 | 1.288 |

## HAT-P-7 b

Slug:

```text
hat_p_7_b
```

Estrela:

```text
HAT-P-7
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 24 linhas.

Exo.MAST:

- 4 JSONs tabularizados;
- inclui TCEs Kepler e TESS.

### MAST

Arquivos:

```text
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/hat_p_7_b/tess_lightcurve.csv
```

Resultados:

- FITS: 6;
- linhas MAST: 64.872;
- missões: Kepler e TESS.

### ETD

- observações: 60;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.243;
- filtros/bandas: `Clear`, `R`, `SLOAN 'r`, `V to IR`;
- registros privados: 0.

### Comentário

É o candidato principal inicial do projeto. Tem boa vantagem metodológica por combinar Kepler, TESS e ETD.

## TrES-2 b

Slug:

```text
tres_2_b
```

Estrela:

```text
TrES-2
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 34 linhas.

Exo.MAST:

- 4 JSONs tabularizados;
- inclui TCEs Kepler e TESS.

### MAST

Arquivos:

```text
data/silver/lightcurves/mast/tres_2_b/kepler_lightcurve.csv
data/silver/lightcurves/mast/tres_2_b/tess_lightcurve.csv
```

Resultados:

- FITS: 6;
- linhas MAST: 63.836;
- missões: Kepler e TESS.

### ETD

- observações: 371;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.180;
- filtros/bandas: `Clear`, `L`, `R`, `clear`, `r`;
- registros privados: 0.

### Comentário

É um candidato forte para Gold pela presença de Kepler e TESS, além de grande volume de observações ETD.

## HD 189733 b

Slug:

```text
hd_189733_b
```

Estrela:

```text
HD 189733
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 21 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hd_189733_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 57.213;
- missão: TESS.

### ETD

- observações: 218;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.262;
- filtros/bandas: `Clear`, `R`, `i`;
- registros privados: 0.

## HD 209458 b

Slug:

```text
hd_209458_b
```

Estrela:

```text
HD 209458
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 23 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hd_209458_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 159.179;
- missão: TESS.

### ETD

- observações: 92;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.625;
- filtros/bandas: `Clear`, `I`, `R`;
- registros privados: 0.

## WASP-12 b

Slug:

```text
wasp_12_b
```

Estrela:

```text
WASP-12
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 19 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_12_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 54.224;
- missão: TESS.

### ETD

- observações: 376;
- curvas JSON públicas: 5;
- pontos fotométricos: 793;
- filtros/bandas: `CBB`, `Clear`, `Luminance`, `R`, `V to IR`;
- registros privados: 0.

## WASP-10 b

Slug:

```text
wasp_10_b
```

Estrela:

```text
WASP-10
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 11 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_10_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 145.851;
- missão: TESS.

### ETD

- observações: 241;
- curvas JSON públicas: 5;
- pontos fotométricos: 322;
- filtros/bandas: `Clear`, `IR-UV`, `L`, `R`;
- registros privados: 0.

## WASP-4 b

Slug:

```text
wasp_4_b
```

Estrela:

```text
WASP-4
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 22 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/wasp_4_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 56.783;
- missão: TESS.

### ETD

- observações: 80;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.039;
- filtros/bandas: `Clear`, `Luminance`, `V`;
- registros privados: 0.

## HAT-P-32 b

Slug:

```text
hat_p_32_b
```

Estrela:

```text
HAT-P-32
```

### Catálogos

NASA:

- `pscomppars`: 1 linha;
- `ps`: 13 linhas.

Exo.MAST:

- 3 JSONs tabularizados.

### MAST

Arquivo:

```text
data/silver/lightcurves/mast/hat_p_32_b/tess_lightcurve.csv
```

Resultados:

- FITS: 3;
- linhas MAST: 140.907;
- missão: TESS.

### ETD

- observações: 212;
- curvas JSON públicas: 5;
- pontos fotométricos: 1.288;
- filtros/bandas: `CV`, `IR`, `Sloan r'`, `V`, `r`;
- registros privados: 0.

## Conclusão do inventário

Todos os planetas possuem:

- NASA `pscomppars`;
- NASA `ps`;
- Exo.MAST tabularizado;
- TESS tabularizado;
- ETD observações;
- ETD pontos fotométricos.

Somente HAT-P-7 b e TrES-2 b possuem Kepler na Silver.

Nenhum planeta possui K2 na Silver.

Para Gold, a disponibilidade favorece HAT-P-7 b e TrES-2 b, com preferência inicial para HAT-P-7 b por alinhamento com o escopo definido do projeto.

---

# Arquivo 9: `docs/silver/19_dicionario_de_arquivos_e_campos_silver.md`

```text
Origem: docs/silver/19_dicionario_de_arquivos_e_campos_silver.md
```

# 19. Dicionário de Arquivos e Campos da Camada Silver

## Objetivo deste documento

Este documento funciona como mapa de localização da camada Silver.

Ele responde:

- onde cada arquivo Silver está;
- que informação cada arquivo contém;
- quais campos principais existem;
- quais campos preservam proveniência;
- como cada tabela deve ser interpretada.

## Manifesto Silver

### Caminho

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

### Conteúdo

Registra todos os artefatos Silver criados na execução.

### Campos principais

| Campo | Descrição |
|---|---|
| `created_at_utc` | Data UTC do registro |
| `silver_layer` | Nome da camada |
| `source_raw_manifest_path` | Manifesto RAW usado |
| `source_raw_path` | Arquivo RAW de origem |
| `source_name` | Fonte |
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `mission` | Missão |
| `raw_file_type` | Tipo RAW |
| `silver_file_path` | Caminho Silver |
| `silver_file_name` | Nome Silver |
| `silver_file_type` | Tipo Silver |
| `transformation_type` | Transformação |
| `row_count` | Linhas |
| `column_count` | Colunas |
| `status` | Status |
| `error_message` | Erro |
| `sha256` | Checksum Silver |
| `file_size_bytes` | Tamanho |
| `notes` | Notas |

## NASA `pscomppars_selected_planets.csv`

### Caminho

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
```

### Conteúdo

Uma linha por planeta configurado, com parâmetros compostos NASA.

### Campos científicos

| Campo | Descrição |
|---|---|
| `planet_name` | Nome do planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug do planeta |
| `discovery_method` | Método de descoberta |
| `discovery_facility` | Instalação de descoberta |
| `orbital_period_days` | Período orbital em dias |
| `orbital_period_err_plus` | Erro superior do período |
| `orbital_period_err_minus` | Erro inferior do período |
| `transit_midpoint` | Meio do trânsito |
| `transit_midpoint_err_plus` | Erro superior do meio do trânsito |
| `transit_midpoint_err_minus` | Erro inferior do meio do trânsito |
| `transit_duration_hours` | Duração do trânsito |
| `transit_duration_err_plus` | Erro superior da duração |
| `transit_duration_err_minus` | Erro inferior da duração |
| `transit_depth` | Profundidade do trânsito |
| `transit_depth_err_plus` | Erro superior da profundidade |
| `transit_depth_err_minus` | Erro inferior da profundidade |
| `planet_radius_earth` | Raio planetário em raios terrestres |
| `planet_radius_earth_err_plus` | Erro superior do raio terrestre |
| `planet_radius_earth_err_minus` | Erro inferior do raio terrestre |
| `planet_radius_jupiter` | Raio planetário em raios de Júpiter |
| `stellar_radius_solar` | Raio estelar em raios solares |
| `stellar_radius_solar_err_plus` | Erro superior do raio estelar |
| `stellar_radius_solar_err_minus` | Erro inferior do raio estelar |
| `stellar_teff` | Temperatura efetiva estelar |
| `stellar_mass_solar` | Massa estelar |
| `system_distance_pc` | Distância do sistema em parsecs |

### Campos de origem

| Campo | Descrição |
|---|---|
| `source_name` | Fonte |
| `source_raw_path` | CSV RAW usado |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do arquivo RAW |
| `silver_created_at_utc` | Data UTC de criação |

## NASA `ps_all_solutions.csv`

### Caminho

```text
data/silver/catalogs/nasa/ps_all_solutions.csv
```

### Conteúdo

Todas as linhas NASA `ps` por planeta.

### Campos adicionados

| Campo | Descrição |
|---|---|
| `planet_name` | Nome padronizado |
| `host_star` | Estrela padronizada |
| `planet_slug` | Slug |
| `solution_row_index` | Índice da solução dentro do CSV RAW |
| `source_name` | Fonte |
| `source_raw_path` | Arquivo RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome RAW |
| `silver_created_at_utc` | Data UTC de criação |

As demais colunas são preservadas da tabela NASA `ps`.

## NASA snapshot geral

### Caminho

```text
data/silver/catalogs/nasa/all_transiting_planets_snapshot.csv
```

### Conteúdo

Snapshot de planetas em trânsito com proveniência Silver.

### Uso

Contexto e exploração. Não é Gold.

## Exo.MAST

### Caminhos

```text
data/silver/catalogs/exomast/exomast_identifiers.csv
data/silver/catalogs/exomast/exomast_properties.csv
data/silver/catalogs/exomast/exomast_tces.csv
```

### Campos obrigatórios

| Campo | Descrição |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `exomast_file_type` | Tipo do JSON |
| `source_name` | Fonte |
| `source_raw_path` | Arquivo RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome RAW |
| `raw_metadata_json` | JSON original compacto |
| `silver_created_at_utc` | Data UTC |

As demais colunas vêm do flattening do JSON.

## MAST lightcurves

### Caminho por planeta e missão

```text
data/silver/lightcurves/mast/{planet_slug}/{mission}_lightcurve.csv
```

### Campos principais

| Campo | Descrição |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela |
| `planet_slug` | Slug |
| `source_name` | Fonte |
| `source_raw_path` | FITS RAW |
| `source_raw_sha256` | Checksum RAW |
| `source_raw_file_name` | Nome do FITS |
| `mission` | Missão |
| `source_fits_file` | Nome do FITS |
| `hdu_name` | Nome da HDU |
| `hdu_index` | Índice da HDU |
| `time` | Tempo fornecido pelo FITS |
| `time_unit` | Unidade de tempo |
| `time_reference` | Referência temporal |
| `sap_flux` | SAP_FLUX |
| `sap_flux_err` | SAP_FLUX_ERR |
| `pdcsap_flux` | PDCSAP_FLUX |
| `pdcsap_flux_err` | PDCSAP_FLUX_ERR |
| `quality` | QUALITY ou SAP_QUALITY |
| `cadence_number` | CADENCENO |
| `mom_centr1` | Centroide |
| `mom_centr2` | Centroide |
| `pos_corr1` | Correção de posição |
| `pos_corr2` | Correção de posição |
| `quarter` | Quarter Kepler |
| `sector` | Setor TESS |
| `campaign` | Campanha K2, se existisse |
| `camera` | Câmera |
| `ccd` | CCD |
| `object` | Objeto no header |
| `telescope` | Telescópio |
| `instrument` | Instrumento |
| `data_origin` | Autor ou criador do produto |
| `quality_is_zero` | Flag auxiliar |
| `quality_is_missing` | Flag auxiliar |
| `has_pdcsap_flux` | Presença de PDCSAP |
| `has_sap_flux` | Presença de SAP |
| `silver_created_at_utc` | Data UTC |

## MAST metadata

### Caminho

```text
data/silver/lightcurves/mast/mast_fits_metadata.csv
```

### Conteúdo

Uma linha por FITS.

Campos:

- identificação;
- proveniência;
- tamanho;
- checksum;
- HDUs;
- colunas disponíveis;
- colunas ausentes;
- intervalo de tempo;
- contagens de qualidade;
- status da extração.

## ETD observations

### Caminho

```text
data/silver/etd/etd_observations.csv
```

### Conteúdo

Observações públicas de trânsito.

Campos principais:

- `obs_id`;
- `trans_id`;
- `epoch`;
- `hjd_mid`;
- `jd_mid_err`;
- `duration`;
- `duration_err`;
- `depth`;
- `depth_err`;
- `dqi`;
- `band`;
- `observer`;
- `reference`;
- `reference_url`;
- `data_version`;
- `is_private`;
- `raw_metadata_json`.

## ETD points

### Caminho

```text
data/silver/etd/etd_lightcurve_points.csv
```

### Conteúdo

Pontos fotométricos das curvas públicas.

Campos principais:

- `obs_id`;
- `trans_id`;
- `point_index`;
- `jd`;
- `mag`;
- `mag_error`;
- `filter`;
- `airmass`;
- `mag_band`;
- `source_json_file`.

## ETD metadata

### Caminho

```text
data/silver/etd/etd_lightcurve_metadata.csv
```

### Conteúdo

Uma linha por JSON de curva.

Campos principais:

- `point_count`;
- `has_photometry`;
- `has_airmass`;
- `has_minimas`;
- `has_transits`;
- `mag_band`;
- `time_span`;
- `orig_raw_header_present`;
- `status`;
- `error_message`.

## Validações

### Caminhos

```text
data/silver/validation/raw_manifest_summary.csv
data/silver/validation/raw_manifest_validation.json
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/validation/silver_etd_summary.csv
data/silver/validation/silver_column_presence_report.csv
```

### Uso

Esses arquivos são a base para:

- auditoria;
- inventário;
- comparação entre planetas;
- seleção futura de Gold;
- descrição metodológica.

---

# Arquivo 10: `docs/silver/20_como_usar_silver_na_metodologia.md`

```text
Origem: docs/silver/20_como_usar_silver_na_metodologia.md
```

# 20. Como Usar a Camada Silver na Metodologia

## Objetivo deste documento

Este documento organiza a implementação da Silver em linguagem útil para a futura seção de metodologia do TCC.

Não é o texto final do TCC.

É uma base técnica para explicar:

- como os dados foram preparados;
- como a rastreabilidade foi preservada;
- como a validação foi feita;
- por que a modelagem ainda não aparece nesta etapa.

## Ideia metodológica central

A camada Silver foi construída como etapa intermediária entre coleta bruta e análise final.

Ela transforma dados públicos heterogêneos em tabelas padronizadas, sem alterar o significado científico dos dados observacionais.

Essa separação ajuda a demonstrar que a futura inferência bayesiana será aplicada sobre uma base rastreável e auditável.

## Como descrever a entrada da Silver

A entrada primária foi:

```text
data/raw/_manifests/raw_data_manifest.csv
```

Esse manifesto registra:

- fonte;
- URL ou origem;
- planeta;
- estrela;
- caminho local;
- tipo de arquivo;
- missão;
- produto;
- status;
- checksum;
- tamanho.

Na metodologia, isso pode ser descrito como um controle de proveniência da camada bruta.

## Como descrever a validação inicial

Antes de transformar dados, a Silver validou a RAW.

Foram conferidos:

- existência do manifesto RAW;
- existência dos arquivos locais registrados;
- checksums SHA256;
- contagens por fonte;
- contagens por status;
- contagens por produto;
- contagens por planeta.

Resultado:

- 749 registros no manifesto RAW;
- 399 arquivos locais únicos validados;
- 0 arquivos ausentes;
- 0 divergências de checksum.

Isso sustenta a afirmação de que a camada Silver foi construída a partir de uma RAW íntegra.

## Como descrever NASA

Os CSVs do NASA Exoplanet Archive foram usados para consolidar parâmetros planetários e estelares.

Tabelas usadas:

- `pscomppars`;
- `ps`;
- snapshot geral de planetas em trânsito.

Na Silver:

- `pscomppars` foi padronizada para uma linha por planeta;
- `ps` foi preservada com múltiplas soluções por planeta;
- o snapshot geral foi mantido como contexto.

Decisão importante:

```text
Nenhuma solução da tabela ps foi escolhida como definitiva na Silver.
```

Essa decisão evita antecipar uma escolha científica que pertence à etapa Gold ou à análise.

## Como descrever Exo.MAST

Os JSONs Exo.MAST foram transformados em tabelas por flattening.

Como os esquemas variam, foi preservado:

```text
raw_metadata_json
```

Esse campo permite rastrear o conteúdo original do JSON mesmo quando a estrutura tabular fica incompleta ou muito heterogênea.

Isso pode ser descrito como estratégia conservadora de tabularização.

## Como descrever MAST

Os FITS do MAST foram abertos com `astropy.io.fits`.

Para cada FITS:

1. a HDU tabular de curva de luz foi identificada;
2. colunas preferidas foram extraídas quando presentes;
3. colunas ausentes foram mantidas como ausentes;
4. metadados do header foram registrados;
5. cada linha manteve o caminho do FITS original.

Ponto metodológico essencial:

```text
As flags de qualidade foram preservadas, mas não filtradas.
```

Isso permite que a futura Gold decida critérios de qualidade explicitamente.

## Como descrever ETD

O ETD foi consolidado em duas dimensões:

1. observações de trânsito;
2. pontos fotométricos de curvas públicas.

Foram preservados:

- IDs de observação;
- IDs de trânsito;
- época;
- meio do trânsito;
- duração;
- profundidade;
- DQI;
- filtro;
- observador;
- JSON original compacto.

Ponto metodológico essencial:

```text
As magnitudes foram mantidas como magnitudes. Não houve conversão para fluxo.
```

Isso evita introduzir transformação física antes da definição da Gold.

## Como descrever proveniência

Toda tabela Silver inclui, quando aplicável:

- `planet_name`;
- `host_star`;
- `planet_slug`;
- `source_name`;
- `source_raw_path`;
- `source_raw_sha256`;
- `source_raw_file_name`;
- `silver_created_at_utc`.

Essa estrutura permite rastrear:

```text
linha Silver -> arquivo RAW -> fonte pública original
```

## Como descrever validações finais

Após gerar as tabelas, a Silver criou relatórios:

- resumo por planeta;
- resumo de qualidade MAST;
- resumo ETD;
- presença de colunas.

Esses relatórios permitem justificar a futura escolha do planeta Gold.

## Como justificar HAT-P-7 b e TrES-2 b

Com base apenas na disponibilidade Silver:

- HAT-P-7 b possui Kepler, TESS, NASA, Exo.MAST e ETD;
- TrES-2 b possui Kepler, TESS, NASA, Exo.MAST e ETD;
- os demais planetas possuem TESS, NASA, Exo.MAST e ETD, mas não Kepler;
- nenhum planeta possui K2.

Assim, HAT-P-7 b e TrES-2 b são candidatos fortes para Gold.

HAT-P-7 b permanece como candidato principal inicial do projeto.

## Frases técnicas úteis para metodologia

As frases abaixo são rascunhos técnicos, não texto final.

### Sobre arquitetura

```text
Os dados foram organizados em uma arquitetura local de datalake, com separação explícita entre camada bruta e camada padronizada.
```

### Sobre RAW

```text
A camada RAW preservou os arquivos públicos conforme coletados, incluindo CSVs, JSONs, HTMLs e FITS, acompanhados de manifesto, logs e checksums.
```

### Sobre Silver

```text
A camada Silver foi construída exclusivamente a partir da RAW, sem novos downloads, com o objetivo de padronizar identificadores, tabularizar curvas de luz e consolidar metadados observacionais.
```

### Sobre integridade

```text
Antes da transformação, o manifesto RAW foi validado por existência de arquivos e comparação de checksums SHA256.
```

### Sobre curvas FITS

```text
Os arquivos FITS do MAST foram lidos com astropy.io.fits, preservando valores de tempo, fluxo e flags de qualidade, sem normalização ou filtragem.
```

### Sobre ETD

```text
As curvas terrestres do ETD foram mantidas em magnitude, sem conversão para fluxo, preservando metadados de observação, filtro e DQI.
```

### Sobre limites

```text
A camada Silver não executou modelagem, inferência bayesiana, faseamento orbital ou remoção de outliers; tais decisões foram reservadas para etapas posteriores.
```

## O que não afirmar

Evitar afirmar que:

- a Silver produziu dataset final de modelagem;
- as curvas já estão limpas;
- os fluxos já estão normalizados;
- os dados ETD são os arquivos originais dos observadores;
- uma solução NASA foi escolhida como definitiva;
- HAT-P-7 b foi definitivamente escolhido como Gold.

## Próximos passos metodológicos

Para a Gold, a metodologia poderá descrever:

1. escolha de planeta;
2. escolha de missão;
3. seleção de curvas;
4. critério de qualidade;
5. normalização;
6. faseamento;
7. tratamento de incertezas;
8. modelo físico de trânsito;
9. especificação bayesiana;
10. diagnóstico posterior.

Esses passos ainda não foram implementados.

---
