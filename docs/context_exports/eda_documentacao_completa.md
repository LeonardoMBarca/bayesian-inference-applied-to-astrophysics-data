# Documentacao Completa EDA
> Snapshot histórico gerado antes do hardening de 2026-08-24. Não descreve automaticamente o pipeline atual.

Documento consolidado para uso como contexto em GPT.
- Gerado em UTC: `2026-06-16T15:47:14+00:00`
- Pasta de origem: `docs/eda`
- Observacao: este arquivo e apenas uma exportacao consolidada; os documentos originais nao foram removidos nem alterados.
- Uso sugerido: copiar este Markdown como contexto quando precisar discutir esta etapa especifica do TCC.

## Arquivos Incluidos
1. `docs/eda/README.md`
2. `docs/eda/gold_hat_p_7_b/README.md`
3. `docs/eda/gold_hat_p_7_b/29_contexto_escopo_e_regras_eda.md`
4. `docs/eda/gold_hat_p_7_b/30_pipeline_eda_e_codigo.md`
5. `docs/eda/gold_hat_p_7_b/31_diagnosticos_estatisticos_e_tabelas.md`
6. `docs/eda/gold_hat_p_7_b/32_figuras_e_leitura_visual.md`
7. `docs/eda/gold_hat_p_7_b/33_resultados_recomendacoes_e_limitacoes.md`
8. `docs/eda/gold_hat_p_7_b/34_dicionario_de_arquivos_e_campos_eda.md`
9. `docs/eda/gold_hat_p_7_b/35_como_usar_eda_na_metodologia.md`

---

# Arquivo 1: `docs/eda/README.md`

```text
Origem: docs/eda/README.md
```

# Documentação das Análises Exploratórias

Esta pasta documenta análises exploratórias e diagnósticas realizadas após a
criação das camadas RAW, Silver e Gold.

As análises nesta pasta não fazem parte da RAW, Silver ou Gold. Elas leem
artefatos já existentes e produzem saídas em:

```text
notebooks/
reports/
figures/
tables/
```

## Análises Disponíveis

1. [gold_hat_p_7_b](gold_hat_p_7_b/README.md)  
   EDA da Gold de HAT-P-7 b antes da modelagem bayesiana.

## Regra Geral

As análises exploratórias:

- não modificam `data/raw/`;
- não modificam `data/silver/`;
- não modificam `data/gold/`;
- não baixam dados externos;
- não fazem inferência bayesiana;
- não ajustam modelo físico de trânsito;
- não criam resultados científicos finais.

Elas servem para diagnosticar se os artefatos preparados estão adequados para a
próxima etapa.

---

# Arquivo 2: `docs/eda/gold_hat_p_7_b/README.md`

```text
Origem: docs/eda/gold_hat_p_7_b/README.md
```

# Documentação EDA Gold - HAT-P-7 b

Esta pasta documenta a etapa de **EDA e diagnóstico visual** da Gold de HAT-P-7 b.

A EDA foi criada para responder se o dataset Gold está adequado para iniciar uma
modelagem bayesiana preliminar.

Ela lê a Gold, mas não altera:

```text
data/raw/
data/silver/
data/gold/
```

## Como Ler

Os arquivos estão numerados em ordem sugerida:

1. [29_contexto_escopo_e_regras_eda.md](29_contexto_escopo_e_regras_eda.md)  
   Explica o objetivo da EDA, entradas, saídas e limites.

2. [30_pipeline_eda_e_codigo.md](30_pipeline_eda_e_codigo.md)  
   Documenta notebook, script, execução e reprodutibilidade.

3. [31_diagnosticos_estatisticos_e_tabelas.md](31_diagnosticos_estatisticos_e_tabelas.md)  
   Explica métricas calculadas e tabelas derivadas.

4. [32_figuras_e_leitura_visual.md](32_figuras_e_leitura_visual.md)  
   Descreve as figuras geradas e incorpora imagens-chave no Markdown.

5. [33_resultados_recomendacoes_e_limitacoes.md](33_resultados_recomendacoes_e_limitacoes.md)  
   Resume interpretação, recomendação de janela e limitações.

6. [34_dicionario_de_arquivos_e_campos_eda.md](34_dicionario_de_arquivos_e_campos_eda.md)  
   Mapeia arquivos e campos produzidos pela EDA.

7. [35_como_usar_eda_na_metodologia.md](35_como_usar_eda_na_metodologia.md)  
   Organiza a EDA em linguagem útil para a futura metodologia.

## Artefatos Principais

Notebook:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
```

Script:

```text
scripts/analyze_gold_lightcurve.py
```

Relatório:

```text
reports/gold_eda_hat_p_7_b_report.md
```

Figuras:

```text
figures/gold_eda/hat_p_7_b/
```

Tabelas:

```text
tables/gold_eda/hat_p_7_b/
```

## Resultado Principal

A EDA indicou:

- o trânsito é visualmente identificável;
- a janela Gold inicial de aproximadamente `±0,48527` dias é ampla;
- há `flux_err` disponível e sem ausências na janela;
- existe quantidade suficiente de pontos em janelas mais estreitas;
- a recomendação preliminar para modelagem é usar `abs(phase) <= 0.15`.

Essa recomendação é diagnóstica, não inferencial.

---

# Arquivo 3: `docs/eda/gold_hat_p_7_b/29_contexto_escopo_e_regras_eda.md`

```text
Origem: docs/eda/gold_hat_p_7_b/29_contexto_escopo_e_regras_eda.md
```

# 29 - Contexto, Escopo e Regras da EDA

## 1. Contexto

Após a criação da Gold, foi necessário verificar se o dataset preparado para
HAT-P-7 b realmente parecia adequado para uma primeira modelagem bayesiana.

A Gold já havia definido:

- planeta: `HAT-P-7 b`;
- missão: `Kepler`;
- fluxo: `pdcsap_flux`;
- erro: `pdcsap_flux_err`;
- curva primária: `6.163` linhas;
- curva filtrada por qualidade: `3.909` linhas;
- curva faseada: `3.909` linhas;
- janela inicial de trânsito: `1.664` linhas;
- meia largura da janela inicial: aproximadamente `0,48527` dias.

A EDA foi criada para diagnosticar esses artefatos antes de qualquer modelo.

## 2. Objetivo

O objetivo da EDA é responder:

1. A curva mostra um trânsito visualmente identificável?
2. A janela Gold atual parece adequada ou larga demais?
3. Há dados suficientes em uma janela mais estreita?
4. `flux_err` está disponível para uma likelihood gaussiana preliminar?
5. A Gold parece pronta para uma primeira modelagem bayesiana?
6. Qual arquivo deve ser usado na próxima etapa?

## 3. Entradas

A EDA lê:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

## 4. Saídas

A EDA escreve apenas em:

```text
notebooks/
reports/
figures/
tables/
```

Arquivos criados:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
scripts/analyze_gold_lightcurve.py
reports/gold_eda_hat_p_7_b_report.md
figures/gold_eda/hat_p_7_b/
tables/gold_eda/hat_p_7_b/
```

## 5. O Que a EDA Faz

A EDA calcula:

- número de linhas;
- intervalo de tempo;
- intervalo de fase;
- valores ausentes em `flux`;
- valores ausentes em `flux_err`;
- estatísticas de `flux`;
- estatísticas de `flux_err`;
- contagem de `quality`;
- mediana e desvio padrão do fluxo;
- dispersão fora do núcleo de trânsito;
- profundidade visual aproximada por contraste de medianas;
- comparação de janelas em torno da fase zero.

## 6. O Que a EDA Não Faz

A EDA não faz:

- inferência bayesiana;
- ajuste físico de trânsito;
- posterior sampling;
- PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- comparação com literatura;
- estimativa final de profundidade;
- normalização final;
- remoção estatística de outliers;
- alteração de RAW/Silver/Gold.

## 7. Interpretação da Profundidade Visual

A EDA calcula uma profundidade visual aproximada.

Ela é obtida por contraste entre:

- mediana do fluxo dentro de um núcleo de trânsito;
- mediana do fluxo fora desse núcleo, dentro da janela analisada.

Essa métrica é apenas exploratória.

Ela não deve ser chamada de:

- estimativa bayesiana;
- ajuste de trânsito;
- resultado físico final;
- parâmetro posterior.

Ela serve apenas para confirmar se a queda de fluxo é visível e coerente com a
expectativa de um trânsito.

## 8. Regra de Imutabilidade

A EDA não modifica os arquivos em:

```text
data/raw/
data/silver/
data/gold/
```

Essa regra foi validada por comparação de checksums, tamanhos e timestamps dos
arquivos dessas camadas antes e depois da execução da EDA.

## 9. Resultado Geral

A EDA concluiu que:

- há trânsito visualmente identificável;
- `flux_err` está disponível;
- a janela Gold inicial é ampla para modelagem;
- uma janela de `±0,15` dias é uma recomendação preliminar mais focada;
- o arquivo Gold principal deve continuar sendo lido, com filtro adicional por fase na etapa de modelagem.

---

# Arquivo 4: `docs/eda/gold_hat_p_7_b/30_pipeline_eda_e_codigo.md`

```text
Origem: docs/eda/gold_hat_p_7_b/30_pipeline_eda_e_codigo.md
```

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

---

# Arquivo 5: `docs/eda/gold_hat_p_7_b/31_diagnosticos_estatisticos_e_tabelas.md`

```text
Origem: docs/eda/gold_hat_p_7_b/31_diagnosticos_estatisticos_e_tabelas.md
```

# 31 - Diagnósticos Estatísticos e Tabelas da EDA

## 1. Objetivo

Este documento descreve as tabelas derivadas pela EDA e o significado das
métricas calculadas.

As tabelas são diagnósticas. Elas não representam resultado inferencial.

## 2. Tabela Resumo

Arquivo:

```text
tables/gold_eda/hat_p_7_b/gold_eda_summary.csv
```

Essa tabela possui uma linha e consolida os principais diagnósticos.

## 3. Principais Valores

| Métrica | Valor |
|---|---:|
| Planeta | `HAT-P-7 b` |
| Missão | `Kepler` |
| Linhas na curva primária | `6.163` |
| Linhas após filtro de qualidade | `3.909` |
| Linhas na curva faseada | `3.909` |
| Linhas na janela Gold atual | `1.664` |
| Tempo mínimo | `120,53881583872862` |
| Tempo máximo | `258,46743138637976` |
| Fase mínima na janela | `-0,4850831437298972` |
| Fase máxima na janela | `0,4849464913942332` |
| Valores ausentes em `flux` | `0` |
| Valores ausentes em `flux_err` | `0` |
| Pontos com `quality == 0` na curva primária | `3.909` |
| Pontos com `quality != 0` na curva primária | `2.254` |
| Duração de trânsito em dias | `0,16175666666666666` |
| Janela recomendada pela EDA | `0,15` dias |

## 4. Estatísticas de Fluxo

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| `flux_min` | `1027023,6` |
| `flux_max` | `1041236,94` |
| `flux_median` | `1034872,5` |
| `flux_mean` | `1036739,1433052885` |
| `flux_std` | `4012,547787789801` |

Interpretação:

- existe variação clara de fluxo dentro da janela;
- a queda de fluxo próxima da fase zero é visualmente identificável;
- a dispersão ainda inclui baseline e estrutura observacional, não apenas ruído branco.

## 5. Estatísticas de `flux_err`

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| `flux_err_median` | `25,8860865` |
| `flux_err_mean` | `26,102194072115385` |
| `flux_err_std` | `0,25819710596197804` |
| Ausências em `flux_err` | `0` |

Interpretação:

`flux_err` está disponível e numericamente consistente para uma likelihood
gaussiana preliminar. A modelagem futura ainda deve avaliar se essa incerteza
é suficiente para explicar os resíduos ou se será necessário incluir termo
extra de dispersão.

## 6. Profundidade Visual Aproximada

A profundidade visual aproximada da janela Gold atual foi:

```text
0,0065010087865026486
```

Em unidades de fluxo:

```text
6765,960000000079
```

Ela foi calculada como:

```text
(mediana fora do trânsito - mediana dentro do trânsito) / mediana fora do trânsito
```

com:

| Métrica | Valor |
|---|---:|
| Pontos dentro do núcleo do trânsito | `287` |
| Pontos fora do núcleo do trânsito | `1.377` |
| Mediana dentro do trânsito | `1033989,44` |
| Mediana fora do trânsito | `1040755,4` |
| Dispersão fora do trânsito | `3334,470461905991` |

Essa métrica é apenas exploratória.

## 7. Comparação de Janelas

Arquivo:

```text
tables/gold_eda/hat_p_7_b/window_comparison_summary.csv
```

Janelas avaliadas:

```text
±0,50 dias
±0,25 dias
±0,15 dias
±0,10 dias
±0,05 dias
```

Resumo:

| Janela | Pontos | Pontos fora do núcleo | Profundidade visual |
|---:|---:|---:|---:|
| `0,50` | `1.711` | `1.424` | `0,0064917` |
| `0,25` | `854` | `567` | `0,0065077` |
| `0,15` | `516` | `229` | `0,0065348` |
| `0,10` | `335` | `48` | `0,0061648` |
| `0,05` | `179` | `0` | indisponível |

## 8. Critério de Recomendação

O script recomenda a menor janela que satisfaça:

- meia largura pelo menos `1,5` vezes a meia duração do trânsito;
- pelo menos `200` pontos;
- pelo menos `50` pontos fora do núcleo do trânsito;
- profundidade visual calculável.

Com esse critério, a recomendação foi:

```text
±0,15 dias
```

## 9. Binning Visual

Arquivo:

```text
tables/gold_eda/hat_p_7_b/transit_window_binned_summary.csv
```

Essa tabela divide a janela de trânsito em bins de fase e calcula:

- mediana do fluxo;
- primeiro quartil;
- terceiro quartil;
- desvio padrão;
- quantidade de pontos;
- ponto médio do bin;
- erro padrão visual do bin.

Ela foi usada apenas para visualização.

## 10. Limitações

As tabelas não:

- normalizam fluxo;
- ajustam modelo;
- removem outliers;
- estimam posterior;
- comparam com literatura;
- validam resíduos.

Elas documentam a condição do dataset antes da modelagem.

---

# Arquivo 6: `docs/eda/gold_hat_p_7_b/32_figuras_e_leitura_visual.md`

```text
Origem: docs/eda/gold_hat_p_7_b/32_figuras_e_leitura_visual.md
```

# 32 - Figuras e Leitura Visual da EDA

## 1. Objetivo

Este documento descreve as figuras geradas pela EDA e orienta como interpretá-las.

As figuras foram salvas em PNG com `dpi=300` em:

```text
figures/gold_eda/hat_p_7_b/
```

As imagens abaixo são incorporadas no Markdown apenas onde ajudam a leitura.

## 2. Curva Primária no Tempo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/01_primary_lightcurve_time.png
```

Conteúdo:

- eixo x: tempo Kepler/BKJD;
- eixo y: fluxo;
- fonte: `primary_lightcurve.csv`;
- inclui pontos antes do filtro por qualidade.

Uso:

Essa figura mostra a série temporal primária ainda com pontos marcados por
flags instrumentais. Ela ajuda a entender o volume inicial e a escala de fluxo.

## 3. Curva Filtrada Por Qualidade no Tempo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/02_quality_filtered_lightcurve_time.png
```

Conteúdo:

- eixo x: tempo Kepler/BKJD;
- eixo y: fluxo;
- fonte: `primary_lightcurve_quality_filtered.csv`;
- mantém apenas `quality == 0`.

Uso:

Essa figura é a melhor visão temporal antes do faseamento, pois mostra apenas
os pontos técnicos considerados bons pela flag da missão.

## 4. Curva Faseada Completa

Arquivo:

```text
figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png
```

Conteúdo:

- eixo x: fase orbital em dias, centrada no trânsito;
- eixo y: fluxo;
- fonte: `phase_folded_lightcurve.csv`.

Leitura:

A queda de fluxo aparece próxima de `phase = 0`, o que confirma visualmente que
o faseamento Gold está coerente com o tempo central de trânsito usado.

![Curva faseada completa](../../../figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png)

## 5. Janela de Trânsito Gold Atual

Arquivo:

```text
figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png
```

Conteúdo:

- eixo x: fase orbital em dias;
- eixo y: fluxo;
- fonte: `transit_window_lightcurve.csv`;
- janela aproximada: `±0,48527` dias.

Leitura:

A janela contém o trânsito, mas também bastante baseline fora do evento. Ela é
útil para diagnóstico amplo, porém parece larga para uma primeira modelagem
paramétrica simples.

![Janela de trânsito Gold atual](../../../figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png)

## 6. Janela de Trânsito Com Binning Visual

Arquivo:

```text
figures/gold_eda/hat_p_7_b/05_transit_window_binned.png
```

Conteúdo:

- pontos individuais em baixa opacidade;
- mediana por bin de fase;
- intervalo interquartil por bin;
- linha vertical em fase zero.

Leitura:

O binning visual torna a queda de fluxo mais evidente sem ajustar um modelo.
Ele não altera a Gold e não substitui inferência. Serve apenas para inspeção.

![Janela com binning visual](../../../figures/gold_eda/hat_p_7_b/05_transit_window_binned.png)

## 7. Distribuição do Fluxo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/06_flux_distribution.png
```

Conteúdo:

- histograma do fluxo na janela de trânsito;
- linha vertical na mediana.

Uso:

Ajuda a verificar a escala do fluxo e a assimetria esperada por mistura de
pontos em trânsito e fora do trânsito.

## 8. Distribuição de `flux_err`

Arquivo:

```text
figures/gold_eda/hat_p_7_b/07_flux_err_distribution.png
```

Conteúdo:

- histograma de `flux_err`;
- linha vertical na mediana.

Uso:

Ajuda a verificar se há incerteza observacional disponível para uma likelihood
gaussiana preliminar. A EDA encontrou `0` ausências em `flux_err`.

## 9. Comparação de Larguras de Janela

Arquivo:

```text
figures/gold_eda/hat_p_7_b/08_window_width_comparison.png
```

Conteúdo:

- painéis para `±0,50`, `±0,25`, `±0,15`, `±0,10` e `±0,05` dias;
- pontos de fluxo por fase;
- contagem de pontos por janela;
- profundidade visual aproximada quando calculável.

Leitura:

A figura mostra que:

- a janela `±0,50` dias é larga;
- a janela `±0,25` dias ainda tem bastante baseline;
- a janela `±0,15` dias preserva o trânsito e baseline local;
- a janela `±0,10` dias começa a ficar limitada no baseline fora do núcleo;
- a janela `±0,05` dias não tem baseline fora do núcleo para calcular contraste.

![Comparação de larguras de janela](../../../figures/gold_eda/hat_p_7_b/08_window_width_comparison.png)

## 10. Conclusão Visual

As figuras sustentam três conclusões diagnósticas:

1. O trânsito é visualmente identificável.
2. O faseamento está coerente com o centro de trânsito.
3. A janela Gold inicial é útil para inspeção, mas larga para modelagem inicial.

A recomendação visual e tabular combinada é iniciar a modelagem com:

```python
abs(phase) <= 0.15
```

---

# Arquivo 7: `docs/eda/gold_hat_p_7_b/33_resultados_recomendacoes_e_limitacoes.md`

```text
Origem: docs/eda/gold_hat_p_7_b/33_resultados_recomendacoes_e_limitacoes.md
```

# 33 - Resultados, Recomendações e Limitações da EDA

## 1. Pergunta: A Curva Mostra Um Trânsito Visualmente Identificável?

Resposta:

```text
Sim.
```

A queda de fluxo aparece próxima de `phase = 0` na curva faseada e na janela de
trânsito. O binning visual reforça essa leitura.

A profundidade visual aproximada na janela Gold atual foi:

```text
0,006501
```

Essa profundidade é apenas exploratória.

## 2. Pergunta: A Janela Atual Parece Excessivamente Larga?

Resposta:

```text
Sim, para a primeira modelagem.
```

A janela Gold atual usa aproximadamente:

```text
±0,48527 dias
```

Ela é útil como janela inicial conservadora, pois garante que o trânsito e
baseline amplo estejam presentes. Porém, para um modelo bayesiano preliminar,
ela inclui baseline demais em relação à duração do trânsito.

## 3. Pergunta: Há Dados Suficientes em Uma Janela Mais Estreita?

Resposta:

```text
Sim.
```

Comparação:

| Janela | Pontos | Pontos fora do núcleo |
|---:|---:|---:|
| `±0,50` | `1.711` | `1.424` |
| `±0,25` | `854` | `567` |
| `±0,15` | `516` | `229` |
| `±0,10` | `335` | `48` |
| `±0,05` | `179` | `0` |

A janela `±0,15` dias preserva pontos suficientes dentro e fora do núcleo do
trânsito.

## 4. Recomendação de Janela

Recomendação preliminar:

```python
abs(phase) <= 0.15
```

Justificativa:

- mantém `516` pontos;
- mantém `287` pontos dentro do núcleo do trânsito;
- mantém `229` pontos fora do núcleo;
- preserva baseline local;
- reduz a largura em relação à janela Gold inicial;
- evita a janela `±0,10`, que já fica com baseline externo limitado;
- evita `±0,05`, que não tem baseline externo suficiente.

## 5. Pergunta: Há `flux_err` Utilizável Para Likelihood Gaussiana?

Resposta:

```text
Sim.
```

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| Ausências em `flux_err` | `0` |
| Mediana de `flux_err` | `25,8860865` |
| Média de `flux_err` | `26,102194072115385` |
| Desvio padrão de `flux_err` | `0,25819710596197804` |

Isso permite usar `flux_err` em uma likelihood gaussiana preliminar.

A modelagem futura ainda deve avaliar se será necessário incluir um termo de
ruído adicional.

## 6. Pergunta: A Gold Está Pronta Para Um Modelo Bayesiano Preliminar?

Resposta:

```text
Sim, com cautela.
```

A Gold está pronta para um primeiro modelo simples porque:

- tem curva faseada;
- tem janela de trânsito;
- tem fluxo;
- tem incerteza de fluxo;
- não possui ausências em `flux` ou `flux_err` na janela;
- mantém proveniência;
- preserva parâmetros orbitais usados.

Mas a modelagem ainda precisa definir:

- normalização local;
- priors;
- modelo físico;
- likelihood;
- estratégia de amostragem;
- diagnóstico de resíduos;
- diagnóstico de convergência.

## 7. Arquivo de Entrada Para a Próxima Etapa

Usar:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Aplicar na etapa de modelagem o filtro preliminar:

```python
abs(phase) <= 0.15
```

Esse filtro não foi aplicado na Gold para preservar a janela inicial ampla e
permitir comparação de janelas.

## 8. Limitações

Limitações da EDA:

- a profundidade visual não é parâmetro físico estimado;
- o binning é apenas visual;
- não há ajuste de trânsito;
- não há inferência;
- não há posterior;
- não há avaliação de ruído correlacionado;
- não há normalização final;
- não há comparação com literatura;
- não há validação residual.

## 9. Decisão Recomendada

Para a próxima etapa, a recomendação objetiva é:

1. carregar `transit_window_lightcurve.csv`;
2. filtrar `abs(phase) <= 0.15`;
3. aplicar uma normalização local simples e documentada;
4. ajustar um modelo bayesiano preliminar;
5. avaliar resíduos, posterior e sensibilidade da janela.

## 10. Frase-Síntese

Uma frase-síntese possível:

```text
A EDA da Gold de HAT-P-7 b confirmou visualmente o trânsito, verificou a
presença de incertezas observacionais em flux_err, identificou que a janela
Gold inicial é ampla para modelagem e recomendou uma janela preliminar de
±0,15 dias em torno da fase zero.
```

---

# Arquivo 8: `docs/eda/gold_hat_p_7_b/34_dicionario_de_arquivos_e_campos_eda.md`

```text
Origem: docs/eda/gold_hat_p_7_b/34_dicionario_de_arquivos_e_campos_eda.md
```

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

---

# Arquivo 9: `docs/eda/gold_hat_p_7_b/35_como_usar_eda_na_metodologia.md`

```text
Origem: docs/eda/gold_hat_p_7_b/35_como_usar_eda_na_metodologia.md
```

# 35 - Como Usar a EDA na Metodologia

## 1. Função Metodológica da EDA

Na metodologia, a EDA pode ser apresentada como uma etapa de diagnóstico antes
da modelagem bayesiana.

Ela verifica se o dataset Gold:

- tem trânsito visualmente identificável;
- tem incerteza observacional utilizável;
- tem janela de trânsito adequada;
- tem quantidade suficiente de pontos;
- exige ajustes adicionais antes da inferência.

## 2. Como Descrever a EDA

Uma descrição possível:

```text
Após a construção da camada Gold, foi realizada uma análise exploratória da
curva de luz de HAT-P-7 b com o objetivo de verificar a adequação do dataset
para modelagem bayesiana preliminar. A análise considerou a curva primária, a
curva filtrada por qualidade, a curva faseada e a janela de trânsito definida
na Gold.
```

## 3. Como Descrever as Métricas

Uma descrição possível:

```text
Foram calculadas métricas descritivas, incluindo contagem de linhas, intervalo
temporal, intervalo de fase, valores ausentes em fluxo e erro de fluxo,
estatísticas de fluxo, distribuição das flags de qualidade e comparação de
janelas em torno da fase zero.
```

## 4. Como Descrever a Profundidade Visual

Use uma formulação cuidadosa:

```text
Como diagnóstico visual, foi calculada uma aproximação exploratória da
profundidade por contraste entre a mediana do fluxo fora do núcleo do trânsito
e a mediana do fluxo dentro do núcleo. Essa medida não foi tratada como
estimativa física final nem como resultado inferencial.
```

Evite:

```text
A profundidade foi estimada pelo modelo.
```

Porque isso não aconteceu nesta etapa.

## 5. Como Descrever as Figuras

Uma descrição possível:

```text
Foram geradas visualizações da curva primária, da curva filtrada por qualidade,
da curva faseada completa, da janela de trânsito, da janela com binning visual,
das distribuições de fluxo e erro de fluxo, além de uma comparação de janelas
com diferentes larguras em torno da fase zero.
```

## 6. Como Descrever a Recomendação de Janela

Uma descrição possível:

```text
A janela Gold inicial de aproximadamente ±0,48527 dias mostrou-se adequada
para inspeção ampla, mas relativamente larga para uma primeira modelagem. A
comparação exploratória de janelas indicou que ±0,15 dias preserva o evento de
trânsito e fornece baseline local suficiente, sendo recomendada como janela
preliminar para o primeiro modelo bayesiano.
```

## 7. Como Descrever `flux_err`

Uma descrição possível:

```text
A coluna de incerteza observacional `flux_err` estava disponível para todos os
pontos da janela de trânsito analisada, com mediana próxima de 25,89 unidades
de fluxo. Isso permite sua utilização em uma likelihood gaussiana preliminar,
embora a adequação dos resíduos ainda deva ser avaliada na etapa de modelagem.
```

## 8. O Que Enfatizar

Enfatize:

- a EDA é posterior à Gold;
- a EDA não altera as camadas de dados;
- a EDA é diagnóstica;
- a EDA não estima parâmetros físicos finais;
- a EDA orienta a janela inicial da modelagem;
- o resultado principal é uma recomendação operacional.

## 9. O Que Evitar

Evite afirmar que a EDA:

- ajustou um modelo de trânsito;
- produziu posterior;
- estimou parâmetros por inferência;
- validou um modelo bayesiano;
- comparou com literatura;
- decidiu a Gold definitiva do TCC.

## 10. Ponte Para a Modelagem

A próxima etapa poderá ser descrita como:

```text
A partir dos diagnósticos da EDA, a modelagem bayesiana preliminar deverá usar
a curva Gold de janela de trânsito, restringindo inicialmente os dados a
abs(phase) <= 0,15, com normalização local explícita e likelihood baseada em
flux_err.
```

## 11. Frase-Síntese

Uma frase-síntese possível:

```text
A EDA funcionou como uma etapa de controle de qualidade analítico da Gold,
confirmando a presença visual do trânsito, avaliando a largura da janela,
verificando a disponibilidade de incertezas observacionais e recomendando uma
janela preliminar de ±0,15 dias para a futura modelagem bayesiana.
```

---
