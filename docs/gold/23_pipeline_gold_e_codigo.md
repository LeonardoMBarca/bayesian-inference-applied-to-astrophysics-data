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
src/gold_processing/config.py
```

`scripts/gold_data_config.py` permanece como import de compatibilidade.

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
