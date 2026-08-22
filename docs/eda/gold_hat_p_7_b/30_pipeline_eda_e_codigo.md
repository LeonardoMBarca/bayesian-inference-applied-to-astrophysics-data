# 30 - Pipeline EDA e Código

## 1. Objetivo do Código

O código da EDA foi estruturado para que o notebook e o script produzam os
mesmos resultados principais.

A lógica central está no script:

```text
scripts/analyze_gold_lightcurve.py
```

O notebook:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
```

carrega esse script e chama a mesma função principal.

## 2. Comando Principal

Executar:

```bash
python scripts/analyze_gold_lightcurve.py
```

No ambiente validado:

```bash
.venv/bin/python scripts/analyze_gold_lightcurve.py
```

## 3. Bibliotecas Usadas

Bibliotecas principais:

```text
pandas
numpy
matplotlib
```

Não foi usado `seaborn`.

Não há dependência de rede.

## 4. Organização do Script

O script contém:

| Função/estrutura | Responsabilidade |
|---|---|
| `GoldEdaPaths` | Centraliza caminhos de entrada e saída |
| `resolve_project_root` | Localiza a raiz do projeto |
| `build_paths` | Monta caminhos Gold, figuras, tabelas e relatório |
| `load_gold_inputs` | Lê os CSVs Gold necessários |
| `validate_inputs` | Verifica colunas esperadas |
| `compute_visual_depth` | Calcula profundidade visual exploratória |
| `build_eda_summary` | Monta tabela resumo da EDA |
| `build_window_comparison` | Compara janelas em torno da fase zero |
| `choose_recommended_window` | Escolhe a janela preliminar recomendada |
| `build_binned_phase_statistics` | Calcula estatísticas por bins de fase |
| `save_all_figures` | Gera as oito figuras PNG |
| `write_report` | Escreve o relatório Markdown |
| `run_analysis` | Orquestra a execução completa |
| `main` | Entrada de linha de comando |

## 5. Entradas Lidas

O script lê:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

## 6. Saídas Escritas

Tabelas:

```text
tables/gold_eda/hat_p_7_b/gold_eda_summary.csv
tables/gold_eda/hat_p_7_b/window_comparison_summary.csv
tables/gold_eda/hat_p_7_b/transit_window_binned_summary.csv
```

Figuras:

```text
figures/gold_eda/hat_p_7_b/01_primary_lightcurve_time.png
figures/gold_eda/hat_p_7_b/02_quality_filtered_lightcurve_time.png
figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png
figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png
figures/gold_eda/hat_p_7_b/05_transit_window_binned.png
figures/gold_eda/hat_p_7_b/06_flux_distribution.png
figures/gold_eda/hat_p_7_b/07_flux_err_distribution.png
figures/gold_eda/hat_p_7_b/08_window_width_comparison.png
```

Relatório:

```text
reports/gold_eda_hat_p_7_b_report.md
```

## 7. Notebook

O notebook:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
```

foi criado para ser executável de ponta a ponta.

Ele:

1. localiza a raiz do projeto;
2. carrega `scripts/analyze_gold_lightcurve.py`;
3. chama `run_analysis`;
4. mostra a tabela resumo;
5. mostra a comparação de janelas;
6. lista as figuras;
7. exibe o começo do relatório Markdown.

## 8. Reprodutibilidade

O script foi validado com:

```bash
.venv/bin/python scripts/analyze_gold_lightcurve.py
```

Resultado esperado:

```text
GOLD EDA completed for HAT-P-7 b.
Report: reports/gold_eda_hat_p_7_b_report.md
Summary table: tables/gold_eda/hat_p_7_b/gold_eda_summary.csv
Window comparison: tables/gold_eda/hat_p_7_b/window_comparison_summary.csv
Figures: 8
Rows in transit window: 1664
Recommended modeling half-window: ±0.150 days
```

## 9. Cache do Matplotlib

O script define:

```text
MPLCONFIGDIR=/tmp/matplotlib-cache
```

Isso evita warnings em ambientes onde o diretório padrão do Matplotlib não é
gravável.

## 10. Validação de Não Modificação das Camadas

Antes da EDA, foi registrada uma impressão digital dos arquivos de:

```text
data/raw/
data/silver/
data/gold/
```

Depois da execução, a comparação mostrou:

```text
446 arquivos antes
446 arquivos depois
0 arquivos adicionados nas camadas de dados
0 arquivos removidos nas camadas de dados
0 SHA256 alterados
0 timestamps alterados
```

Portanto, a EDA ficou isolada nos diretórios de análise.
