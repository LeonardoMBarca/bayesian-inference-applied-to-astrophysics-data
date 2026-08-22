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
