# 34 - Dicionário de Arquivos e Campos da EDA

## 1. Objetivo

Este documento mapeia os arquivos criados pela EDA e o significado dos campos
das tabelas derivadas.

## 2. Notebook

Arquivo:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
```

Função:

- executar a EDA de ponta a ponta;
- reutilizar o script principal;
- exibir tabelas;
- listar figuras;
- mostrar o relatório gerado.

## 3. Script

Arquivo:

```text
scripts/analyze_gold_lightcurve.py
```

Função:

- ler a Gold;
- calcular métricas;
- gerar tabelas;
- gerar figuras;
- escrever relatório Markdown.

## 4. Relatório

Arquivo:

```text
reports/gold_eda_hat_p_7_b_report.md
```

Função:

- consolidar os resultados da EDA;
- responder às perguntas diagnósticas;
- indicar recomendação de janela;
- apontar próximo arquivo de modelagem;
- incorporar imagens-chave.

## 5. Tabela `gold_eda_summary.csv`

Arquivo:

```text
tables/gold_eda/hat_p_7_b/gold_eda_summary.csv
```

Campos:

| Campo | Significado |
|---|---|
| `planet_name` | Nome do planeta |
| `mission` | Missão analisada |
| `rows_primary` | Linhas da curva Gold primária |
| `rows_quality_filtered` | Linhas após filtro Gold de qualidade |
| `rows_phase_folded` | Linhas da curva faseada |
| `rows_transit_window` | Linhas da janela Gold atual |
| `time_min` | Menor tempo da curva primária |
| `time_max` | Maior tempo da curva primária |
| `phase_min` | Menor fase na janela Gold atual |
| `phase_max` | Maior fase na janela Gold atual |
| `missing_flux_count` | Ausências em `flux` |
| `missing_flux_err_count` | Ausências em `flux_err` |
| `quality_zero_count` | Pontos com `quality == 0` |
| `quality_nonzero_count` | Pontos com `quality != 0` |
| `transit_duration_days` | Duração de trânsito em dias |
| `recommended_window_half_width_days` | Meia janela recomendada pela EDA |
| `flux_min` | Fluxo mínimo na janela |
| `flux_max` | Fluxo máximo na janela |
| `flux_median` | Mediana do fluxo na janela |
| `flux_mean` | Média do fluxo na janela |
| `flux_std` | Desvio padrão do fluxo na janela |
| `flux_err_median` | Mediana de `flux_err` |
| `flux_err_mean` | Média de `flux_err` |
| `flux_err_std` | Desvio padrão de `flux_err` |
| `in_transit_count` | Pontos no núcleo do trânsito |
| `out_of_transit_count` | Pontos fora do núcleo |
| `in_transit_flux_median` | Mediana do fluxo no núcleo |
| `out_of_transit_flux_median` | Mediana do fluxo fora do núcleo |
| `out_of_transit_flux_std` | Dispersão fora do núcleo |
| `approximate_depth_visual` | Profundidade visual aproximada |
| `approximate_depth_flux_units` | Diferença de medianas em unidades de fluxo |
| `notes` | Observação sobre o cálculo |

## 6. Tabela `window_comparison_summary.csv`

Arquivo:

```text
tables/gold_eda/hat_p_7_b/window_comparison_summary.csv
```

Uma linha por janela testada.

Campos:

| Campo | Significado |
|---|---|
| `window_half_width_days` | Meia largura da janela em dias |
| `row_count` | Quantidade de pontos na janela |
| `flux_median` | Mediana do fluxo |
| `flux_std` | Desvio padrão do fluxo |
| `in_transit_count` | Pontos dentro do núcleo do trânsito |
| `out_of_transit_count` | Pontos fora do núcleo |
| `in_transit_flux_median` | Mediana dentro do núcleo |
| `out_of_transit_flux_median` | Mediana fora do núcleo |
| `out_of_transit_flux_std` | Dispersão fora do núcleo |
| `approximate_depth_visual` | Profundidade visual aproximada |
| `approximate_depth_flux_units` | Contraste em unidades de fluxo |
| `notes` | Observação sobre cálculo ou limitação |

## 7. Tabela `transit_window_binned_summary.csv`

Arquivo:

```text
tables/gold_eda/hat_p_7_b/transit_window_binned_summary.csv
```

Uma linha por bin de fase.

Campos:

| Campo | Significado |
|---|---|
| `phase_bin` | Intervalo de fase do bin |
| `flux_median` | Mediana do fluxo no bin |
| `flux_q25` | Primeiro quartil do fluxo |
| `flux_q75` | Terceiro quartil do fluxo |
| `flux_std` | Desvio padrão do fluxo no bin |
| `count` | Número de pontos no bin |
| `phase_mid` | Ponto médio do bin |
| `flux_sem` | Erro padrão visual do fluxo no bin |

## 8. Figuras

Diretório:

```text
figures/gold_eda/hat_p_7_b/
```

Arquivos:

```text
01_primary_lightcurve_time.png
02_quality_filtered_lightcurve_time.png
03_phase_folded_lightcurve_full.png
04_transit_window_lightcurve.png
05_transit_window_binned.png
06_flux_distribution.png
07_flux_err_distribution.png
08_window_width_comparison.png
```

Todas foram geradas com `matplotlib` e `dpi=300`.

## 9. Relação Com a Gold

A EDA não cria novos arquivos dentro de:

```text
data/gold/
```

Ela lê a Gold e escreve artefatos derivados fora das camadas do datalake.

## 10. Arquivo Recomendado Para Modelagem

Entrada recomendada:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Filtro recomendado na próxima etapa:

```python
abs(phase) <= 0.15
```
