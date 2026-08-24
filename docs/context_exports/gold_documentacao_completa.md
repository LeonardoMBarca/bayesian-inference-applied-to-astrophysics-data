# Documentacao Completa Gold
> Snapshot histórico gerado antes do hardening de 2026-08-24. Não descreve automaticamente o pipeline atual.

Documento consolidado para uso como contexto em GPT.
- Gerado em UTC: `2026-06-16T15:47:14+00:00`
- Pasta de origem: `docs/gold`
- Observacao: este arquivo e apenas uma exportacao consolidada; os documentos originais nao foram removidos nem alterados.
- Uso sugerido: copiar este Markdown como contexto quando precisar discutir esta etapa especifica do TCC.

## Arquivos Incluidos
1. `docs/gold/README.md`
2. `docs/gold/21_contexto_escopo_e_regras_gold.md`
3. `docs/gold/22_selecao_candidato_gold.md`
4. `docs/gold/23_pipeline_gold_e_codigo.md`
5. `docs/gold/24_catalogo_parametros_referencia.md`
6. `docs/gold/25_curvas_gold_e_preparacao_modelagem.md`
7. `docs/gold/26_manifestos_logs_validacoes_gold.md`
8. `docs/gold/27_dicionario_de_arquivos_e_campos_gold.md`
9. `docs/gold/28_como_usar_gold_na_metodologia.md`

---

# Arquivo 1: `docs/gold/README.md`

```text
Origem: docs/gold/README.md
```

# Documentação Gold

Esta pasta documenta a camada **Gold inicial** do datalake local do TCC.

A Gold foi construída a partir da Silver, sem modificar a RAW e sem modificar a
Silver. O objetivo foi selecionar um candidato principal e preparar um dataset
analítico inicial para uma futura modelagem bayesiana de trânsito.

No estado atual do projeto, a Gold não contém inferência bayesiana. Ela contém
apenas seleção, organização, filtros técnicos explícitos, faseamento e uma
janela de trânsito pronta para inspeção e modelagem posterior.

## Como Ler

Os arquivos estão numerados em ordem sugerida:

1. [21_contexto_escopo_e_regras_gold.md](21_contexto_escopo_e_regras_gold.md)  
   Explica o papel da Gold, a relação com RAW/Silver e o que foi ou não feito.

2. [22_selecao_candidato_gold.md](22_selecao_candidato_gold.md)  
   Documenta o scorecard, os critérios de pontuação, a escolha de HAT-P-7 b e a missão Kepler.

3. [23_pipeline_gold_e_codigo.md](23_pipeline_gold_e_codigo.md)  
   Mapeia scripts, módulos, configuração, comandos e fluxo de execução da Gold.

4. [24_catalogo_parametros_referencia.md](24_catalogo_parametros_referencia.md)  
   Descreve o catálogo Gold de parâmetros de referência do planeta selecionado.

5. [25_curvas_gold_e_preparacao_modelagem.md](25_curvas_gold_e_preparacao_modelagem.md)  
   Explica a curva primária, filtro por qualidade, fase orbital e janela de trânsito.

6. [26_manifestos_logs_validacoes_gold.md](26_manifestos_logs_validacoes_gold.md)  
   Documenta manifesto, logs, checksums, validações e evidências de reprodutibilidade.

7. [27_dicionario_de_arquivos_e_campos_gold.md](27_dicionario_de_arquivos_e_campos_gold.md)  
   Mapeia onde está cada informação da Gold e o significado dos campos principais.

8. [28_como_usar_gold_na_metodologia.md](28_como_usar_gold_na_metodologia.md)  
   Organiza a Gold em linguagem útil para a futura seção de metodologia do TCC.

## Saída Principal

```text
data/gold/
```

## Comandos

Pipeline Gold completo:

```bash
python scripts/build_gold_data.py
```

Somente seleção:

```bash
python scripts/build_gold_selection_report.py
```

## Resultado Principal

- Planeta selecionado: `HAT-P-7 b`
- Estrela hospedeira: `HAT-P-7`
- Slug: `hat_p_7_b`
- Missão selecionada: `Kepler`
- Fluxo usado: `pdcsap_flux`
- Erro usado: `pdcsap_flux_err`
- Curva primária: `6.163` linhas
- Curva filtrada por qualidade: `3.909` linhas
- Curva faseada: `3.909` linhas
- Janela de trânsito Gold inicial: `1.664` linhas
- Meia largura da janela inicial: aproximadamente `0,48527` dias

## Arquivo Principal Para Modelagem Futura

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Esse arquivo é a entrada Gold inicial para a próxima etapa, mas a EDA posterior
recomendou usar, dentro dele, uma janela preliminar mais estreita:

```python
abs(phase) <= 0.15
```

Essa recomendação pertence à etapa EDA, documentada separadamente em:

```text
docs/eda/gold_hat_p_7_b/
```

## O Que a Gold Não Faz

A Gold não executa:

- inferência bayesiana;
- posterior sampling;
- PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- ajuste físico de trânsito;
- comparação com literatura;
- gráficos finais do TCC.

Ela apenas prepara uma base analítica mínima, rastreável e reproduzível.

---

# Arquivo 2: `docs/gold/21_contexto_escopo_e_regras_gold.md`

```text
Origem: docs/gold/21_contexto_escopo_e_regras_gold.md
```

# 21 - Contexto, Escopo e Regras da Gold

## 1. Contexto Acadêmico

O projeto de TCC se chama:

```text
Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional
```

O objetivo geral é investigar como inferência bayesiana pode ser aplicada à
estimação de parâmetros físicos em sistemas astrofísicos sob incerteza
observacional, com ênfase em curvas de luz de trânsitos de exoplanetas.

A arquitetura de dados foi construída em camadas:

- **RAW**: dados públicos preservados como coletados;
- **Silver**: dados validados, padronizados, tabulares e auditáveis;
- **Gold**: dataset analítico inicial para modelagem bayesiana futura.

Este documento descreve a terceira camada, a **Gold inicial**.

## 2. Papel da Gold no Projeto

A Gold existe para fazer a ponte entre uma camada Silver ampla, ainda
multi-planeta e multi-fonte, e uma etapa futura de modelagem bayesiana focada
em um alvo específico.

A Silver preserva uma base mais larga:

- vários planetas;
- múltiplas missões;
- NASA Exoplanet Archive;
- MAST/Lightkurve;
- Exo.MAST;
- ETD/VarAstro;
- catálogos;
- curvas espaciais;
- curvas terrestres;
- validações por planeta.

A Gold inicial reduz esse universo para um caso analítico controlado:

- escolhe um planeta;
- escolhe uma missão principal;
- escolhe uma coluna de fluxo;
- mantém uma coluna de incerteza associada;
- aplica um filtro técnico simples de qualidade;
- cria fase orbital;
- seleciona uma janela em torno do trânsito;
- registra a decisão em manifestos, logs e relatórios.

## 3. Entradas da Gold

A Gold lê exclusivamente arquivos da Silver:

```text
data/silver/
```

As principais entradas são:

```text
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/exomast/exomast_tces.csv
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_metadata.csv
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
```

A Gold não lê a internet, não baixa novos dados e não consulta APIs externas.

## 4. Saídas da Gold

A Gold escreve exclusivamente em:

```text
data/gold/
```

Os principais grupos de saída são:

- seleção do candidato Gold;
- catálogo de parâmetros de referência;
- curva primária;
- curva filtrada por qualidade;
- curva faseada;
- janela de trânsito;
- validações;
- manifesto;
- log;
- documentação técnica gerada pela execução.

## 5. Imutabilidade das Camadas Anteriores

A construção da Gold respeita a imutabilidade das camadas anteriores:

- não altera `data/raw/`;
- não altera `data/silver/`;
- não reprocessa arquivos RAW diretamente;
- não sobrescreve produtos Silver;
- não baixa dados externos;
- não cria dados sintéticos.

A Gold é uma camada derivada. Se for necessário reconstruí-la, ela deve ser
reexecutada a partir da Silver, não editada manualmente como fonte primária.

## 6. O Que Foi Feito

Foram implementadas as seguintes operações:

1. Leitura de resumos Silver por planeta.
2. Construção de scorecard de candidatos.
3. Seleção do planeta Gold inicial.
4. Seleção da missão principal.
5. Seleção da coluna de fluxo preferencial.
6. Seleção da coluna de erro do fluxo.
7. Criação de catálogo Gold com parâmetros de referência.
8. Criação da curva primária.
9. Remoção de linhas sem `time`.
10. Remoção de linhas sem fluxo.
11. Filtro técnico por `quality == 0`.
12. Conversão do tempo central de trânsito da NASA para a escala Kepler.
13. Criação de fase orbital.
14. Seleção de janela em torno da fase zero.
15. Criação de manifesto Gold com SHA256.
16. Criação de logs e validações.

## 7. O Que Não Foi Feito

Não foram feitos:

- inferência bayesiana;
- amostragem posterior;
- ajuste físico completo de trânsito;
- normalização científica final;
- escolha de priors;
- definição de likelihood final;
- modelagem com PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- comparação com literatura;
- gráficos finais para o TCC;
- seleção definitiva e irrevogável do dataset final da dissertação.

A Gold é uma preparação analítica inicial. A decisão de modelagem ainda depende
da EDA e dos diagnósticos posteriores.

## 8. Resultado da Execução Gold

O alvo selecionado foi:

```text
HAT-P-7 b
```

A missão escolhida foi:

```text
Kepler
```

A coluna de fluxo usada foi:

```text
pdcsap_flux
```

A coluna de erro usada foi:

```text
pdcsap_flux_err
```

Resumo numérico:

| Produto | Linhas |
|---|---:|
| Curva primária | 6.163 |
| Curva filtrada por qualidade | 3.909 |
| Curva faseada | 3.909 |
| Janela de trânsito | 1.664 |

## 9. Interpretação Correta da Gold

A Gold não deve ser interpretada como resultado científico final.

Ela deve ser interpretada como:

- uma seleção inicial rastreável;
- uma preparação analítica mínima;
- uma entrada organizada para EDA;
- uma base potencial para o primeiro modelo bayesiano.

A Gold permite que a modelagem futura comece a partir de um arquivo único,
mas ainda exige decisões adicionais sobre janela, normalização local, modelo
físico, priors, likelihood e diagnóstico posterior.

---

# Arquivo 3: `docs/gold/22_selecao_candidato_gold.md`

```text
Origem: docs/gold/22_selecao_candidato_gold.md
```

# 22 - Seleção do Candidato Gold

## 1. Objetivo da Seleção

A etapa de seleção Gold teve como objetivo escolher um planeta e uma missão
principal para a primeira análise bayesiana futura.

A seleção não foi feita manualmente apenas por preferência. Ela foi baseada em
um scorecard simples, explícito e reprodutível, construído a partir da Silver.

O objetivo do scorecard não é definir uma métrica astrofísica definitiva. Ele
serve para justificar de forma transparente por que um alvo é mais apropriado
para a primeira modelagem.

## 2. Fontes Silver Usadas

O scorecard leu os seguintes arquivos:

```text
data/silver/validation/silver_summary_by_planet.csv
data/silver/validation/silver_mast_quality_summary.csv
data/silver/lightcurves/mast/mast_fits_metadata.csv
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
data/silver/catalogs/exomast/exomast_tces.csv
data/silver/etd/etd_observations.csv
data/silver/etd/etd_lightcurve_metadata.csv
```

Esses arquivos já continham a consolidação da disponibilidade de dados por
planeta, missão e fonte.

## 3. Arquivos Gold Gerados Pela Seleção

Foram criados:

```text
data/gold/selection/gold_candidate_scorecard.csv
data/gold/selection/gold_candidate_report.md
data/gold/selection/selected_gold_target.json
```

O CSV é a versão tabular do scorecard.

O Markdown é a versão humana da justificativa.

O JSON é a decisão final em formato legível por máquina.

## 4. Critérios de Pontuação

A pontuação foi dividida em três blocos:

- disponibilidade;
- qualidade técnica;
- completude catalográfica.

### 4.1 Disponibilidade

Critérios:

- `+3` se possui Kepler;
- `+2` se possui TESS;
- `+1` se possui K2;
- `+1` se possui pelo menos 50.000 linhas MAST;
- `+1` se possui observações ETD.

Justificativa:

Kepler recebeu maior peso porque, para trânsitos de exoplanetas, fornece
séries temporais extensas, homogêneas e historicamente muito usadas. TESS é
igualmente relevante, mas neste projeto a primeira modelagem foi planejada
para começar com um alvo Kepler quando disponível.

### 4.2 Qualidade Técnica

Critérios:

- `+2` se `PDCSAP_FLUX` está disponível;
- `+1` se `SAP_FLUX` está disponível;
- `+3` se a razão `quality == 0` é pelo menos `0,80`;
- `+2` se a razão `quality == 0` é pelo menos `0,60`;
- `+1` se há qualquer linha com `quality == 0`;
- `-1` se mais de 30% das linhas têm `quality != 0`.

Justificativa:

`PDCSAP_FLUX` foi preferido por ser o fluxo corrigido pelo pipeline da missão,
mantendo-se ainda como dado observacional tabular derivado da missão, não como
resultado de modelagem bayesiana deste projeto.

O filtro por `quality == 0` é técnico: ele seleciona pontos sem flags de
qualidade instrumentais explícitas. Esse filtro não remove outliers por análise
estatística própria e não ajusta o trânsito.

### 4.3 Completude Catalográfica

Critérios:

- `+2` se há período orbital;
- `+2` se há tempo de meio trânsito;
- `+1` se há duração de trânsito;
- `+1` se há profundidade de trânsito.

Justificativa:

Esses parâmetros são necessários para preparar fase orbital e uma janela
inicial de trânsito. Sem período e tempo central, o faseamento não seria
defensável sem criar aproximações adicionais.

## 5. Resultado do Scorecard

Resumo dos candidatos principais:

| Planeta | Kepler | TESS | Score total | Papel recomendado |
|---|---:|---:|---:|---|
| TrES-2 b | sim | sim | 19 | backup_candidate |
| HAT-P-7 b | sim | sim | 19 | primary_candidate |
| HD 209458 b | não | sim | 16 | reference_only |
| WASP-10 b | não | sim | 16 | reference_only |
| HAT-P-32 b | não | sim | 16 | reference_only |
| HD 189733 b | não | sim | 16 | reference_only |
| WASP-12 b | não | sim | 16 | reference_only |
| WASP-4 b | não | sim | 16 | reference_only |

HAT-P-7 b e TrES-2 b empataram em score total, ambos com `19`.

## 6. Por Que HAT-P-7 b Foi Selecionado

A decisão final selecionou:

```text
HAT-P-7 b
```

Motivo registrado no JSON de seleção:

```text
HAT-P-7 b selected because it satisfies the default rule: Kepler available, PDCSAP flux available, orbital period available, and more than 1000 quality==0 rows.
```

Além do score, HAT-P-7 b já era o candidato principal inicial do projeto.
Como ele satisfez todos os critérios mínimos esperados, não houve necessidade
de acionar o backup TrES-2 b.

## 7. Papel de TrES-2 b

TrES-2 b permaneceu como backup forte.

Motivos:

- possui Kepler;
- possui TESS;
- possui `PDCSAP_FLUX`;
- possui bom volume de pontos com `quality == 0`;
- empatou com HAT-P-7 b em score total.

Se a EDA ou a modelagem futura mostrar problemas graves com HAT-P-7 b, TrES-2 b
é a alternativa natural.

## 8. Limitações do Scorecard

O scorecard é simples por desenho.

Ele não avalia:

- ruído correlacionado;
- systematics de longo prazo;
- profundidade real por ajuste físico;
- consistência com literatura;
- contaminação por estrelas próximas;
- sensibilidade de priors;
- qualidade de resíduos;
- evidência bayesiana;
- convergência de cadeias MCMC.

Esses pontos pertencem a etapas posteriores.

## 9. Como Citar na Metodologia

Na metodologia, a seleção pode ser descrita como uma triagem técnica
reprodutível baseada em:

- disponibilidade de missões;
- presença de fluxo corrigido;
- quantidade de pontos válidos por flags;
- presença de parâmetros orbitais mínimos;
- rastreabilidade por manifesto.

É importante deixar claro que o scorecard não é uma métrica astrofísica de
qualidade absoluta, mas um procedimento operacional para escolher o primeiro
alvo de modelagem.

---

# Arquivo 4: `docs/gold/23_pipeline_gold_e_codigo.md`

```text
Origem: docs/gold/23_pipeline_gold_e_codigo.md
```

# 23 - Pipeline Gold e Código

## 1. Objetivo do Pipeline

O pipeline Gold transforma a Silver em um dataset analítico inicial focado em
um planeta.

Ele foi desenhado para ser:

- local;
- reexecutável;
- sem dependência de rede;
- rastreável;
- conservador;
- explícito nas transformações;
- compatível com Python 3.12.

## 2. Comandos de Execução

Pipeline completo:

```bash
python scripts/build_gold_data.py
```

Somente relatório de seleção:

```bash
python scripts/build_gold_selection_report.py
```

No ambiente validado, quando `python` não estiver disponível diretamente:

```bash
.venv/bin/python scripts/build_gold_data.py
```

## 3. Configuração

Arquivo:

```text
scripts/gold_data_config.py
```

Principais parâmetros:

```text
SILVER_DATA_DIR = data/silver
GOLD_DATA_DIR = data/gold
PRIMARY_CANDIDATE = HAT-P-7 b
BACKUP_CANDIDATE = TrES-2 b
PREFERRED_MISSIONS = Kepler, TESS
EXPECTED_MISSIONS = Kepler, K2, TESS
PREFERRED_FLUX_COLUMN = pdcsap_flux
PREFERRED_FLUX_ERR_COLUMN = pdcsap_flux_err
FALLBACK_FLUX_COLUMN = sap_flux
FALLBACK_FLUX_ERR_COLUMN = sap_flux_err
QUALITY_GOOD_VALUE = 0
```

A configuração também registra a política de janela inicial:

```text
TRANSIT_WINDOW_DURATION_MULTIPLIER = 3.0
TRANSIT_WINDOW_MIN_HALF_WIDTH_DAYS = 0.2
```

No caso de HAT-P-7 b, a duração de trânsito levou a uma meia janela de
aproximadamente `0,48527` dias.

## 4. Scripts de Entrada

### 4.1 `scripts/build_gold_data.py`

Executa todas as etapas Gold:

- seleção;
- target Gold;
- validação;
- documentação gerada pela execução.

É o comando principal.

### 4.2 `scripts/build_gold_selection_report.py`

Executa apenas a etapa de seleção.

É útil quando se quer revisar o scorecard sem reconstruir todos os arquivos
do planeta selecionado.

## 5. Pacote `src/gold_processing`

Diretório:

```text
src/gold_processing/
```

Módulos principais:

```text
config.py
pipeline.py
selection.py
lightcurve_preparation.py
validation.py
manifests.py
utils.py
```

### 5.1 `pipeline.py`

Orquestra as etapas Gold.

Responsabilidades:

- criar diretórios;
- inicializar logging;
- chamar seleção;
- chamar preparação do alvo;
- chamar validações;
- escrever documentação gerada pela execução;
- registrar artefatos no manifesto.

### 5.2 `selection.py`

Constrói o scorecard dos planetas.

Responsabilidades:

- ler resumos Silver;
- calcular disponibilidade por missão;
- avaliar presença de fluxos;
- avaliar completude de parâmetros orbitais;
- atribuir score;
- definir papel recomendado;
- escrever `gold_candidate_scorecard.csv`;
- escrever `gold_candidate_report.md`;
- escrever `selected_gold_target.json`.

### 5.3 `lightcurve_preparation.py`

Cria os arquivos do planeta selecionado.

Responsabilidades:

- criar catálogo de referência;
- selecionar missão principal;
- selecionar coluna de fluxo;
- criar curva primária;
- aplicar filtro `quality == 0`;
- criar fase orbital;
- criar janela de trânsito;
- registrar warnings de tempo.

### 5.4 `validation.py`

Cria validações numéricas da Gold.

Responsabilidades:

- contar linhas;
- calcular intervalo de tempo;
- calcular estatísticas de fluxo;
- contar flags de qualidade;
- registrar parâmetros usados;
- escrever relatório de qualidade.

### 5.5 `manifests.py`

Gerencia o manifesto Gold.

Responsabilidades:

- criar linhas de manifesto;
- calcular SHA256;
- registrar tamanho dos arquivos;
- registrar status;
- escrever CSV e JSON.

### 5.6 `utils.py`

Funções utilitárias:

- escrita atômica;
- cálculo de SHA256;
- conversão de caminhos relativos;
- logging;
- leitura CSV;
- conversão numérica.

## 6. Fluxo de Execução

Fluxo conceitual:

```text
Silver summaries
  -> scorecard de candidatos
  -> decisão do alvo
  -> catálogo Gold
  -> curva primária
  -> filtro por qualidade
  -> fase orbital
  -> janela de trânsito
  -> validação
  -> manifesto/log/documentação
```

## 7. Regras de Escrita

A Gold escreve apenas em:

```text
data/gold/
```

Ela não escreve em:

```text
data/raw/
data/silver/
```

Como a Gold é derivada, seus artefatos podem ser reconstruídos por reexecução.
Mesmo assim, cada arquivo gerado é registrado no manifesto com checksum.

## 8. Resultado Esperado da Execução

Após executar o pipeline completo, espera-se encontrar:

```text
data/gold/selection/gold_candidate_scorecard.csv
data/gold/selection/gold_candidate_report.md
data/gold/selection/selected_gold_target.json
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
data/gold/hat_p_7_b/validation/gold_data_quality_report.md
data/gold/manifests/gold_data_manifest.csv
data/gold/logs/build_gold_data.log
```

## 9. Observação Sobre Documentação

Existe documentação gerada dentro da Gold:

```text
data/gold/hat_p_7_b/docs/README_gold.md
```

Ela é um artefato da execução.

A documentação metodológica e técnica organizada do repositório fica em:

```text
docs/gold/
```

---

# Arquivo 5: `docs/gold/24_catalogo_parametros_referencia.md`

```text
Origem: docs/gold/24_catalogo_parametros_referencia.md
```

# 24 - Catálogo Gold de Parâmetros de Referência

## 1. Objetivo

O catálogo de referência Gold reúne os parâmetros planetários e estelares
necessários para preparar a curva de luz de HAT-P-7 b para modelagem futura.

Ele é derivado da tabela Silver:

```text
data/silver/catalogs/nasa/pscomppars_selected_planets.csv
```

Essa tabela Silver, por sua vez, foi derivada da RAW NASA Exoplanet Archive:

```text
data/raw/nasa_exoplanet_archive/pscomppars/hat_p_7_b/response.csv
```

## 2. Arquivos Criados

Versão CSV:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
```

Versão JSON:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.json
```

A versão CSV é conveniente para leitura tabular.

A versão JSON é conveniente para uso programático em scripts ou notebooks.

## 3. Conteúdo

O catálogo possui uma linha para:

```text
HAT-P-7 b
```

Campos principais:

| Campo | Descrição |
|---|---|
| `planet_name` | Nome do planeta selecionado |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Identificador seguro para caminhos |
| `orbital_period_days` | Período orbital em dias |
| `transit_midpoint` | Tempo central de trânsito conforme catálogo NASA |
| `transit_duration_hours` | Duração de trânsito em horas |
| `transit_depth` | Profundidade catalográfica do trânsito |
| `planet_radius_earth` | Raio planetário em raios terrestres |
| `planet_radius_jupiter` | Raio planetário em raios de Júpiter |
| `stellar_radius_solar` | Raio estelar em raios solares |
| `stellar_mass_solar` | Massa estelar em massas solares |
| `stellar_teff` | Temperatura efetiva da estrela |
| `system_distance_pc` | Distância do sistema em parsecs |
| `source_raw_path` | Arquivo RAW de origem |
| `silver_source_path` | Arquivo Silver de origem |
| `gold_created_at_utc` | Data/hora UTC de criação da Gold |

## 4. Valores Registrados

Valores principais da execução:

| Parâmetro | Valor |
|---|---:|
| Período orbital | `2,20474` dias |
| Tempo central de trânsito NASA | `2454954,358572` |
| Duração de trânsito | `3,88216` horas |
| Profundidade catalográfica | `0,6` |
| Raio planetário | `16,92559` raios terrestres |
| Raio planetário | `1,51` raios de Júpiter |
| Raio estelar | `2,0` raios solares |
| Massa estelar | `1,56` massas solares |
| Temperatura efetiva | `6389 K` |
| Distância do sistema | `341,079 pc` |

## 5. Uso na Gold

O catálogo foi usado para:

- recuperar período orbital;
- recuperar tempo central de trânsito;
- recuperar duração de trânsito;
- criar a fase orbital;
- definir a largura inicial da janela de trânsito;
- documentar parâmetros físicos que serão necessários na modelagem futura.

## 6. Conversão de Tempo

O `transit_midpoint` veio do catálogo NASA em escala absoluta de data juliana
baricêntrica.

A curva Kepler usa tempo relativo com referência:

```text
BJDREFI = 2454833
BJDREFF = 0
```

Na Gold, o tempo central foi convertido para a escala da curva:

```text
transit_midpoint_used = transit_midpoint - (BJDREFI + BJDREFF)
```

Resultado usado:

```text
121.35857200017199
```

Esse valor aparece em:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

## 7. O Que Não Foi Feito

O catálogo Gold não:

- escolhe nova solução astrofísica;
- recalcula parâmetros físicos;
- compara com literatura;
- ajusta período orbital;
- ajusta época de trânsito;
- estima incertezas novas;
- preenche valores ausentes.

Ele apenas preserva, para o planeta selecionado, os parâmetros catalográficos
que já estavam consolidados na Silver.

---

# Arquivo 6: `docs/gold/25_curvas_gold_e_preparacao_modelagem.md`

```text
Origem: docs/gold/25_curvas_gold_e_preparacao_modelagem.md
```

# 25 - Curvas Gold e Preparação Para Modelagem

## 1. Objetivo

Este documento descreve como a Gold preparou as curvas de luz de HAT-P-7 b
para uma futura modelagem bayesiana.

A preparação é mínima e explícita. Ela não executa ajuste físico, inferência,
normalização final ou remoção estatística de outliers.

## 2. Entrada Silver

A curva principal veio de:

```text
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
```

Essa tabela Silver foi construída a partir de FITS Kepler baixados na RAW e
tabularizados na Silver.

## 3. Curva Primária Gold

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
```

Linhas:

```text
6.163
```

Colunas principais:

```text
planet_name
host_star
planet_slug
mission
time
flux
flux_err
flux_source
quality
quality_is_zero
cadence_number
source_silver_path
source_raw_path
source_fits_file
gold_created_at_utc
```

## 4. Seleção do Fluxo

A coluna preferida foi:

```text
pdcsap_flux
```

A coluna de erro preferida foi:

```text
pdcsap_flux_err
```

Na Gold, elas foram renomeadas para:

```text
flux
flux_err
```

O campo:

```text
flux_source
```

registra a origem do fluxo selecionado. Para esta execução:

```text
pdcsap_flux
```

## 5. Remoção de Linhas Sem Tempo ou Fluxo

A Gold removeu linhas sem `time` ou sem fluxo utilizável.

Resumo registrado no manifesto:

```text
Selected pdcsap_flux; removed 306 rows with missing time or flux.
```

Essa remoção é técnica. Ela evita linhas impossíveis de usar em qualquer modelo
temporal, mas não remove outliers e não altera valores de fluxo.

## 6. Curva Filtrada Por Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
```

Linhas:

```text
3.909
```

Critério:

```python
quality == 0
```

Resumo registrado no manifesto:

```text
Kept rows with quality == 0. rows_before=6163; rows_after=3909; removed=2254.
```

Esse filtro usa a flag técnica da missão. Ele não é uma detecção estatística de
outliers feita pelo projeto.

## 7. Curva Faseada

Arquivo:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
```

Linhas:

```text
3.909
```

Fórmula:

```python
phase = ((time - transit_midpoint_used + 0.5 * period) % period) - 0.5 * period
```

Parâmetros usados:

```text
period = 2.20474 dias
transit_midpoint_used = 121.35857200017199
```

Interpretação:

- `phase = 0` representa o centro esperado do trânsito;
- valores negativos ocorrem antes do centro do trânsito;
- valores positivos ocorrem depois do centro do trânsito;
- a unidade da fase neste arquivo é dias, não fração adimensional de ciclo.

## 8. Janela de Trânsito Gold Inicial

Arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas:

```text
1.664
```

Critério registrado:

```text
abs(phase) <= 0.48527000000000003
```

A largura veio da regra Gold:

```text
janela = max(3 * duração_em_dias, 0,2 dias)
```

Como a duração catalográfica foi:

```text
3,88216 horas = 0,1617566667 dias
```

Então:

```text
3 * 0,1617566667 = 0,48527 dias
```

## 9. Colunas da Janela de Trânsito

Campos principais:

```text
planet_name
host_star
planet_slug
mission
time
phase
flux
flux_err
quality
flux_source
orbital_period_days
transit_midpoint_used
phase_formula
source_gold_lightcurve
gold_created_at_utc
in_transit_window
transit_window_half_width_days
transit_duration_hours_used
```

## 10. O Que Ainda Precisa Ser Decidido

A Gold inicial ainda não decide:

- normalização final do fluxo;
- janela ótima para modelagem;
- modelo físico;
- priors;
- likelihood definitiva;
- tratamento de ruído correlacionado;
- estratégia de amostragem posterior.

A EDA posterior recomendou iniciar a modelagem com uma janela mais estreita:

```python
abs(phase) <= 0.15
```

Essa recomendação está documentada em:

```text
docs/eda/gold_hat_p_7_b/
```

## 11. Interpretação Correta

O arquivo `transit_window_lightcurve.csv` é uma base de trabalho.

Ele não é ainda o dataset final de inferência.

Ele deve ser usado como entrada para:

- inspeção visual;
- normalização local futura;
- testes de modelo simples;
- definição de priors;
- validação de likelihood.

---

# Arquivo 7: `docs/gold/26_manifestos_logs_validacoes_gold.md`

```text
Origem: docs/gold/26_manifestos_logs_validacoes_gold.md
```

# 26 - Manifestos, Logs e Validações Gold

## 1. Objetivo

A Gold mantém manifestos, logs e validações para garantir rastreabilidade.

Cada arquivo derivado da Gold deve poder ser associado a:

- fonte Silver;
- fonte RAW, quando aplicável;
- planeta;
- missão;
- transformação;
- quantidade de linhas;
- quantidade de colunas;
- status;
- tamanho;
- SHA256.

## 2. Manifesto Gold

Arquivos:

```text
data/gold/manifests/gold_data_manifest.csv
data/gold/manifests/gold_data_manifest.json
```

O manifesto possui `12` registros, todos com status:

```text
created
```

## 3. Colunas do Manifesto

Colunas:

```text
created_at_utc
gold_layer
planet_name
host_star
planet_slug
source_silver_path
source_raw_path
gold_file_path
gold_file_name
transformation_type
row_count
column_count
status
error_message
sha256
file_size_bytes
notes
```

## 4. Transformações Registradas

Transformações presentes:

```text
gold_candidate_scorecard
selected_gold_target
gold_candidate_report
gold_reference_parameters_csv
gold_reference_parameters_json
gold_primary_lightcurve
gold_primary_lightcurve_quality_filtered
gold_phase_folded_lightcurve
gold_transit_window_lightcurve
gold_lightcurve_summary
gold_data_quality_report
gold_readme
```

## 5. Checksums

Cada arquivo Gold criado tem SHA256 registrado no manifesto.

O checksum permite verificar se um arquivo derivado foi alterado após a
execução. Isso é importante porque a Gold é derivada, mas ainda precisa ser
auditável.

## 6. Log Gold

Arquivo:

```text
data/gold/logs/build_gold_data.log
```

O log registra:

- início da execução;
- etapas chamadas;
- arquivos criados;
- decisões de seleção;
- contagens de linhas;
- warnings de tempo;
- fim da execução.

## 7. Validação Numérica

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

Principais campos:

| Campo | Valor |
|---|---:|
| `rows_primary` | `6.163` |
| `rows_quality_filtered` | `3.909` |
| `rows_phase_folded` | `3.909` |
| `rows_transit_window` | `1.664` |
| `time_min` | `120,53881583872862` |
| `time_max` | `258,46743138637976` |
| `flux_min` | `1027023,6` |
| `flux_max` | `1041324,94` |
| `flux_median` | `1040914,9` |
| `flux_std` | `3530,9448155449695` |
| `flux_err_median` | `25,875484` |
| `quality_zero_count` | `3.909` |
| `quality_nonzero_count` | `2.254` |
| `period_used` | `2,20474` |
| `transit_midpoint_used` | `121,35857200017199` |
| `transit_duration_used` | `3,88216` |

## 8. Relatório de Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_data_quality_report.md
```

Esse relatório resume:

- planeta escolhido;
- missão;
- fonte de fluxo;
- linhas antes/depois do filtro;
- faseamento;
- janela de trânsito;
- warnings;
- recomendação para modelagem futura.

## 9. Warning Principal

Warning registrado:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.
```

Esse warning é esperado e importante. Ele documenta que o tempo central da NASA
foi convertido para a escala temporal da curva Kepler.

## 10. Reexecução

A Gold é derivada. Em caso de necessidade, ela pode ser reconstruída com:

```bash
python scripts/build_gold_data.py
```

Como ela é derivada, sobrescrever saídas Gold em uma reexecução é aceitável,
desde que:

- a RAW não seja alterada;
- a Silver não seja alterada;
- o manifesto seja atualizado;
- os logs registrem a execução.

## 11. Limitações das Validações

As validações Gold não avaliam:

- convergência de modelo;
- qualidade de ajuste físico;
- ruído correlacionado;
- evidência bayesiana;
- comparação com literatura;
- estabilidade de posterior.

Elas apenas conferem a coerência técnica dos artefatos preparados.

---

# Arquivo 8: `docs/gold/27_dicionario_de_arquivos_e_campos_gold.md`

```text
Origem: docs/gold/27_dicionario_de_arquivos_e_campos_gold.md
```

# 27 - Dicionário de Arquivos e Campos Gold

## 1. Objetivo

Este documento responde a duas perguntas práticas:

1. Onde está cada informação da Gold?
2. Como cada informação está estruturada?

## 2. Seleção Gold

### 2.1 `gold_candidate_scorecard.csv`

Caminho:

```text
data/gold/selection/gold_candidate_scorecard.csv
```

Uma linha por planeta candidato.

Campos principais:

| Campo | Significado |
|---|---|
| `planet_name` | Nome do planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug usado em caminhos |
| `has_kepler` | Indica se há dados Kepler |
| `has_tess` | Indica se há dados TESS |
| `has_k2` | Indica se há dados K2 |
| `kepler_fits_count` | Quantidade de FITS Kepler |
| `tess_fits_count` | Quantidade de FITS TESS |
| `total_mast_rows` | Total de linhas MAST na Silver |
| `total_quality_zero_rows` | Linhas com `quality == 0` |
| `total_quality_nonzero_rows` | Linhas com `quality != 0` |
| `pdcsap_flux_available` | Disponibilidade de `PDCSAP_FLUX` |
| `sap_flux_available` | Disponibilidade de `SAP_FLUX` |
| `orbital_period_available` | Presença de período orbital |
| `transit_midpoint_available` | Presença de tempo central |
| `transit_duration_available` | Presença de duração |
| `transit_depth_available` | Presença de profundidade |
| `etd_observation_count` | Observações ETD consolidadas |
| `etd_curve_count` | Curvas ETD públicas baixadas |
| `etd_photometry_points` | Pontos fotométricos ETD |
| `score_availability` | Pontuação de disponibilidade |
| `score_quality` | Pontuação de qualidade |
| `score_catalog_completeness` | Pontuação catalográfica |
| `score_total` | Soma das pontuações |
| `recommended_role` | Papel recomendado |
| `notes` | Justificativas compactas |

### 2.2 `selected_gold_target.json`

Caminho:

```text
data/gold/selection/selected_gold_target.json
```

Campos:

| Campo | Valor da execução |
|---|---|
| `selected_planet_name` | `HAT-P-7 b` |
| `selected_host_star` | `HAT-P-7` |
| `selected_planet_slug` | `hat_p_7_b` |
| `selected_primary_mission` | `Kepler` |
| `selected_flux_column` | `pdcsap_flux` |
| `selected_flux_err_column` | `pdcsap_flux_err` |
| `selection_reason` | Justificativa textual |
| `created_at_utc` | Data/hora UTC |

## 3. Catálogo de Referência

Arquivo:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
```

Uma linha para HAT-P-7 b.

Campos:

```text
planet_name
host_star
planet_slug
orbital_period_days
transit_midpoint
transit_duration_hours
transit_depth
planet_radius_earth
planet_radius_jupiter
stellar_radius_solar
stellar_mass_solar
stellar_teff
system_distance_pc
source_raw_path
silver_source_path
gold_created_at_utc
```

## 4. Curva Primária

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
```

Linhas:

```text
6.163
```

Campos:

| Campo | Significado |
|---|---|
| `planet_name` | Planeta |
| `host_star` | Estrela hospedeira |
| `planet_slug` | Slug |
| `mission` | Missão usada |
| `time` | Tempo Kepler/BKJD |
| `flux` | Fluxo selecionado |
| `flux_err` | Erro do fluxo selecionado |
| `flux_source` | Coluna original usada |
| `quality` | Flag de qualidade |
| `quality_is_zero` | Indicador booleano |
| `cadence_number` | Número de cadência |
| `source_silver_path` | Arquivo Silver de origem |
| `source_raw_path` | FITS RAW de origem |
| `source_fits_file` | Nome do FITS |
| `gold_created_at_utc` | Data/hora UTC |

## 5. Curva Filtrada Por Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
```

Linhas:

```text
3.909
```

Possui as mesmas colunas da curva primária, mas mantém apenas:

```python
quality == 0
```

## 6. Curva Faseada

Arquivo:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
```

Linhas:

```text
3.909
```

Campos principais:

```text
planet_name
host_star
planet_slug
mission
time
phase
flux
flux_err
quality
flux_source
orbital_period_days
transit_midpoint_used
phase_formula
source_gold_lightcurve
gold_created_at_utc
```

## 7. Janela de Trânsito

Arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas:

```text
1.664
```

Campos adicionais em relação à curva faseada:

```text
in_transit_window
transit_window_half_width_days
transit_duration_hours_used
```

Esse é o arquivo Gold principal para a próxima etapa.

## 8. Validação

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

Uma linha com resumo técnico da Gold.

Campos:

```text
planet_name
mission
rows_primary
rows_quality_filtered
rows_phase_folded
rows_transit_window
time_min
time_max
flux_min
flux_max
flux_median
flux_std
flux_err_median
quality_zero_count
quality_nonzero_count
selected_flux_source
period_used
transit_midpoint_used
transit_duration_used
warnings
```

## 9. Manifesto

Arquivo:

```text
data/gold/manifests/gold_data_manifest.csv
```

Usado para auditoria dos arquivos criados.

Campos essenciais:

```text
gold_file_path
transformation_type
row_count
column_count
status
sha256
file_size_bytes
notes
```

## 10. Relatórios Markdown Dentro da Gold

Arquivos:

```text
data/gold/selection/gold_candidate_report.md
data/gold/hat_p_7_b/validation/gold_data_quality_report.md
data/gold/hat_p_7_b/docs/README_gold.md
```

Eles são artefatos da execução Gold.

A documentação completa, organizada por tópico, é esta pasta:

```text
docs/gold/
```

---

# Arquivo 9: `docs/gold/28_como_usar_gold_na_metodologia.md`

```text
Origem: docs/gold/28_como_usar_gold_na_metodologia.md
```

# 28 - Como Usar a Gold na Metodologia

## 1. Função Metodológica da Gold

Na metodologia do TCC, a Gold pode ser apresentada como a etapa de preparação
analítica inicial.

Depois da coleta RAW e da padronização Silver, a Gold reduz o problema para um
caso de estudo:

```text
HAT-P-7 b observado pela missão Kepler
```

Essa redução é necessária porque a inferência bayesiana futura não será feita
simultaneamente em todos os planetas e fontes coletadas. Ela precisa começar
com um dataset controlado.

## 2. Como Descrever a Seleção

Uma descrição possível:

```text
A seleção do alvo Gold foi conduzida por meio de um scorecard técnico
construído a partir dos resumos Silver. O scorecard considerou disponibilidade
de missões, presença de fluxo corrigido, quantidade de pontos com flag de
qualidade igual a zero e completude de parâmetros orbitais necessários para
faseamento.
```

Em seguida:

```text
HAT-P-7 b foi selecionado porque possuía dados Kepler e TESS, fluxo PDCSAP,
período orbital, tempo central de trânsito e mais de mil pontos com quality
igual a zero. TrES-2 b permaneceu como candidato backup por apresentar
disponibilidade semelhante.
```

## 3. Como Descrever a Preparação da Curva

Uma descrição possível:

```text
A curva Gold primária foi construída a partir da tabela Silver MAST/Kepler de
HAT-P-7 b. Foi selecionado o fluxo PDCSAP como variável principal e o erro
PDCSAP correspondente como incerteza observacional associada. Linhas sem tempo
ou fluxo foram removidas por inviabilidade técnica de uso temporal.
```

Depois:

```text
Foi criada uma versão filtrada por qualidade, mantendo apenas pontos com
quality igual a zero. Esse filtro utiliza flags instrumentais da missão e não
constitui remoção estatística de outliers.
```

## 4. Como Descrever o Faseamento

Uma descrição possível:

```text
O faseamento orbital foi realizado usando o período orbital e o tempo central
de trânsito do catálogo NASA consolidado na Silver. Como os tempos Kepler são
expressos em escala relativa ao BJDREF dos FITS, o tempo central da NASA foi
convertido para a escala temporal da curva antes da aplicação da fórmula de
fase.
```

Fórmula:

```python
phase = ((time - transit_midpoint_used + 0.5 * period) % period) - 0.5 * period
```

## 5. Como Descrever a Janela Gold Inicial

Uma descrição possível:

```text
A janela Gold inicial foi definida em torno da fase zero com meia largura
igual a três vezes a duração catalográfica do trânsito, respeitando o critério
mínimo configurado no pipeline. Para HAT-P-7 b, essa regra resultou em uma
janela de aproximadamente ±0,48527 dias e 1.664 pontos.
```

É importante acrescentar:

```text
Essa janela foi criada como ponto de partida para diagnóstico e modelagem
futura. A definição final da janela de modelagem depende da etapa EDA.
```

## 6. O Que Enfatizar

Na metodologia, vale enfatizar:

- separação clara entre coleta, padronização e preparação analítica;
- rastreabilidade da Gold até a Silver e a RAW;
- uso de critérios explícitos;
- ausência de dados sintéticos;
- ausência de inferência nesta etapa;
- preservação de incerteza observacional via `flux_err`;
- documentação de conversão temporal;
- documentação de filtros aplicados.

## 7. O Que Evitar

Evite escrever que a Gold:

- estimou parâmetros físicos;
- ajustou o trânsito;
- validou cientificamente o modelo;
- produziu resultado bayesiano;
- encontrou posterior;
- comparou com literatura;
- removeu outliers por inferência;
- normalizou a curva de forma final.

Essas afirmações pertenceriam a etapas posteriores e não foram feitas.

## 8. Ponte Para a EDA

A Gold terminou com o arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

A etapa EDA leu esse arquivo e avaliou:

- forma visual do trânsito;
- dispersão;
- disponibilidade de `flux_err`;
- largura da janela;
- janelas alternativas para modelagem.

Portanto, na metodologia, a Gold pode ser apresentada como preparação e a EDA
como diagnóstico antes da inferência.

## 9. Frase-Síntese

Uma frase-síntese possível:

```text
A camada Gold consolidou um dataset analítico inicial para HAT-P-7 b a partir
da Silver, selecionando a missão Kepler, o fluxo PDCSAP, pontos com qualidade
instrumental igual a zero e uma janela inicial faseada em torno do trânsito,
mantendo proveniência e checksums para todos os artefatos derivados.
```

---
