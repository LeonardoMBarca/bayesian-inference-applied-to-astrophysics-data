# Documentação M4 - Comparação de Modelos - HAT-P-7 b

Esta pasta documenta a quarta etapa de modelagem do projeto:

```text
M4 - Model Comparison
```

O M4 compara M1, M2 e M3 a partir dos artefatos já gerados. Ele não ajusta um
novo modelo bayesiano, não roda NUTS e não modifica os resultados anteriores.

O papel do M4 é responder, de forma organizada:

- como as hipóteses de forma do trânsito afetam a profundidade inferida;
- qual modelo descreve melhor o formato observado;
- qual modelo apresenta melhor comportamento preditivo simples;
- qual modelo oferece melhor equilíbrio entre interpretabilidade e
  flexibilidade;
- qual modelo deve ser tratado como resultado principal preliminar do TCC.

## Como Ler

1. [01_contexto_e_objetivo.md](01_contexto_e_objetivo.md)  
   Explica o papel do M4 na sequência M1-M4, suas entradas e seu escopo.

2. [02_criterios_de_comparacao.md](02_criterios_de_comparacao.md)  
   Documenta os critérios usados: parâmetros, diagnósticos, métricas
   preditivas, resíduos, LOO/WAIC opcional e recomendação.

3. [03_resultados_comparativos.md](03_resultados_comparativos.md)  
   Resume os resultados comparativos, com links para tabelas e figuras.

4. [04_recomendacao_e_limitacoes.md](04_recomendacao_e_limitacoes.md)  
   Explica a recomendação de M3 como resultado principal preliminar, preserva
   os papéis de M1/M2 e lista limitações.

## Artefatos Principais

Script:

```text
scripts/run_model_comparison.py
```

Notebook:

```text
notebooks/06_model_comparison_hat_p_7_b.ipynb
```

Configuração e resumo:

```text
models/model_comparison/hat_p_7_b/model_comparison_config.json
models/model_comparison/hat_p_7_b/model_comparison_summary.json
```

Tabelas:

```text
tables/model_comparison/hat_p_7_b/parameter_comparison.csv
tables/model_comparison/hat_p_7_b/diagnostic_comparison.csv
tables/model_comparison/hat_p_7_b/predictive_metric_comparison.csv
tables/model_comparison/hat_p_7_b/residual_comparison.csv
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
tables/model_comparison/hat_p_7_b/loo_waic_comparison.csv
```

Figuras:

```text
figures/model_comparison/hat_p_7_b/
```

Relatório:

```text
reports/model_comparison_hat_p_7_b_report.md
```

## Resultado Resumido

Profundidade:

- M1: `0,00525258`, HDI 94% `[0,00464576, 0,00587726]`;
- M2: `0,00721029`, HDI 94% `[0,00637213, 0,00809741]`, exploratória;
- M3: `0,00656620`, HDI 94% `[0,00594692, 0,00716767]`.

`Rp/Rs`:

- M1: `0,07243869`, HDI 94% `[0,06815983, 0,07666328]`;
- M2: não estimado diretamente;
- M3: `0,08100761`, HDI 94% `[0,07711627, 0,08466210]`.

Diagnósticos:

- todos os modelos tiveram `divergências = 0`;
- todos tiveram `R-hat máximo <= 1,01`;
- todos tiveram ESS mínimo acima de `1000`.

Métricas preditivas:

- M1 RMSE: `0,00358754`;
- M2 RMSE: `0,00317888`;
- M3 RMSE: `0,00317499`.

Recomendação:

```text
M3 - primary_preliminary_result
```

M1 permanece como baseline de referência. M2 permanece como descrição
preditiva suave. M3 é recomendado como resultado principal preliminar por
equilibrar diagnóstico, predição, profundidade direta e interpretabilidade
física aproximada.
