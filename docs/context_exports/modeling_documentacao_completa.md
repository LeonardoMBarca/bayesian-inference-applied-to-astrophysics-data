# Documentacao Completa Modeling
Documento consolidado para uso como contexto em GPT.
- Gerado em UTC: `2026-06-16T15:47:14+00:00`
- Pasta de origem: `docs/modeling`
- Observacao: este arquivo e apenas uma exportacao consolidada; os documentos originais nao foram removidos nem alterados.
- Uso sugerido: copiar este Markdown como contexto quando precisar discutir esta etapa especifica do TCC.

## Arquivos Incluidos
1. `docs/modeling/README.md`
2. `docs/modeling/bayesian_baseline_hat_p_7_b/README.md`
3. `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/README.md`
4. `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/README.md`
5. `docs/modeling/model_comparison_hat_p_7_b/README.md`
6. `docs/modeling/bayesian_baseline_hat_p_7_b/36_contexto_escopo_e_regras_m1.md`
7. `docs/modeling/bayesian_baseline_hat_p_7_b/37_pipeline_codigo_execucao_m1.md`
8. `docs/modeling/bayesian_baseline_hat_p_7_b/38_dataset_preprocessamento_normalizacao_m1.md`
9. `docs/modeling/bayesian_baseline_hat_p_7_b/39_modelo_probabilistico_priors_likelihood_m1.md`
10. `docs/modeling/bayesian_baseline_hat_p_7_b/40_resultados_diagnosticos_m1.md`
11. `docs/modeling/bayesian_baseline_hat_p_7_b/41_figuras_tabelas_artefatos_m1.md`
12. `docs/modeling/bayesian_baseline_hat_p_7_b/42_limitacoes_proximos_modelos_m1.md`
13. `docs/modeling/bayesian_baseline_hat_p_7_b/43_como_usar_m1_na_metodologia.md`
14. `docs/modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md`
15. `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/01_contexto_e_objetivo.md`
16. `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/02_especificacao_do_modelo.md`
17. `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/03_resultados_e_diagnosticos.md`
18. `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/04_limitacoes_e_proximos_passos.md`
19. `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/01_contexto_e_objetivo.md`
20. `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/02_especificacao_do_modelo.md`
21. `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/03_resultados_e_diagnosticos.md`
22. `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/04_limitacoes_e_proximos_passos.md`
23. `docs/modeling/model_comparison_hat_p_7_b/01_contexto_e_objetivo.md`
24. `docs/modeling/model_comparison_hat_p_7_b/02_criterios_de_comparacao.md`
25. `docs/modeling/model_comparison_hat_p_7_b/03_resultados_comparativos.md`
26. `docs/modeling/model_comparison_hat_p_7_b/04_recomendacao_e_limitacoes.md`

---

# Arquivo 1: `docs/modeling/README.md`

```text
Origem: docs/modeling/README.md
```

# Documentação de Modelagem Bayesiana

Esta pasta documenta as etapas de modelagem bayesiana do projeto.

As etapas de modelagem leem artefatos preparados na Gold e geram saídas em:

```text
models/
reports/
figures/
tables/
notebooks/
scripts/
```

Elas não devem modificar:

```text
data/raw/
data/silver/
data/gold/
```

## Modelos Documentados

1. [bayesian_baseline_hat_p_7_b](bayesian_baseline_hat_p_7_b/README.md)  
   M1 - baseline bayesiano simples do tipo box transit para HAT-P-7 b,
   incluindo a execução robusta `002_nuts_robust` com NUTS.

2. [bayesian_predictive_phase_regression_hat_p_7_b](bayesian_predictive_phase_regression_hat_p_7_b/README.md)  
   M2 - regressão bayesiana preditiva de fluxo normalizado em função da fase,
   usando funções de base radial gaussianas fixas.

3. [bayesian_trapezoid_transit_hat_p_7_b](bayesian_trapezoid_transit_hat_p_7_b/README.md)  
   M3 - modelo bayesiano trapezoidal para HAT-P-7 b, estimando profundidade,
   centro, duração total aproximada e ingresso/egresso.

4. [model_comparison_hat_p_7_b](model_comparison_hat_p_7_b/README.md)  
   M4 - comparação entre M1, M2 e M3, com parâmetros, diagnósticos, métricas
   preditivas, resíduos e recomendação de resultado principal preliminar.

## Observação

A modelagem está planejada como uma sequência incremental:

- M1: baseline box transit;
- M2: modelo bayesiano preditivo de fluxo em função da fase;
- M3: modelo trapezoidal aproximado;
- M4: comparação entre modelos.

M1 não é conclusão final do TCC. Ele serve como baseline comparativo. A
execução recomendada para interpretar o M1 é:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

M2 também não é conclusão final. Ele serve como modelo preditivo intermediário
para avaliar uma curva suave de fluxo por fase:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/
```

M3 também não é conclusão final. Ele serve como modelo paramétrico aproximado,
mais interpretável que o M2 e mais flexível que o M1:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/
```

M4 não ajusta novo modelo. Ele compara os modelos anteriores e recomenda M3
como resultado principal preliminar:

```text
models/model_comparison/hat_p_7_b/
```

---

# Arquivo 2: `docs/modeling/bayesian_baseline_hat_p_7_b/README.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/README.md
```

# Documentação M1 - Bayesian Baseline - HAT-P-7 b

Esta pasta documenta o primeiro modelo bayesiano preliminar do projeto:

```text
M1 - box transit baseline
```

O modelo estima uma distribuição posterior para a profundidade média do
trânsito e deriva:

```text
Rp/Rs = sqrt(depth)
```

## Como Ler

1. [36_contexto_escopo_e_regras_m1.md](36_contexto_escopo_e_regras_m1.md)  
   Explica o objetivo do M1, seu papel na sequência de modelos e seus limites.

2. [37_pipeline_codigo_execucao_m1.md](37_pipeline_codigo_execucao_m1.md)  
   Documenta script, notebook, dependências, execução e ambiente.

3. [38_dataset_preprocessamento_normalizacao_m1.md](38_dataset_preprocessamento_normalizacao_m1.md)  
   Explica filtros, janela de fase e normalização local.

4. [39_modelo_probabilistico_priors_likelihood_m1.md](39_modelo_probabilistico_priors_likelihood_m1.md)  
   Detalha modelo probabilístico, priors, likelihood e parâmetro derivado.

5. [40_resultados_diagnosticos_m1.md](40_resultados_diagnosticos_m1.md)  
   Resume posterior, R-hat, ESS, posterior predictive e interpretação cautelosa.

6. [41_figuras_tabelas_artefatos_m1.md](41_figuras_tabelas_artefatos_m1.md)  
   Mapeia tabelas, figuras, `trace.nc` e arquivos de configuração.

7. [42_limitacoes_proximos_modelos_m1.md](42_limitacoes_proximos_modelos_m1.md)  
   Explica limitações científicas e computacionais e próximos modelos.

8. [43_como_usar_m1_na_metodologia.md](43_como_usar_m1_na_metodologia.md)  
   Organiza a etapa M1 em linguagem útil para a metodologia do TCC.

9. [44_reexecucao_robusta_nuts_m1.md](44_reexecucao_robusta_nuts_m1.md)  
   Documenta a reexecução robusta com NUTS, o versionamento das runs e a
   comparação com a execução curta Metropolis.

## Artefatos Principais

Script:

```text
scripts/run_bayesian_baseline.py
scripts/run_bayesian_baseline_nuts_robust.py
```

Notebook:

```text
notebooks/03_bayesian_baseline_hat_p_7_b.ipynb
```

Trace:

```text
models/bayesian_baseline/hat_p_7_b/trace.nc
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
```

Relatório:

```text
reports/bayesian_baseline_hat_p_7_b_report.md
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

Tabelas:

```text
tables/bayesian_baseline/hat_p_7_b/
```

Figuras:

```text
figures/bayesian_baseline/hat_p_7_b/
```

## Resultado Resumido Atual

Execução recomendada para interpretação do M1:

```text
002_nuts_robust
```

- Pontos usados: `516`
- Janela de fase: `abs(phase) <= 0,15`
- Normalização: `flux / baseline_median`
- `baseline_median`: `1040715,45`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- Profundidade posterior média: `0,00525258`
- HDI 94% da profundidade: `[0,00464576, 0,00587726]`
- `Rp/Rs` posterior médio: `0,07243869`
- HDI 94% de `Rp/Rs`: `[0,06815983, 0,07666328]`
- Posterior predictive: criado
- Maior R-hat: `1,00088086`
- Menor ESS: `4553,60020940`
- Divergências: `0`

## Atenção

Os artefatos planos originais continuam representando a execução operacional
curta com Metropolis. Eles foram preservados por rastreabilidade em:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
```

Para interpretação científica preliminar do M1, usar a execução:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Mesmo com bons diagnósticos, M1 continua sendo baseline simplificado, não
caracterização física final do sistema.

---

# Arquivo 3: `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/README.md`

```text
Origem: docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/README.md
```

# Documentação M2 - Bayesian Predictive Phase Regression - HAT-P-7 b

Esta pasta documenta o segundo modelo bayesiano do projeto:

```text
M2 - Bayesian Predictive Phase Regression
```

O M2 modela o fluxo normalizado como função suave da fase orbital usando
funções de base radial gaussianas fixas. Ele é mais flexível que o M1 box
transit, mas ainda não é um modelo físico final de trânsito.

## Como Ler

1. [01_contexto_e_objetivo.md](01_contexto_e_objetivo.md)  
   Explica o papel do M2 na sequência de modelos e a diferença conceitual em
   relação ao M1.

2. [02_especificacao_do_modelo.md](02_especificacao_do_modelo.md)  
   Detalha entrada, pré-processamento, normalização, funções de base radial,
   priors, likelihood e amostragem.

3. [03_resultados_e_diagnosticos.md](03_resultados_e_diagnosticos.md)  
   Resume resultados posteriores, curva preditiva, resíduos, diagnósticos
   MCMC, posterior predictive e comparação qualitativa com M1.

4. [04_limitacoes_e_proximos_passos.md](04_limitacoes_e_proximos_passos.md)  
   Documenta limitações científicas e metodológicas do M2 e recomenda M3.

## Artefatos Principais

Script:

```text
scripts/run_bayesian_predictive_phase_regression.py
```

Notebook:

```text
notebooks/04_bayesian_predictive_phase_regression_hat_p_7_b.ipynb
```

Trace:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/trace.nc
```

Configuração:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/model_config.json
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/inference_data_summary.json
```

Tabelas:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/modeling_input_predictive.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/prediction_grid.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/posterior_summary.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/residual_summary.csv
```

Figuras:

```text
figures/bayesian_predictive_phase_regression/hat_p_7_b/
```

Relatório:

```text
reports/bayesian_predictive_phase_regression_hat_p_7_b_report.md
```

## Resultado Resumido

- Pontos usados: `516`
- `n_basis`: `12`
- `basis_width`: `0,035`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- `target_accept` final: `0,99`
- Divergências finais: `0`
- Maior R-hat: `1,00292448`
- Menor ESS: `2269,80467052`
- BFMI mínimo: `0,71467278`
- `predicted_depth` exploratório médio: `0,00721029`
- HDI 94% de `predicted_depth`: `[0,00637213, 0,00809741]`
- `depth` robusto M1 para comparação: `0,00525258`

## Interpretação Curta

O M2 recupera visualmente a depressão do trânsito como curva suave em função da
fase. Ele oferece uma descrição preditiva mais flexível do formato do trânsito
do que o box model do M1.

Ainda assim, M2 não estima diretamente `Rp/Rs`, não incorpora geometria orbital
e não deve ser tratado como caracterização física final.

---

# Arquivo 4: `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/README.md`

```text
Origem: docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/README.md
```

# Documentação M3 - Bayesian Trapezoid Transit - HAT-P-7 b

Esta pasta documenta o terceiro modelo bayesiano do projeto:

```text
M3 - Bayesian Trapezoid Transit
```

O M3 aproxima o trânsito de HAT-P-7 b por uma forma trapezoidal probabilística.
Ele estima explicitamente profundidade, centro do trânsito, duração total,
duração de ingresso/egresso, baseline local e ruído extra. O modelo é mais
interpretável que o M2, porque possui parâmetros geométricos aproximados, e é
mais flexível que o M1, porque não força um trânsito em formato de caixa.

O M3 ainda não é um modelo físico completo de trânsito. Ele não usa limb
darkening, não usa Mandel & Agol, não usa `batman` ou `exoplanet`, e não
incorpora geometria orbital completa. Seu papel é servir como etapa
intermediária entre o baseline box do M1 e uma modelagem física futura.

## Como Ler

1. [01_contexto_e_objetivo.md](01_contexto_e_objetivo.md)  
   Explica o papel do M3 na sequência M1-M4, a pergunta científica respondida
   pelo modelo e os limites da etapa.

2. [02_especificacao_do_modelo.md](02_especificacao_do_modelo.md)  
   Detalha entrada, pré-processamento, normalização, parametrização
   trapezoidal, priors, likelihood, parâmetros derivados e amostragem.

3. [03_resultados_e_diagnosticos.md](03_resultados_e_diagnosticos.md)  
   Resume resultados posteriores, diagnósticos MCMC, posterior predictive,
   resíduos, figuras e comparação qualitativa com M1 e M2.

4. [04_limitacoes_e_proximos_passos.md](04_limitacoes_e_proximos_passos.md)  
   Documenta limitações científicas/metodológicas e recomenda a etapa M4 de
   comparação de modelos.

## Artefatos Principais

Script:

```text
scripts/run_bayesian_trapezoid_transit.py
```

Notebook:

```text
notebooks/05_bayesian_trapezoid_transit_hat_p_7_b.ipynb
```

Trace e configuração:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/trace.nc
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/model_config.json
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/inference_data_summary.json
```

Tabelas:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/modeling_input_trapezoid.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/residual_summary.csv
```

Figuras:

```text
figures/bayesian_trapezoid_transit/hat_p_7_b/
```

Relatório:

```text
reports/bayesian_trapezoid_transit_hat_p_7_b_report.md
```

## Resultado Resumido

- Pontos usados: `516`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- `target_accept` final: `0,90`
- Divergências: `0`
- Maior R-hat: `1,00107423`
- Menor ESS: `4212,34208408`
- BFMI mínimo: `0,85430120`
- Profundidade posterior média: `0,00656620`
- HDI 94% da profundidade: `[0,00594692, 0,00716767]`
- `Rp/Rs` posterior médio: `0,08100761`
- HDI 94% de `Rp/Rs`: `[0,07711627, 0,08466210]`
- Centro posterior médio: `-0,00058156` dias
- Duração total posterior média: `0,17664741` dias, ou `4,23954` horas
- Duração média de ingresso: `0,03697592` dias, ou `0,88742` horas

## Interpretação Curta

O M3 recupera visualmente a depressão do trânsito com uma curva trapezoidal e
apresenta bons diagnósticos de NUTS. Ele fornece uma estimativa posterior de
profundidade e durações aproximadas, tornando-se uma ponte metodológica entre:

- o M1, que é simples e transparente, mas rígido;
- o M2, que é flexível e preditivo, mas menos parametricamente interpretável;
- um modelo físico futuro, que poderá incorporar limb darkening e geometria de
  trânsito mais realista.

O M3 deve ser tratado como modelo paramétrico aproximado, não como
caracterização física final de HAT-P-7 b.

---

# Arquivo 5: `docs/modeling/model_comparison_hat_p_7_b/README.md`

```text
Origem: docs/modeling/model_comparison_hat_p_7_b/README.md
```

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

---

# Arquivo 6: `docs/modeling/bayesian_baseline_hat_p_7_b/36_contexto_escopo_e_regras_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/36_contexto_escopo_e_regras_m1.md
```

# 36 - Contexto, Escopo e Regras do M1

## 1. Contexto

As camadas RAW, Silver e Gold já foram construídas e validadas. A EDA da Gold
indicou que HAT-P-7 b possui trânsito visualmente identificável e que uma
janela de fase mais estreita, `abs(phase) <= 0,15`, é adequada para a primeira
modelagem.

O M1 é o primeiro modelo bayesiano preliminar.

Ele usa:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

sem modificar a Gold.

## 2. Objetivo

O objetivo do M1 é estimar a profundidade média do trânsito como distribuição
posterior e derivar:

```text
Rp/Rs = sqrt(depth)
```

Esse objetivo demonstra a ideia central do TCC:

```text
parâmetros astrofísicos podem ser representados por distribuições posteriores,
não apenas por estimativas pontuais.
```

## 3. Papel na Sequência de Modelos

O M1 é apenas o primeiro modelo:

- M1: baseline box transit;
- M2: modelo bayesiano preditivo de fluxo em função da fase;
- M3: modelo trapezoidal ou fisicamente mais estruturado;
- M4: comparação entre modelos.

M1 serve como comparação inicial.

## 4. O Que M1 Faz

M1:

- lê a janela Gold;
- filtra `abs(phase) <= 0,15`;
- mantém `quality == 0`;
- remove ausências em `flux` e `flux_err`;
- remove `flux_err <= 0`;
- normaliza o fluxo por baseline local;
- define um modelo box-shaped;
- estima `baseline`, `depth` e `extra_sigma`;
- deriva `rp_rs`;
- gera posterior predictive;
- salva trace, tabelas, figuras e relatório.

## 5. O Que M1 Não Faz

M1 não usa:

- batman;
- exoplanet;
- Gaussian Process;
- limb darkening;
- Mandel & Agol;
- modelo trapezoidal;
- ajuste multi-missão;
- TESS;
- ETD;
- modelo hierárquico;
- comparação formal entre modelos.

## 6. Regra de Imutabilidade

M1 não modifica:

```text
data/raw/
data/silver/
data/gold/
```

Ele cria artefatos apenas em:

```text
notebooks/
scripts/
models/
reports/
figures/
tables/
docs/
```

## 7. Interpretação Correta

M1 não é resultado final do TCC.

Ele deve ser lido como:

- baseline bayesiano;
- demonstração metodológica;
- primeira aproximação;
- ponto de comparação para modelos futuros.

Não deve ser usado como caracterização física completa de HAT-P-7 b.

---

# Arquivo 7: `docs/modeling/bayesian_baseline_hat_p_7_b/37_pipeline_codigo_execucao_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/37_pipeline_codigo_execucao_m1.md
```

# 37 - Pipeline, Código e Execução do M1

## 1. Script Operacional Original

Arquivo:

```text
scripts/run_bayesian_baseline.py
```

Função:

- preparar entrada de modelagem;
- construir o modelo PyMC;
- executar amostragem;
- gerar posterior predictive;
- salvar `trace.nc`;
- salvar tabelas;
- salvar figuras;
- salvar relatório;
- salvar roadmap de modelos.

Esse script permanece como registro da primeira implementação completa do M1.
Ele gerou a execução curta operacional, posteriormente versionada como:

```text
001_operational_metropolis
```

## 2. Script Robusto NUTS

Arquivo:

```text
scripts/run_bayesian_baseline_nuts_robust.py
```

Função:

- preservar a execução operacional em `runs/001_operational_metropolis`;
- preparar a mesma entrada de modelagem;
- construir o mesmo modelo PyMC;
- executar NUTS com `2000` draws, `2000` tune e `4` cadeias;
- gerar posterior predictive;
- salvar `trace.nc` versionado;
- salvar tabelas versionadas;
- salvar figuras versionadas;
- gerar relatório robusto;
- gerar comparação entre runs.

## 3. Notebook

Arquivo:

```text
notebooks/03_bayesian_baseline_hat_p_7_b.ipynb
```

O notebook carrega o script e chama:

```python
run_pipeline()
```

Assim, notebook e script usam a mesma lógica.

## 4. Comandos de Execução

Execução operacional original:

```bash
python scripts/run_bayesian_baseline.py
```

No ambiente validado:

```bash
.venv/bin/python scripts/run_bayesian_baseline.py
```

Execução robusta recomendada:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

## 5. Dependências

Dependências principais:

```text
pandas
numpy
matplotlib
pymc
arviz
h5netcdf
h5py
```

Não foi usado `seaborn`.

## 6. Estrutura de Saída

```text
models/
  modeling_roadmap.md
  bayesian_baseline/
    hat_p_7_b/
      trace.nc
      model_config.json
      inference_data_summary.json

reports/
  bayesian_baseline_hat_p_7_b_report.md

figures/
  bayesian_baseline/
    hat_p_7_b/

tables/
  bayesian_baseline/
    hat_p_7_b/
```

Saídas versionadas da robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 7. Ambiente da Execução Operacional Original

O ambiente operacional original não possuía `Python.h`. Isso impediu o backend
C do PyTensor naquela primeira execução.

Para permitir execução, o script configura:

```text
PYTENSOR_FLAGS=base_compiledir=/tmp/pytensor-cache,linker=py,cxx=
MPLCONFIGDIR=/tmp/matplotlib-cache
```

Consequência:

- NUTS 2000/2000 ficou impraticável;
- a execução validada usou `Metropolis`;
- a amostragem foi curta;
- os diagnósticos MCMC ficaram fracos.

## 8. Ambiente da Execução Robusta

A execução robusta usa um ambiente local separado:

```text
.venv-nuts/
```

Esse ambiente usa Python do Conda com `Python.h` disponível e backend C do
PyTensor operacional.

Configuração do PyTensor:

```text
PYTENSOR_FLAGS=base_compiledir=/tmp/pytensor-cache-nuts-robust
MPLCONFIGDIR=/tmp/matplotlib-cache
```

## 9. Configurações Registradas

Arquivo operacional original:

```text
models/bayesian_baseline/hat_p_7_b/model_config.json
```

Resumo:

```text
draws = 300
tune = 300
chains = 4
sampler = Metropolis
requested_draws = 2000
requested_tune = 2000
```

Arquivo robusto:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/model_config.json
```

Resumo robusto:

```text
draws = 2000
tune = 2000
chains = 4
sampler = NUTS
target_accept = 0,9
```

## 10. Política de Reexecução

O script reaproveita `trace.nc` se ele já existir, para evitar repetir a
amostragem quando apenas relatórios, figuras ou tabelas precisam ser
regenerados.

Para a execução robusta, a política adotada foi versionar os resultados em
subpastas `runs/`, preservando a execução operacional e criando a execução
NUTS recomendada sem apagar histórico.

---

# Arquivo 8: `docs/modeling/bayesian_baseline_hat_p_7_b/38_dataset_preprocessamento_normalizacao_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/38_dataset_preprocessamento_normalizacao_m1.md
```

# 38 - Dataset, Pré-processamento e Normalização do M1

## 1. Entrada

Arquivo Gold lido:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas na janela Gold original:

```text
1.664
```

## 2. Filtro de Fase

Critério:

```python
abs(phase) <= 0.15
```

Linhas após filtro:

```text
516
```

## 3. Filtro de Qualidade

Critério:

```python
quality == 0
```

Linhas após filtro:

```text
516
```

Como a janela Gold já vinha da curva filtrada por qualidade, esse filtro não
removeu linhas adicionais.

## 4. Ausências e Erros Inválidos

Foram removidas linhas:

- sem `flux`;
- sem `flux_err`;
- com `flux_err <= 0`.

Resultado:

```text
516 pontos usados no modelo
```

## 5. Região de Baseline Local

Critério:

```python
0.08 <= abs(phase) <= 0.15
```

Pontos nessa região:

```text
232
```

Mediana do baseline:

```text
1040715,45
```

## 6. Normalização

Foram criadas:

```python
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Mediana de `normalized_flux`:

```text
0,993836144164094
```

Mediana de `normalized_flux_err`:

```text
2,487015879316484e-05
```

## 7. Núcleo Inicial de Trânsito

Critério:

```python
abs(phase) <= 0.05
```

Pontos no núcleo:

```text
179
```

Essa região define onde o modelo box aplica:

```text
mu = baseline - depth
```

## 8. Dataset Salvo

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/modeling_input_baseline.csv
```

Colunas:

```text
planet_name
host_star
mission
time
phase
flux
flux_err
normalized_flux
normalized_flux_err
quality
is_core_transit_initial
is_baseline_region
source_gold_path
```

## 9. Interpretação

A normalização local é simples e explícita. Ela não é uma normalização final
para todo o TCC.

Ela serve apenas para colocar o fluxo em escala próxima de `1` e permitir a
interpretação direta de `depth` como queda relativa média.

---

# Arquivo 9: `docs/modeling/bayesian_baseline_hat_p_7_b/39_modelo_probabilistico_priors_likelihood_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/39_modelo_probabilistico_priors_likelihood_m1.md
```

# 39 - Modelo Probabilístico, Priors e Likelihood do M1

## 1. Tipo de Modelo

M1 é um modelo bayesiano simples do tipo:

```text
box-shaped transit
```

Ele aproxima o trânsito como uma queda constante de fluxo dentro de uma janela
central fixa.

## 2. Dados

Para cada observação `i`:

```text
y_i = normalized_flux_i
sigma_obs_i = normalized_flux_err_i
phase_i = phase_i
```

## 3. Regra do Box Transit

Se:

```python
abs(phase_i) <= 0.05
```

então:

```text
mu_i = baseline - depth
```

Caso contrário:

```text
mu_i = baseline
```

## 4. Parâmetros

Parâmetros amostrados:

```text
baseline
depth
extra_sigma
```

Parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

## 5. Priors

Baseline:

```text
baseline ~ Normal(1.0, 0.01)
```

Profundidade:

```text
depth ~ HalfNormal(0.02)
```

Dispersão extra:

```text
extra_sigma ~ HalfNormal(0.005)
```

## 6. Likelihood

Incerteza efetiva:

```text
sigma_eff_i = sqrt(sigma_obs_i^2 + extra_sigma^2)
```

Likelihood:

```text
y_i ~ Normal(mu_i, sigma_eff_i)
```

## 7. Por Que Existe `extra_sigma`

A coluna `normalized_flux_err` representa a incerteza observacional tabular.

Porém, a dispersão real da curva pode ser maior por:

- ruído instrumental residual;
- estrutura de baseline;
- simplificação do modelo box;
- ausência de limb darkening;
- ausência de ingresso/egresso.

`extra_sigma` permite absorver parte dessa dispersão adicional.

## 8. Interpretação de `depth`

`depth` representa a queda média relativa do fluxo no núcleo definido pelo box.

Ela não deve ser interpretada como profundidade física final do trânsito.

## 9. Interpretação de `rp_rs`

O parâmetro:

```text
rp_rs = sqrt(depth)
```

é uma aproximação útil para demonstrar a relação entre profundidade e razão de
raios.

Como M1 ignora efeitos físicos importantes, `rp_rs` também é preliminar.

---

# Arquivo 10: `docs/modeling/bayesian_baseline_hat_p_7_b/40_resultados_diagnosticos_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/40_resultados_diagnosticos_m1.md
```

# 40 - Resultados e Diagnósticos do M1

## 1. Resultado Atual Recomendado

A execução recomendada para interpretação preliminar do M1 é:

```text
002_nuts_robust
```

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
```

Resumo robusto:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat |
|---|---:|---:|---:|---:|
| `baseline` | `0,99597938` | `0,99561513` | `0,99636166` | `1,00044605` |
| `depth` | `0,00525258` | `0,00464576` | `0,00587726` | `1,00034161` |
| `extra_sigma` | `0,00360075` | `0,00339170` | `0,00382274` | `1,00088086` |
| `rp_rs` | `0,07243869` | `0,06815983` | `0,07666328` | `1,00033967` |

Diagnóstico robusto:

```text
max R-hat = 1,00088086
min ESS = 4553,60020940
divergences = 0
BFMI mínimo = 1,10526248
```

Conclusão:

```text
A execução NUTS robusta satisfaz os critérios definidos para uso do M1 como baseline comparativo.
```

Detalhes completos:

```text
docs/modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 2. Resultado Posterior da Execução Operacional Original

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/posterior_summary.csv
```

Resumo:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat |
|---|---:|---:|---:|---:|
| `baseline` | `0,99582952` | `0,99513262` | `0,99617200` | `2,33522345` |
| `depth` | `0,00507495` | `0,00439089` | `0,00577990` | `1,27595378` |
| `extra_sigma` | `0,00360586` | `0,00338010` | `0,00384425` | `1,15526789` |
| `rp_rs` | `0,07118168` | `0,06626377` | `0,07602563` | `1,27595378` |

## 3. Parâmetros Derivados

Arquivo robusto:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
```

Resultado principal robusto:

```text
depth_mean = 0,00525258
rp_rs_mean = 0,07243869
```

Arquivo operacional original:

```text
tables/bayesian_baseline/hat_p_7_b/derived_parameters_summary.csv
```

Resultado principal:

```text
depth_mean = 0,00507495
rp_rs_mean = 0,07118168
```

## 4. Comparação Com a EDA

Profundidade visual aproximada da EDA:

```text
0,0065010087865026
```

Profundidade posterior M1 robusta:

```text
0,00525258
```

Profundidade posterior M1 operacional original:

```text
0,00507495
```

Interpretação:

Os valores têm a mesma ordem de grandeza, mas não são idênticos. Isso é
esperado porque:

- a EDA usa contraste de medianas;
- M1 usa uma região central fixa;
- M1 estima baseline, profundidade e dispersão extra;
- o modelo box é simplificado.

## 5. Diagnósticos MCMC da Execução Operacional Original

Maior R-hat:

```text
2,33522345
```

Menor ESS:

```text
4,25512801
```

Conclusão:

```text
Os diagnósticos não indicam convergência adequada.
```

## 6. Por Que os Diagnósticos Originais Ficaram Fracos

O ambiente operacional original não possuía `Python.h`, impedindo o uso normal
do backend C do PyTensor. Isso tornou NUTS 2000/2000 impraticável naquela
primeira execução.

Para validar o pipeline completo, foi usada uma execução curta com:

```text
sampler = Metropolis
draws = 300
tune = 300
chains = 4
```

Essa execução gera artefatos e demonstra o fluxo M1, mas não deve ser usada
como resultado científico final.

## 7. Posterior Predictive

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/posterior_predictive_summary.csv
```

Status:

```text
created
```

Campos:

```text
phase
observed_flux
predicted_mean
predicted_hdi_3
predicted_hdi_97
residual
```

## 8. Interpretação Cautelosa

M1 cumpriu o objetivo de pipeline:

- preparou os dados;
- especificou o modelo;
- gerou posterior;
- gerou posterior predictive;
- salvou trace e tabelas.

Na execução operacional original, pelos diagnósticos, ele ainda não deve ser
interpretado como inferência final.

Na execução robusta `002_nuts_robust`, os diagnósticos ficaram adequados para o
uso do M1 como baseline comparativo.

## 9. Recomendação Atual

Usar a execução robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Não usar a execução curta Metropolis para conclusões científicas.

---

# Arquivo 11: `docs/modeling/bayesian_baseline_hat_p_7_b/41_figuras_tabelas_artefatos_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/41_figuras_tabelas_artefatos_m1.md
```

# 41 - Figuras, Tabelas e Artefatos do M1

## 1. Figuras

Diretório:

```text
figures/bayesian_baseline/hat_p_7_b/
```

Diretórios versionados:

```text
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

A execução recomendada para leitura visual e interpretação preliminar é
`002_nuts_robust`.

## 2. Input de Modelagem

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/01_modeling_input.png
```

Mostra `normalized_flux` contra `phase` e destaca a região central usada pelo
box transit.

![Input de modelagem](../../../figures/bayesian_baseline/hat_p_7_b/01_modeling_input.png)

## 3. Trace Plot

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/02_trace_plot.png
```

Mostra cadeias de:

- `baseline`;
- `depth`;
- `extra_sigma`;
- `rp_rs`.

Os traços confirmam visualmente o problema já apontado por R-hat/ESS: a
execução curta não convergiu adequadamente.

![Trace plot](../../../figures/bayesian_baseline/hat_p_7_b/02_trace_plot.png)

## 4. Posterior de `depth`

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/03_posterior_depth.png
```

Mostra a distribuição posterior da profundidade média do box.

![Posterior de depth](../../../figures/bayesian_baseline/hat_p_7_b/03_posterior_depth.png)

## 5. Posterior de `Rp/Rs`

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/04_posterior_rp_rs.png
```

Mostra a distribuição posterior do parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

![Posterior de Rp/Rs](../../../figures/bayesian_baseline/hat_p_7_b/04_posterior_rp_rs.png)

## 6. Ajuste Box Por Fase

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/05_model_fit_phase.png
```

Mostra os pontos normalizados e a média posterior do modelo box.

![Ajuste box por fase](../../../figures/bayesian_baseline/hat_p_7_b/05_model_fit_phase.png)

## 7. Posterior Predictive Check

Arquivo:

```text
figures/bayesian_baseline/hat_p_7_b/06_posterior_predictive_check.png
```

Mostra observações, média preditiva e intervalo preditivo.

![Posterior predictive](../../../figures/bayesian_baseline/hat_p_7_b/06_posterior_predictive_check.png)

## 8. Tabelas

Diretório:

```text
tables/bayesian_baseline/hat_p_7_b/
```

Arquivos:

```text
modeling_input_baseline.csv
posterior_summary.csv
derived_parameters_summary.csv
posterior_predictive_summary.csv
model_run_comparison.csv
```

Diretórios versionados:

```text
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

## 9. Artefatos do Modelo

Diretório:

```text
models/bayesian_baseline/hat_p_7_b/
```

Arquivos:

```text
trace.nc
model_config.json
inference_data_summary.json
```

Diretórios versionados:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Artefatos principais da execução robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/model_config.json
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/inference_data_summary.json
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_predictive_summary.csv
```

Relatório robusto:

```text
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 10. Roadmap

Arquivo:

```text
models/modeling_roadmap.md
```

Documenta M1, M2, M3 e M4 como sequência planejada.

---

# Arquivo 12: `docs/modeling/bayesian_baseline_hat_p_7_b/42_limitacoes_proximos_modelos_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/42_limitacoes_proximos_modelos_m1.md
```

# 42 - Limitações e Próximos Modelos do M1

## 1. Limitações Científicas

M1 é limitado porque:

- usa forma box-shaped;
- fixa a meia largura em `0,05` dias;
- ignora limb darkening;
- ignora geometria orbital;
- ignora ingresso e egresso;
- não estima duração;
- não estima inclinação orbital;
- não usa modelo físico Mandel & Agol;
- não usa dados TESS ou ETD;
- não compara missões;
- não trata ruído correlacionado.

## 2. Limitação Computacional da Primeira Execução

A primeira execução operacional ocorreu em ambiente sem `Python.h`.

Isso impediu o backend C do PyTensor e tornou NUTS 2000/2000 impraticável.

A execução validada usou:

```text
Metropolis
300 draws
300 tune
4 chains
```

Os diagnósticos ficaram fracos:

```text
max R-hat = 2,33522345
min ESS = 4,25512801
```

Essa execução foi preservada como:

```text
001_operational_metropolis
```

## 3. Reexecução Robusta

A limitação computacional foi tratada criando um ambiente local separado:

```text
.venv-nuts/
```

Nesse ambiente, `Python.h` está disponível e NUTS foi executado com:

```text
draws = 2000
tune = 2000
chains = 4
target_accept = 0,9
```

Resultado diagnóstico:

```text
max R-hat = 1,00088086
min ESS = 4553,60020940
divergences = 0
```

A execução robusta foi salva como:

```text
002_nuts_robust
```

## 4. Consequência

Os valores da execução operacional curta são úteis para:

- testar o pipeline;
- validar artefatos;
- demonstrar a lógica bayesiana;
- orientar o próximo modelo.

Eles não devem ser usados como conclusão final.

Os valores da execução robusta podem ser usados como resultado do baseline M1,
desde que a interpretação permaneça limitada ao modelo box-shaped.

## 5. Próximo Passo Imediato

Usar `002_nuts_robust` como baseline comparativo e avançar para M2.

## 6. M2

M2 deve ser um modelo bayesiano preditivo de fluxo em função da fase.

Possibilidades:

- spline bayesiana;
- base radial;
- regressão suave;
- GP simples, se interpretável e computacionalmente viável.

## 7. M3

M3 deve introduzir estrutura de trânsito mais realista:

- profundidade;
- duração;
- ingresso;
- egresso;
- talvez baseline local inclinado.

Um modelo trapezoidal é um bom candidato antes de partir para modelos físicos
mais completos.

## 8. M4

M4 deve comparar modelos:

- posterior predictive checks;
- erro preditivo;
- LOO;
- WAIC, se apropriado.

## 9. Papel Final do M1

Mesmo que M1 seja reexecutado com bons diagnósticos, ele continuará sendo um
baseline.

A conclusão astrofísica final deve depender da comparação com modelos mais
estruturados.

---

# Arquivo 13: `docs/modeling/bayesian_baseline_hat_p_7_b/43_como_usar_m1_na_metodologia.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/43_como_usar_m1_na_metodologia.md
```

# 43 - Como Usar o M1 na Metodologia

## 1. Função Metodológica

M1 pode ser descrito como o primeiro modelo bayesiano preliminar, usado para
demonstrar a passagem de uma curva Gold para uma distribuição posterior de um
parâmetro astrofísico simplificado.

## 2. Texto Possível

```text
Como primeiro baseline, foi especificado um modelo bayesiano do tipo box
transit para a curva de luz faseada de HAT-P-7 b. O modelo estima uma
profundidade média de trânsito e deriva a razão aproximada Rp/Rs pela relação
Rp/Rs = sqrt(depth).
```

## 3. Pré-processamento

```text
Foram utilizados pontos da janela Gold com abs(phase) <= 0,15, mantendo apenas
pontos com quality igual a zero e removendo observações sem fluxo, sem erro de
fluxo ou com erro não positivo. O fluxo foi normalizado pela mediana de uma
região local de baseline definida por 0,08 <= abs(phase) <= 0,15.
```

## 4. Modelo

```text
Dentro de uma região central fixa, abs(phase) <= 0,05, o modelo assume fluxo
médio baseline - depth. Fora dessa região, assume fluxo médio baseline. A
likelihood é normal, com incerteza efetiva composta pelo erro observacional e
um termo extra de dispersão.
```

## 5. Priors

```text
Foram usados priors fracos e centrados em uma curva normalizada: baseline ~
Normal(1, 0,01), depth ~ HalfNormal(0,02) e extra_sigma ~ HalfNormal(0,005).
```

## 6. Resultado

```text
A execução robusta com NUTS produziu uma profundidade posterior média de
0,00525258, com HDI 94% entre 0,00464576 e 0,00587726. A razão Rp/Rs derivada
teve média posterior de 0,07243869, com HDI 94% entre 0,06815983 e
0,07666328.
```

## 7. Como Mencionar a Execução Operacional Anterior

```text
Uma execução operacional inicial com Metropolis curto foi usada para validar o
pipeline de artefatos, mas seus diagnósticos MCMC foram inadequados. Por isso,
ela foi preservada apenas para rastreabilidade e substituída, para
interpretação do M1, por uma reexecução robusta com NUTS 2000/2000 e quatro
cadeias.
```

## 8. Como Mencionar os Diagnósticos

```text
A reexecução robusta apresentou R-hat máximo de 1,00088086, ESS mínimo de
4553,60020940 e zero divergências, atendendo aos critérios definidos para uso
do M1 como baseline comparativo.
```

## 9. Ponte Para Próximos Modelos

```text
O M1 estabelece um baseline interpretável para comparação posterior. As
próximas etapas devem considerar modelos com maior flexibilidade preditiva e
maior estrutura física, como modelos suaves em fase ou trapezoidais.
```

## 10. O Que Evitar

Evite escrever que:

- M1 caracterizou fisicamente HAT-P-7 b;
- a razão `Rp/Rs` é resultado final;
- o modelo box representa toda a física do trânsito;
- o box transit representa a física completa do trânsito.

## 11. Frase-Síntese

```text
O M1 robusto demonstrou a construção de uma inferência bayesiana preliminar
para a profundidade de trânsito, produzindo distribuições posteriores para
depth e Rp/Rs com diagnósticos MCMC adequados. Ainda assim, por usar um modelo
box-shaped simplificado, ele deve ser tratado como baseline comparativo, não
como caracterização física final de HAT-P-7 b.
```

---

# Arquivo 14: `docs/modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md`

```text
Origem: docs/modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md
```

# 44 - Reexecução Robusta NUTS do M1

## 1. Papel Desta Subetapa

Esta documentação registra a reexecução robusta do mesmo modelo M1:

```text
M1 - Bayesian Baseline Box Transit
```

Ela não cria um novo modelo. A especificação probabilística, a entrada Gold e
as regras de pré-processamento permanecem as mesmas. A mudança relevante é
operacional e inferencial:

- a execução curta anterior foi preservada como `001_operational_metropolis`;
- a nova execução robusta foi criada como `002_nuts_robust`;
- a execução robusta usa NUTS com `2000` draws, `2000` tune e `4` cadeias;
- a execução robusta é a recomendada para interpretação do M1 como baseline.

## 2. Motivação

A primeira execução validada do M1 foi útil para testar a cadeia completa de
artefatos, mas não era cientificamente interpretável.

O ambiente anterior não tinha `Python.h`, o que impediu o backend C do
PyTensor. Por isso, o pipeline foi validado com Metropolis curto:

```text
sampler = Metropolis
draws = 300
tune = 300
chains = 4
```

Diagnósticos da execução curta:

```text
max R-hat = 2,33522345
min ESS = 4,25512801
```

Esses valores indicavam ausência de convergência adequada.

## 3. Ambiente Robusto Criado

Foi criado um ambiente local separado:

```text
.venv-nuts/
```

Esse ambiente foi construído a partir do Python do Conda, que possui headers de
desenvolvimento disponíveis.

Resumo do ambiente usado:

```text
Python = 3.13.13
Python executable = .venv-nuts/bin/python
Python.h disponível = True
PyMC = 6.0.1
ArviZ = 1.2.0
PyTensor = 3.0.7
PyTensor flags = base_compiledir=/tmp/pytensor-cache-nuts-robust
```

O backend C do PyTensor foi testado com uma amostragem NUTS mínima antes da
execução robusta. O teste funcionou sem forçar `linker=py`.

## 4. Comando de Execução

Script criado:

```text
scripts/run_bayesian_baseline_nuts_robust.py
```

Comando usado:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

Esse script:

- preserva os artefatos planos antigos em `runs/001_operational_metropolis`;
- executa o M1 com NUTS;
- salva a nova execução em `runs/002_nuts_robust`;
- gera posterior predictive;
- salva tabelas, figuras, trace, configuração e relatório;
- cria comparação direta entre as duas execuções.

## 5. Entrada e Pré-processamento Mantidos

Entrada principal:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Regras preservadas:

```text
abs(phase) <= 0,15
quality == 0
flux não ausente
flux_err não ausente
flux_err > 0
```

Normalização local:

```text
baseline region = 0,08 <= abs(phase) <= 0,15
baseline_median = 1040715,45
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Região central fixa do trânsito no M1:

```text
abs(phase) <= 0,05
```

Resumo da entrada robusta:

| Métrica | Valor |
|---|---:|
| Linhas na janela Gold original | `1664` |
| Linhas após `abs(phase) <= 0,15` | `516` |
| Linhas após `quality == 0` | `516` |
| Linhas usadas no modelo | `516` |
| Pontos na região de baseline | `232` |
| Pontos no núcleo do trânsito | `179` |

## 6. Modelo Probabilístico Mantido

O M1 continua sendo um modelo box-shaped:

```text
mu_i = baseline - depth, se abs(phase_i) <= 0,05
mu_i = baseline, caso contrário
```

Priors:

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
extra_sigma ~ HalfNormal(0.005)
```

Likelihood:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(mu_i, sigma_eff_i)
```

Parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

## 7. Configuração NUTS

Configuração usada:

```text
sampler = NUTS
draws = 2000
tune = 2000
chains = 4
cores = 4
target_accept = 0,9
random_seed = 42
```

Não houve necessidade de repetir com `target_accept = 0,95`, porque a execução
com `0,9` terminou com zero divergências.

Durante a adaptação, o stdout registrou um `RuntimeWarning` de overflow em
`quadpotential.py`. Esse aviso não foi ocultado. A avaliação final foi feita
pelos diagnósticos MCMC salvos, que ficaram adequados para o baseline M1:

```text
divergences = 0
max R-hat = 1,00088086
min ESS = 4553,60020940
BFMI mínimo = 1,10526248
```

## 8. Resultados Posteriores Robustos

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
```

Resumo:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat | ESS bulk | ESS tail |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | `0,99597938` | `0,99561513` | `0,99636166` | `1,00044605` | `4613,18299016` | `5213,13706106` |
| `depth` | `0,00525258` | `0,00464576` | `0,00587726` | `1,00034161` | `4553,60020940` | `4599,27286730` |
| `extra_sigma` | `0,00360075` | `0,00339170` | `0,00382274` | `1,00088086` | `6017,13283284` | `5859,49044795` |
| `rp_rs` | `0,07243869` | `0,06815983` | `0,07666328` | `1,00033967` | `4553,60020940` | `4599,27286730` |

Parâmetros derivados:

```text
depth_mean = 0,00525258
depth_hdi_3 = 0,00464576
depth_hdi_97 = 0,00587726
rp_rs_mean = 0,07243869
rp_rs_hdi_3 = 0,06815983
rp_rs_hdi_97 = 0,07666328
```

## 9. Comparação Entre Execuções

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/model_run_comparison.csv
```

Comparação essencial:

| Run | Sampler | Draws | Tune | R-hat máximo | ESS mínimo | Divergências | Recomendado |
|---|---|---:|---:|---:|---:|---:|---|
| `001_operational_metropolis` | `Metropolis` | `300` | `300` | `2,33522345` | `4,25512801` | não aplicável | `False` |
| `002_nuts_robust` | `NUTS` | `2000` | `2000` | `1,00088086` | `4553,60020940` | `0` | `True` |

Conclusão:

```text
002_nuts_robust substitui 001_operational_metropolis para interpretação do M1.
```

A execução Metropolis curta permanece preservada apenas para rastreabilidade e
histórico operacional.

## 10. Artefatos Criados

Modelos:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Tabelas:

```text
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
tables/bayesian_baseline/hat_p_7_b/model_run_comparison.csv
```

Figuras:

```text
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Relatório:

```text
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 11. Figuras Principais

Trace plot robusto:

![Trace plot robusto](../../../figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/02_trace_plot.png)

Posterior robusta de `depth`:

![Posterior robusta de depth](../../../figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/03_posterior_depth.png)

Ajuste box por fase:

![Ajuste box robusto](../../../figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/05_model_fit_phase.png)

Posterior predictive check:

![Posterior predictive robusto](../../../figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/06_posterior_predictive_check.png)

## 12. Integridade das Camadas de Dados

Antes e depois da execução robusta, foi calculada uma impressão digital dos
arquivos em:

```text
data/raw/
data/silver/
data/gold/
```

Resultado:

```text
arquivos antes = 446
arquivos depois = 446
arquivos adicionados = 0
arquivos ausentes = 0
checksums alterados = 0
timestamps alterados = 0
```

Portanto, a reexecução robusta não modificou RAW, Silver ou Gold.

## 13. Interpretação Metodológica

Agora o M1 pode ser descrito como um baseline bayesiano efetivamente amostrado
com NUTS e diagnósticos adequados.

O resultado principal a reportar para o M1 é:

```text
depth = 0,00525258, HDI 94% [0,00464576, 0,00587726]
Rp/Rs = 0,07243869, HDI 94% [0,06815983, 0,07666328]
```

Ainda assim, essa interpretação deve ser limitada ao escopo do M1. O modelo:

- usa caixa fixa;
- não modela limb darkening;
- não modela ingresso e egresso;
- não estima duração;
- não incorpora geometria orbital completa;
- não é caracterização física final do planeta.

## 14. Próximo Passo

O próximo passo recomendado é usar `002_nuts_robust` como baseline comparativo
para o M2.

O M2 deve melhorar a capacidade preditiva da curva em função da fase, mantendo
a rastreabilidade dos dados Gold e permitindo comparação posterior com o M1 por
posterior predictive checks e métricas adequadas.

---

# Arquivo 15: `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/01_contexto_e_objetivo.md`

```text
Origem: docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/01_contexto_e_objetivo.md
```

# 01 - Contexto e Objetivo do M2

## 1. Contexto Acadêmico

O projeto de TCC investiga como a inferência bayesiana pode ser aplicada à
estimação de parâmetros físicos em sistemas astrofísicos sob incerteza
observacional, com ênfase em curvas de luz de trânsitos de exoplanetas.

Após as etapas RAW, Silver, Gold, EDA e M1, o projeto passa para o segundo
modelo bayesiano:

```text
M2 - Bayesian Predictive Phase Regression
```

## 2. Sequência de Modelos

A sequência planejada é:

```text
M1 - baseline bayesiano box-shaped transit
M2 - regressão bayesiana preditiva de fluxo por fase
M3 - modelo trapezoidal ou físico aproximado
M4 - comparação formal entre modelos
```

M2 não substitui M1. Ele responde outra pergunta.

## 3. Pergunta do M1

M1 pergunta:

```text
Qual a profundidade média do trânsito assumindo uma forma box?
```

M1 estima `depth` como parâmetro explícito e deriva:

```text
Rp/Rs = sqrt(depth)
```

Na execução robusta, M1 usou NUTS com bons diagnósticos e produziu:

```text
depth_mean = 0,00525258
Rp/Rs_mean = 0,07243869
```

## 4. Pergunta do M2

M2 pergunta:

```text
Qual função suave de fluxo em função da fase é suportada pelos dados?
```

O foco muda:

- de uma profundidade paramétrica box-shaped;
- para uma função suave preditiva `f(phase)`.

## 5. Objetivo do M2

O objetivo do M2 é produzir:

1. curva preditiva média;
2. intervalo de credibilidade da função latente;
3. intervalo preditivo para observações futuras;
4. avaliação de resíduos;
5. comparação qualitativa com M1.

## 6. Entrada

Entrada principal:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Essa entrada já foi preparada na Gold e diagnosticada na EDA.

## 7. O Que o M2 Não Faz

M2 não faz:

- Gaussian Process;
- batman;
- exoplanet;
- Mandel & Agol;
- limb darkening;
- modelo trapezoidal;
- ajuste multi-missão;
- TESS;
- ETD;
- comparação formal LOO/WAIC;
- inferência física final.

## 8. Papel na Metodologia

Na metodologia do TCC, M2 pode ser descrito como uma etapa intermediária entre:

- um baseline paramétrico extremamente simples, M1;
- e um modelo mais estruturado fisicamente, M3.

Ele demonstra que a inferência bayesiana pode descrever não apenas um parâmetro
pontual, mas uma função preditiva com incerteza associada.

---

# Arquivo 16: `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/02_especificacao_do_modelo.md`

```text
Origem: docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/02_especificacao_do_modelo.md
```

# 02 - Especificação do Modelo M2

## 1. Script

Arquivo:

```text
scripts/run_bayesian_predictive_phase_regression.py
```

Comando validado:

```bash
.venv-nuts/bin/python scripts/run_bayesian_predictive_phase_regression.py
```

O ambiente `.venv-nuts` foi usado porque já havia sido validado na execução
robusta do M1 com backend adequado para NUTS.

## 2. Notebook

Arquivo:

```text
notebooks/04_bayesian_predictive_phase_regression_hat_p_7_b.ipynb
```

O notebook é reprodutível e chama o script principal para gerar os mesmos
artefatos.

## 3. Entrada

Arquivo Gold:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Essa entrada não foi modificada.

## 4. Pré-processamento

Regras aplicadas:

```text
abs(phase) <= 0,15
quality == 0
phase não ausente
flux não ausente
flux_err não ausente
flux_err > 0
```

Resumo:

| Métrica | Valor |
|---|---:|
| Linhas na janela Gold original | `1664` |
| Linhas após filtro de fase | `516` |
| Linhas após filtro de qualidade | `516` |
| Linhas usadas no M2 | `516` |

## 5. Normalização

A normalização foi mantida igual à do M1 para comparabilidade.

Região de baseline:

```text
0,08 <= abs(phase) <= 0,15
```

Mediana usada:

```text
baseline_median = 1040715,45
```

Transformações:

```text
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Arquivo gerado:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/modeling_input_predictive.csv
```

## 6. Funções de Base Radial

M2 usa funções de base radial gaussianas fixas, não Gaussian Process.

Para cada centro `c_k`:

```text
phi_k(x) = exp(-0.5 * ((x - c_k) / width)^2)
```

Configuração:

```text
n_basis = 12
basis_width = 0,035
centers = linspace(-0,15, 0,15, 12)
```

Arquivo com o grid e valores das bases:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/prediction_grid.csv
```

Figura:

![Funções de base radial](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/02_basis_functions.png)

## 7. Função Latente

A função latente é:

```text
f(x) = intercept + soma_k w_k * phi_k(x)
```

onde:

- `x` é a fase orbital;
- `phi_k(x)` é a k-ésima função radial;
- `w_k` é o peso correspondente;
- `intercept` representa o nível médio global em escala normalizada.

## 8. Priors

Priors usados:

```text
intercept ~ Normal(1.0, 0.01)
weight_sigma ~ HalfNormal(0.01)
weights_raw_k ~ Normal(0, 1)
weights_k = weights_raw_k * weight_sigma
extra_sigma ~ HalfNormal(0.005)
```

Foi usada parametrização não centrada para os pesos:

```text
weights = weights_raw * weight_sigma
```

Essa escolha reduz problemas geométricos típicos de modelos hierárquicos.

## 9. Likelihood

Para cada ponto observado:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(f(phase_i), sigma_eff_i)
```

O termo `extra_sigma` captura dispersão adicional não explicada pelo erro
observacional tabulado.

## 10. Grid Preditivo

Grid:

```text
phase_grid = linspace(-0,15, 0,15, 300)
```

Para cada amostra posterior foi calculada a função latente nesse grid.

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
```

Campos:

```text
phase
latent_mean
latent_hdi_3
latent_hdi_97
predictive_mean
predictive_hdi_3
predictive_hdi_97
```

## 11. Profundidade Exploratória Derivada

M2 não estima `depth` como parâmetro primário.

Para comparação qualitativa com M1, foi derivada uma profundidade exploratória:

```text
predicted_depth = baseline_level - min(f_grid)
```

com:

```text
baseline_level = média de f_grid nas bordas, abs(phase) >= 0,08
```

Esse valor deve ser tratado apenas como diagnóstico preditivo. Ele não é
equivalente físico direto ao `depth` paramétrico do M1.

## 12. Amostragem

Configuração inicial:

```text
draws = 2000
tune = 2000
chains = 4
target_accept = 0,9
random_seed = 42
```

Tentativas:

```text
target_accept = 0,90 -> 21 divergências
target_accept = 0,95 -> 3 divergências
target_accept = 0,99 -> 0 divergências
```

A execução final registrada usa:

```text
target_accept = 0,99
```

## 13. Saídas

Modelo:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/
```

Tabelas:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/
```

Figuras:

```text
figures/bayesian_predictive_phase_regression/hat_p_7_b/
```

Relatório:

```text
reports/bayesian_predictive_phase_regression_hat_p_7_b_report.md
```

---

# Arquivo 17: `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/03_resultados_e_diagnosticos.md`

```text
Origem: docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/03_resultados_e_diagnosticos.md
```

# 03 - Resultados e Diagnósticos do M2

## 1. Artefatos de Resultado

Resumo inferencial:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/inference_data_summary.json
```

Configuração:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/model_config.json
```

Trace:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/trace.nc
```

## 2. Diagnósticos MCMC

Resultado final após `target_accept = 0,99`:

| Métrica | Valor |
|---|---:|
| Pontos usados | `516` |
| Draws | `2000` |
| Tune | `2000` |
| Chains | `4` |
| R-hat máximo | `1,00292448` |
| ESS mínimo | `2269,80467052` |
| Divergências | `0` |
| Aceitação média | `0,98810751` |
| BFMI mínimo | `0,71467278` |

Conclusão:

```text
Os diagnósticos satisfazem os critérios definidos para uso do M2 como modelo preditivo intermediário.
```

## 3. Parâmetros Principais

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/posterior_summary.csv
```

Resumo:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat |
|---|---:|---:|---:|---:|
| `intercept` | `0,99596322` | `0,99131842` | `1,00207021` | `1,00256981` |
| `weight_sigma` | `0,00367651` | `0,00179424` | `0,00716827` | `1,00292448` |
| `extra_sigma` | `0,00321035` | `0,00303038` | `0,00340200` | `1,00093715` |

Os pesos `weights[k]` estão documentados linha a linha no arquivo CSV, junto
com o índice e o centro da função de base radial.

Figura dos pesos:

![Pesos posteriores](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/04_posterior_weights.png)

## 4. Trace Plot

Figura:

![Trace plot M2](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/03_trace_plot.png)

O trace plot inclui:

- `intercept`;
- `weight_sigma`;
- `extra_sigma`;
- pesos selecionados.

## 5. Curva Latente

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
```

Figura:

![Curva latente M2](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/05_predictive_curve_latent.png)

Leitura:

- a média da função latente acompanha a depressão do trânsito;
- o intervalo da função latente é mais estreito que o intervalo preditivo de
  observações futuras;
- a curva é mais suave e flexível que o box model do M1.

## 6. Posterior Predictive

Figura:

![Posterior predictive M2](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/06_posterior_predictive_observations.png)

Cobertura aproximada do intervalo preditivo de 94% nos pontos observados:

```text
1,000000
```

Essa cobertura alta indica que o intervalo preditivo cobre os dados, mas
também sugere que o termo `extra_sigma` domina a largura preditiva. Isso deve
ser considerado na comparação futura entre modelos.

## 7. Resíduos

Arquivo:

```text
tables/bayesian_predictive_phase_regression/hat_p_7_b/residual_summary.csv
```

Métricas:

| Métrica | Valor |
|---|---:|
| Média dos resíduos | `-0,00000214` |
| Mediana dos resíduos | `0,00234046` |
| Desvio padrão dos resíduos | `0,00318197` |
| Média dos resíduos padronizados | `-0,00066448` |
| Desvio padrão dos resíduos padronizados | `0,99112818` |

Figura:

![Resíduos por fase](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/07_residuals_by_phase.png)

## 8. Profundidade Exploratória Derivada

M2 não possui `depth` como parâmetro primário.

Foi derivado apenas para diagnóstico:

```text
predicted_depth = baseline_level - min(f_grid)
```

Resultado:

| Métrica | Valor |
|---|---:|
| `predicted_depth_mean` | `0,00721029` |
| `predicted_depth_hdi_3` | `0,00637213` |
| `predicted_depth_hdi_97` | `0,00809741` |
| `baseline_level_mean` | `0,99709191` |
| `min_latent_flux_mean` | `0,98988161` |
| mediana da fase de mínimo | `0,02558528` |

Interpretação:

```text
Esse valor é exploratório e não deve ser tratado como equivalente físico direto ao depth do M1.
```

## 9. Comparação Qualitativa com M1

M1 robusto:

```text
depth_mean = 0,00525258
```

M2:

```text
predicted_depth_mean = 0,00721029
```

Diferença:

```text
M2 - M1 = 0,00195771
```

Figura:

![Comparação M2 com M1](../../../figures/bayesian_predictive_phase_regression/hat_p_7_b/08_comparison_with_m1.png)

Leitura:

- M1 representa o trânsito por uma caixa fixa;
- M2 permite uma curva suave;
- M2 parece descrever melhor a forma visual do trânsito;
- a comparação de profundidades é apenas qualitativa porque as definições são
  diferentes.

## 10. Respostas Diretas

A curva preditiva recupera visualmente o trânsito?

```text
Sim. A depressão próxima da fase zero aparece na curva latente média.
```

O intervalo preditivo cobre razoavelmente os dados?

```text
Sim. A cobertura aproximada do intervalo preditivo de 94% nos pontos observados foi 1,0.
```

A profundidade exploratória do M2 é próxima da depth do M1?

```text
Está na mesma ordem de grandeza, mas é maior. A diferença é esperada porque M2 usa mínimo da curva suave, não uma caixa fixa.
```

O M2 melhora a descrição visual do formato do trânsito em relação ao box model?

```text
Sim, qualitativamente, por permitir uma transição suave em fase.
```

O M2 deve ser usado como modelo físico final?

```text
Não.
```

---

# Arquivo 18: `docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/04_limitacoes_e_proximos_passos.md`

```text
Origem: docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/04_limitacoes_e_proximos_passos.md
```

# 04 - Limitações e Próximos Passos do M2

## 1. Limitações Científicas

M2 é um modelo bayesiano preditivo flexível, mas não é modelo físico final.

Ele não incorpora:

- geometria orbital;
- limb darkening;
- ingresso e egresso como parâmetros explícitos;
- duração física do trânsito;
- modelo Mandel & Agol;
- batman;
- exoplanet;
- Gaussian Process;
- ajuste multi-missão;
- dados TESS;
- dados ETD;
- estrutura hierárquica.

## 2. Limitação da Profundidade Derivada

O M2 não estima `depth` diretamente.

A profundidade exploratória:

```text
predicted_depth = baseline_level - min(f_grid)
```

é útil para comparar visualmente a depressão da curva com o M1, mas não deve
ser interpretada como equivalente físico exato ao `depth` paramétrico do M1.

Também não se deve derivar `Rp/Rs` a partir desse `predicted_depth` nesta etapa.

## 3. Limitação da Base Radial

As funções de base radial são fixas:

```text
n_basis = 12
basis_width = 0,035
```

Essa escolha controla a flexibilidade do modelo.

Consequências:

- bases muito largas podem suavizar demais a curva;
- bases muito estreitas podem aproximar ruído;
- o número de bases afeta a capacidade preditiva;
- a escolha ainda é metodológica, não física.

## 4. Limitação Preditiva

O intervalo preditivo cobre os dados observados, mas a cobertura de `1,0` para
um intervalo de 94% sugere que o termo `extra_sigma` deixa a predição
conservadora.

Isso não é necessariamente um erro, mas deve ser discutido como:

- possível ruído extra real;
- simplificação do modelo;
- consequência de não modelar efeitos instrumentais ou correlação temporal;
- argumento para comparar modelos no M4.

## 5. Interpretação Correta

M2 pode ser usado para dizer:

```text
O fluxo normalizado foi modelado como função suave da fase, permitindo estimar uma curva preditiva média e sua incerteza.
```

M2 não deve ser usado para dizer:

```text
O raio planetário foi estimado fisicamente pelo M2.
```

ou:

```text
M2 é o modelo final de trânsito.
```

## 6. Relação Com M1

M1:

- estima uma profundidade explícita;
- assume forma box;
- é simples e interpretável.

M2:

- não estima profundidade explícita;
- estima uma função suave;
- descreve melhor a forma visual da curva;
- produz incerteza preditiva.

Os dois modelos são complementares.

## 7. Próximo Modelo Recomendado

O próximo passo é M3:

```text
modelo trapezoidal ou físico aproximado
```

M3 deve buscar uma ponte entre:

- interpretabilidade física;
- flexibilidade de forma;
- estimação explícita de parâmetros relacionados ao trânsito.

Parâmetros candidatos para M3:

- profundidade;
- duração;
- meia largura;
- tempo de ingresso/egresso;
- baseline local;
- dispersão extra.

## 8. Comparação Formal Futuramente

M4 deve comparar M1, M2 e M3 usando:

- posterior predictive checks;
- erro preditivo;
- LOO;
- WAIC, se as hipóteses forem adequadas.

Essa comparação não foi feita no M2 porque o objetivo desta etapa era construir
e diagnosticar o modelo preditivo, não selecionar formalmente o melhor modelo.

## 9. Uso na Metodologia

Na metodologia do TCC, o M2 pode ser descrito como:

```text
um modelo bayesiano preditivo intermediário, baseado em funções de base radial gaussianas, usado para representar a curva de luz faseada como uma função suave com incerteza posterior.
```

Ele ajuda a demonstrar que a inferência bayesiana pode produzir não só
distribuições posteriores de parâmetros, mas também distribuições sobre funções
e predições futuras.

---

# Arquivo 19: `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/01_contexto_e_objetivo.md`

```text
Origem: docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/01_contexto_e_objetivo.md
```

# 01 - Contexto e Objetivo do M3

## 1. Contexto no Projeto

O projeto investiga como a inferência bayesiana pode ser aplicada à estimação
de parâmetros físicos em sistemas astrofísicos sob incerteza observacional, com
ênfase em curvas de luz de trânsitos de exoplanetas.

As etapas anteriores já organizaram os dados em camadas e modelos progressivos:

- RAW: coleta pública bruta e rastreável.
- Silver: padronização tabular e validação técnica.
- Gold: seleção de HAT-P-7 b e preparação da curva Kepler.
- EDA: diagnóstico visual da janela de trânsito.
- M1: baseline bayesiano box-shaped transit.
- M2: regressão bayesiana preditiva suave em função da fase.

O M3 é a terceira etapa de modelagem. Ele lê a Gold, preserva M1/M2 intactos e
cria novos artefatos em `models/`, `tables/`, `figures/`, `reports/`,
`notebooks/`, `scripts/` e `docs/`.

## 2. Pergunta Respondida pelo M3

O M3 responde:

```text
Quais são as distribuições posteriores da profundidade, duração e
ingresso/egresso se o trânsito for aproximado por uma forma trapezoidal?
```

Essa pergunta é diferente das perguntas dos modelos anteriores:

- M1 pergunta qual profundidade média é suportada por uma forma box-shaped
  fixa.
- M2 pergunta qual função suave de fluxo por fase é suportada pelos dados.
- M3 pergunta qual conjunto de parâmetros trapezoidais aproximados explica a
  curva faseada.

## 3. Por que um Modelo Trapezoidal

Um trânsito real não é perfeitamente retangular. Há uma queda de fluxo durante
o ingresso, um trecho próximo ao fundo do trânsito e uma subida de fluxo no
egresso.

O M3 introduz essa estrutura sem chegar ainda à complexidade de modelos físicos
completos. Ele permite estimar:

- `baseline`: nível médio de fluxo normalizado fora do trânsito;
- `depth`: queda de fluxo associada ao trânsito;
- `center`: deslocamento do centro do trânsito em relação à fase zero;
- `half_duration`: meia duração total aproximada;
- `ingress_duration`: duração aproximada de ingresso ou egresso;
- `extra_sigma`: dispersão adicional além do erro fotométrico reportado;
- `rp_rs`: razão aproximada `Rp/Rs = sqrt(depth)`.

## 4. Entrada Principal

Arquivo Gold usado:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Esse arquivo foi criado na camada Gold a partir da curva Kepler de HAT-P-7 b,
com fase orbital calculada e janela de trânsito inicial.

O M3 aplica internamente a janela recomendada pela EDA:

```text
abs(phase) <= 0.15
```

## 5. Regra de Imutabilidade

O M3 não modifica:

```text
data/raw/
data/silver/
data/gold/
```

Também não modifica os artefatos de M1 e M2. A comparação com M1 e M2 é feita
por leitura dos artefatos existentes:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
```

## 6. Artefatos Criados

Script:

```text
scripts/run_bayesian_trapezoid_transit.py
```

Notebook:

```text
notebooks/05_bayesian_trapezoid_transit_hat_p_7_b.ipynb
```

Modelo:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/
```

Tabelas:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/
```

Figuras:

```text
figures/bayesian_trapezoid_transit/hat_p_7_b/
```

Relatório:

```text
reports/bayesian_trapezoid_transit_hat_p_7_b_report.md
```

## 7. Papel Metodológico

Na metodologia do TCC, o M3 pode ser descrito como uma etapa de refinamento
paramétrico intermediário.

Ele preserva a lógica bayesiana central:

```text
os parâmetros de interesse não são representados por valores pontuais únicos,
mas por distribuições posteriores condicionadas aos dados e às hipóteses do modelo.
```

Ao mesmo tempo, o M3 deixa explícito que suas conclusões dependem da hipótese
trapezoidal simplificada.

---

# Arquivo 20: `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/02_especificacao_do_modelo.md`

```text
Origem: docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/02_especificacao_do_modelo.md
```

# 02 - Especificação do Modelo M3

## 1. Entrada e Dataset Efetivo

Entrada original:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Dataset salvo para modelagem:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/modeling_input_trapezoid.csv
```

O dataset efetivo contém `516` pontos após filtros e normalização.

## 2. Pré-processamento

Foram aplicadas as mesmas regras de M1 e M2 para manter comparabilidade:

1. Manter somente linhas com `abs(phase) <= 0.15`.
2. Manter somente `quality == 0`, quando a coluna existe.
3. Remover linhas sem `phase`.
4. Remover linhas sem `flux`.
5. Remover linhas sem `flux_err`.
6. Remover linhas com `flux_err <= 0`.
7. Normalizar por baseline local.

Resumo da entrada:

| Etapa | Linhas |
|---|---:|
| Janela Gold original | `1664` |
| Após filtro de fase | `516` |
| Após filtro de qualidade | `516` |
| Após filtro de ausentes | `516` |
| Após filtro de `flux_err > 0` | `516` |
| Linhas usadas | `516` |

## 3. Normalização Local

A região de baseline local foi definida como:

```text
0.08 <= abs(phase) <= 0.15
```

A mediana do fluxo nessa região foi:

```text
baseline_median = 1040715.45
```

As colunas normalizadas foram criadas como:

```text
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Essa normalização é a mesma usada em M1 e M2. Ela não altera a Gold; apenas
gera o dataset derivado de modelagem do M3.

## 4. Variáveis do Modelo

Variável de entrada:

```text
x_i = phase_i
```

Variável observada:

```text
y_i = normalized_flux_i
```

Incerteza observacional:

```text
sigma_obs_i = normalized_flux_err_i
```

## 5. Forma Trapezoidal

O modelo define a distância em fase ao centro do trânsito:

```text
d_i = abs(x_i - center)
```

A forma trapezoidal é:

```text
transit_shape_i = clip((half_duration - d_i) / ingress_duration, 0, 1)
```

Média esperada:

```text
mu_i = baseline - depth * transit_shape_i
```

Essa construção gera:

- fora do trânsito: `transit_shape = 0`, portanto `mu = baseline`;
- fundo do trânsito: `transit_shape = 1`, portanto `mu = baseline - depth`;
- ingresso/egresso: `0 < transit_shape < 1`, com transição linear.

## 6. Parametrização Estável do Ingresso

A restrição importante é:

```text
ingress_duration < half_duration
```

Em vez de amostrar `ingress_duration` diretamente com uma restrição dura, foi
usada uma fração:

```text
ingress_fraction ~ Beta(2, 5)
ingress_duration = ingress_fraction * half_duration
```

Essa parametrização é mais estável para NUTS, porque evita regiões inválidas
do espaço de parâmetros.

## 7. Priors

Priors usados:

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
center ~ Normal(0.0, 0.01)
half_duration ~ Uniform(0.03, 0.12)
ingress_fraction ~ Beta(2, 5)
extra_sigma ~ HalfNormal(0.005)
```

Leitura dos priors:

- `baseline` fica concentrado próximo de 1, porque o fluxo foi normalizado.
- `depth` é positivo por construção.
- `center` permite pequeno deslocamento em torno da fase zero.
- `half_duration` cobre durações totais aproximadas entre `0.06` e `0.24`
  dias.
- `ingress_fraction` favorece ingressos menores que a duração total, mas sem
  fixar um valor rígido.
- `extra_sigma` captura dispersão adicional não explicada por `flux_err`.

## 8. Likelihood

A incerteza efetiva combina erro observacional e ruído extra:

```text
sigma_eff_i = sqrt(sigma_obs_i^2 + extra_sigma^2)
```

Likelihood:

```text
y_i ~ Normal(mu_i, sigma_eff_i)
```

## 9. Parâmetros Derivados

O modelo calcula:

```text
rp_rs = sqrt(depth)
full_duration = 2 * half_duration
flat_duration = 2 * maximum(half_duration - ingress_duration, 0)
ingress_egress_total = 2 * ingress_duration
```

Esses parâmetros são salvos no trace e resumidos em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
```

## 10. Amostragem

Configuração final:

```text
sampler = NUTS
draws = 2000
tune = 2000
chains = 4
cores = 4
target_accept = 0.90
random_seed = 42
```

O script possui política de retry:

1. tenta `target_accept = 0.90`;
2. se houver divergências, tenta `0.95`;
3. se ainda houver divergências, tenta `0.99`.

Nesta execução, não foi necessário retry.

## 11. Posterior Predictive

O posterior predictive foi calculado para os pontos observados e resumido em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
```

O resumo contém:

- `phase`;
- `observed_flux`;
- `predicted_mean`;
- `predicted_hdi_3`;
- `predicted_hdi_97`;
- `residual`.

## 12. Grade Trapezoidal

Foi criada uma grade:

```text
phase_grid = linspace(-0.15, 0.15, 300)
```

Para cada amostra posterior, a curva trapezoidal foi avaliada nessa grade. O
resumo foi salvo em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
```

Campos principais:

- `phase`;
- `model_mean`;
- `model_hdi_3`;
- `model_hdi_97`;
- `predictive_mean`;
- `predictive_hdi_3`;
- `predictive_hdi_97`.

---

# Arquivo 21: `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/03_resultados_e_diagnosticos.md`

```text
Origem: docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/03_resultados_e_diagnosticos.md
```

# 03 - Resultados e Diagnósticos do M3

## 1. Artefatos de Resultado

Resumo inferencial:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/inference_data_summary.json
```

Configuração:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/model_config.json
```

Trace:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/trace.nc
```

## 2. Diagnósticos MCMC

Resultado final:

| Métrica | Valor |
|---|---:|
| Pontos usados | `516` |
| Draws | `2000` |
| Tune | `2000` |
| Chains | `4` |
| `target_accept` final | `0,90` |
| R-hat máximo | `1,00107423` |
| ESS mínimo | `4212,34208408` |
| Divergências | `0` |
| Aceitação média | `0,90800918` |
| BFMI mínimo | `0,85430120` |

Conclusão:

```text
Os diagnósticos satisfazem os critérios definidos para interpretar o M3 como
modelo trapezoidal aproximado.
```

## 3. Parâmetros Principais

Arquivo:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_summary.csv
```

Resumo:

| Parâmetro | Média | HDI 3% | HDI 97% | R-hat | ESS bulk | ESS tail |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | `0,99730624` | `0,99690219` | `0,99771396` | `1,00098607` | `5725,46753276` | `5562,56225124` |
| `depth` | `0,00656620` | `0,00594692` | `0,00716767` | `1,00038945` | `5995,33013887` | `5614,30368942` |
| `center` | `-0,00058156` | `-0,00373031` | `0,00260803` | `1,00011232` | `6882,63367449` | `5538,93234534` |
| `half_duration` | `0,08832370` | `0,08218581` | `0,09584455` | `1,00080861` | `4830,81184246` | `4260,83957835` |
| `ingress_duration` | `0,03697592` | `0,02548890` | `0,05114678` | `1,00107423` | `4560,39444976` | `4212,34208408` |
| `extra_sigma` | `0,00319567` | `0,00301355` | `0,00338942` | `1,00006640` | `7350,45288943` | `5260,39266575` |
| `rp_rs` | `0,08100761` | `0,07711627` | `0,08466210` | `1,00042132` | `5995,33013887` | `5614,30368942` |

## 4. Parâmetros Derivados

Arquivo:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
```

Principais resultados:

| Parâmetro derivado | Média | HDI 3% | HDI 97% |
|---|---:|---:|---:|
| `depth` | `0,00656620` | `0,00594692` | `0,00716767` |
| `Rp/Rs` | `0,08100761` | `0,07711627` | `0,08466210` |
| `center` dias | `-0,00058156` | `-0,00373031` | `0,00260803` |
| duração total dias | `0,17664741` | `0,16437161` | `0,19168911` |
| duração total horas | `4,23954` | - | - |
| ingresso dias | `0,03697592` | - | - |
| ingresso horas | `0,88742` | - | - |
| fundo plano dias | `0,10269557` | - | - |
| ingresso+egresso dias | `0,07395184` | - | - |

Figura de posteriores de profundidade e duração:

![Posteriores de profundidade e duração](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/03_posterior_depth_duration.png)

Figura de `Rp/Rs`:

![Posterior de Rp/Rs](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/04_posterior_rp_rs.png)

## 5. Trace Plot

Figura:

![Trace plot M3](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/02_trace_plot.png)

O trace plot inclui:

- `baseline`;
- `depth`;
- `center`;
- `half_duration`;
- `ingress_duration`;
- `extra_sigma`;
- `rp_rs`.

## 6. Curva Trapezoidal Ajustada

Arquivo:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
```

Figura:

![Curva trapezoidal M3](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/05_trapezoid_fit_phase.png)

Leitura:

- a curva média representa a depressão do trânsito com transições lineares;
- o centro posterior fica próximo de zero;
- a forma é mais flexível que a caixa do M1;
- a forma é mais parametricamente interpretável que a curva suave do M2.

## 7. Posterior Predictive

Arquivo:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
```

Figura:

![Posterior predictive M3](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/06_posterior_predictive_check.png)

Cobertura aproximada do intervalo preditivo de 94% nos pontos observados:

```text
1,000000
```

Essa cobertura indica que o intervalo preditivo cobre os dados observados. Como
em M2, a largura preditiva deve ser interpretada junto com `extra_sigma`, pois
o ruído extra ajuda a absorver dispersão não capturada pela forma média.

## 8. Resíduos

Arquivo:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/residual_summary.csv
```

Métricas:

| Métrica | Valor |
|---|---:|
| Média dos resíduos | `-0,00000396` |
| Mediana dos resíduos | `0,00259044` |
| Desvio padrão dos resíduos | `0,00317806` |
| Média dos resíduos padronizados | `-0,00123703` |
| Desvio padrão dos resíduos padronizados | `0,99446006` |

Figura:

![Resíduos por fase M3](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/07_residuals_by_phase.png)

## 9. Comparação Qualitativa com M1 e M2

M1 robusto:

```text
depth_mean = 0,00525258
Rp/Rs mean = 0,07243869
```

M2:

```text
predicted_depth exploratório = 0,00721029
```

M3:

```text
depth_mean = 0,00656620
Rp/Rs mean = 0,08100761
```

Figura:

![Comparação M1 M2 M3](../../../figures/bayesian_trapezoid_transit/hat_p_7_b/08_comparison_m1_m2_m3.png)

Leitura:

- M1 é mais rígido e tende a representar o trânsito por uma caixa fixa.
- M2 é mais flexível e segue uma curva suave, mas sua profundidade é derivada
  de forma exploratória.
- M3 fica entre os dois: estima parâmetros interpretáveis e permite
  ingresso/egresso.
- A profundidade M3 ficou entre a profundidade paramétrica do M1 e a
  profundidade exploratória do M2.

## 10. Respostas Diretas

O modelo convergiu?

```text
Sim. Os diagnósticos de NUTS foram adequados para a interpretação do M3.
```

Houve divergências?

```text
Não. Divergências = 0.
```

Qual foi a profundidade posterior?

```text
depth_mean = 0,00656620, HDI 94% [0,00594692, 0,00716767].
```

Qual foi `Rp/Rs` posterior?

```text
Rp/Rs mean = 0,08100761, HDI 94% [0,07711627, 0,08466210].
```

Qual foi a duração total aproximada?

```text
full_duration_mean = 0,17664741 dias, aproximadamente 4,23954 horas.
```

Qual foi o centro posterior do trânsito?

```text
center_mean = -0,00058156 dias, com HDI 94% [-0,00373031, 0,00260803].
```

O M3 descreve melhor o formato do trânsito que o box M1?

```text
Qualitativamente sim, porque inclui ingresso e egresso.
```

O M3 é mais interpretável que o M2?

```text
Sim, porque possui parâmetros explícitos de profundidade, centro e duração.
```

O M3 deve ser tratado como modelo físico final?

```text
Não. Ele ainda é uma aproximação paramétrica simplificada.
```

---

# Arquivo 22: `docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/04_limitacoes_e_proximos_passos.md`

```text
Origem: docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/04_limitacoes_e_proximos_passos.md
```

# 04 - Limitações e Próximos Passos do M3

## 1. Limitações Científicas

O M3 é mais estruturado que M1 e mais interpretável que M2, mas ainda é um
modelo aproximado.

Ele não incorpora:

- limb darkening;
- geometria orbital completa;
- inclinação orbital;
- razão semi-eixo maior/raio estelar;
- excentricidade;
- argumento do periastro;
- integração por tempo de exposição;
- modelo Mandel & Agol;
- `batman`;
- `exoplanet`;
- Gaussian Process;
- ajuste multi-missão;
- TESS;
- ETD;
- comparação formal LOO/WAIC.

Portanto, os parâmetros estimados devem ser lidos como aproximações sob uma
hipótese trapezoidal, não como caracterização física final de HAT-P-7 b.

## 2. Limitações Estatísticas

O modelo assume:

- independência condicional dos erros;
- likelihood Gaussiana;
- erro efetivo `sqrt(flux_err^2 + extra_sigma^2)`;
- janela fixa `abs(phase) <= 0.15`;
- normalização local por mediana;
- forma simétrica em torno do centro posterior;
- ingresso e egresso com mesma duração;
- profundidade constante no fundo do trânsito.

Essas hipóteses são úteis para um modelo intermediário, mas podem ser relaxadas
em etapas futuras.

## 3. Limitações de Interpretação

O parâmetro:

```text
rp_rs = sqrt(depth)
```

é uma razão aproximada. Em um modelo físico completo, a profundidade observada
depende de outros elementos, como limb darkening, geometria e integração da
exposição.

A duração total estimada:

```text
full_duration = 2 * half_duration
```

também deve ser interpretada como duração trapezoidal aproximada, não como uma
medida física final de contato primeiro-quarto.

## 4. Relação com M1 e M2

M1:

- fornece um baseline transparente;
- estima profundidade diretamente;
- ignora ingresso e egresso.

M2:

- descreve uma curva suave;
- é mais flexível;
- não possui profundidade física direta.

M3:

- estima profundidade e durações;
- introduz ingresso/egresso;
- permanece simples o bastante para documentação metodológica;
- serve como melhor ponte para modelos físicos futuros.

## 5. Próximo Passo: M4

O próximo passo recomendado é:

```text
M4 - Comparação de Modelos
```

O M4 deve comparar M1, M2 e M3 usando:

- posterior predictive checks;
- métricas de erro preditivo;
- análise comparativa de resíduos;
- consistência entre profundidades;
- possivelmente LOO ou WAIC, se as hipóteses forem adequadas.

O M4 não deve apagar as diferenças conceituais entre os modelos. A comparação
deve deixar claro que:

- M1 estima uma profundidade sob hipótese box;
- M2 estima uma curva preditiva suave;
- M3 estima uma forma trapezoidal paramétrica aproximada.

## 6. Como Usar na Metodologia

Na metodologia do TCC, o M3 pode ser descrito como:

```text
um modelo bayesiano paramétrico aproximado, usado para representar o trânsito
por uma forma trapezoidal e estimar distribuições posteriores de profundidade,
centro e durações, preservando a incerteza observacional.
```

Pontos úteis para o texto metodológico:

- os dados vêm da Gold de HAT-P-7 b;
- a janela de fase foi definida pela EDA;
- a normalização local foi mantida igual à de M1 e M2;
- a forma trapezoidal foi escolhida como compromisso entre simplicidade e
  interpretabilidade;
- os diagnósticos de NUTS indicaram convergência adequada;
- o resultado não é caracterização física final.

## 7. Arquivos para Consulta

Relatório técnico:

```text
reports/bayesian_trapezoid_transit_hat_p_7_b_report.md
```

Resumo posterior:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_summary.csv
```

Resumo de parâmetros derivados:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
```

Curva trapezoidal:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
```

Posterior predictive:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
```

Resíduos:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/residual_summary.csv
```

---

# Arquivo 23: `docs/modeling/model_comparison_hat_p_7_b/01_contexto_e_objetivo.md`

```text
Origem: docs/modeling/model_comparison_hat_p_7_b/01_contexto_e_objetivo.md
```

# 01 - Contexto e Objetivo do M4

## 1. Contexto no Projeto

O projeto possui uma sequência incremental de modelos bayesianos para a curva
de trânsito de HAT-P-7 b:

- M1: baseline bayesiano box-shaped;
- M2: regressão bayesiana preditiva em fase;
- M3: trânsito bayesiano trapezoidal aproximado;
- M4: comparação dos modelos anteriores.

O M4 é uma etapa de síntese. Ele não cria uma nova hipótese de trânsito e não
estima novos parâmetros por amostragem. Em vez disso, lê os resultados já
gerados e organiza uma comparação metodológica.

## 2. Perguntas Centrais

O M4 responde:

1. Como os pressupostos de cada modelo afetam a profundidade inferida?
2. Qual modelo descreve melhor o formato observado do trânsito?
3. Qual modelo apresenta melhor comportamento preditivo?
4. Qual modelo oferece melhor equilíbrio entre interpretabilidade e
   flexibilidade?
5. Qual modelo deve ser usado como resultado principal preliminar do TCC?

## 3. Entradas

M1:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/derived_parameters_summary.csv
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_predictive_summary.csv
```

M2:

```text
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/trace.nc
tables/bayesian_predictive_phase_regression/hat_p_7_b/posterior_summary.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/predictive_curve_summary.csv
tables/bayesian_predictive_phase_regression/hat_p_7_b/residual_summary.csv
```

M3:

```text
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/trace.nc
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
tables/bayesian_trapezoid_transit/hat_p_7_b/residual_summary.csv
```

Gold, apenas como referência de origem:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

## 4. Saídas

O M4 cria novos artefatos somente em:

```text
notebooks/
scripts/
models/
reports/
figures/
tables/
docs/
```

Ele não modifica:

```text
data/raw/
data/silver/
data/gold/
```

Também não modifica as pastas específicas de M1, M2 e M3.

## 5. Comando de Execução

```bash
.venv-nuts/bin/python scripts/run_model_comparison.py
```

O notebook equivalente é:

```text
notebooks/06_model_comparison_hat_p_7_b.ipynb
```

## 6. Papel Metodológico

Na metodologia do TCC, o M4 pode ser usado para demonstrar que a escolha do
modelo não é apenas operacional, mas epistemológica:

- modelos diferentes impõem formas diferentes ao trânsito;
- essas formas alteram a profundidade inferida;
- flexibilidade e interpretabilidade não crescem necessariamente juntas;
- diagnósticos MCMC bons são necessários, mas não suficientes para declarar
  um modelo como fisicamente final.

O M4 organiza essa discussão sem transformar o resultado em conclusão
astrofísica definitiva.

---

# Arquivo 24: `docs/modeling/model_comparison_hat_p_7_b/02_criterios_de_comparacao.md`

```text
Origem: docs/modeling/model_comparison_hat_p_7_b/02_criterios_de_comparacao.md
```

# 02 - Critérios de Comparação do M4

## 1. Comparação de Parâmetros

Arquivo:

```text
tables/model_comparison/hat_p_7_b/parameter_comparison.csv
```

Campos principais:

- `model_id`;
- `model_name`;
- `model_family`;
- `depth_type`;
- `depth_mean`;
- `depth_hdi_3`;
- `depth_hdi_97`;
- `rp_rs_mean`;
- `rp_rs_hdi_3`;
- `rp_rs_hdi_97`;
- `duration_hours`;
- `ingress_hours`;
- `interpretation_note`.

Critério:

- M1 e M3 possuem profundidade direta de modelo.
- M2 possui `predicted_depth` exploratório derivado da curva preditiva.
- M2 não possui `Rp/Rs` físico direto.

## 2. Comparação de Diagnósticos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/diagnostic_comparison.csv
```

Campos:

- `sampler`;
- `draws`;
- `tune`;
- `chains`;
- `target_accept`;
- `r_hat_max`;
- `ess_min`;
- `divergences`;
- `bfmi_min`;
- `diagnostic_status`;
- `notes`.

Critério operacional:

```text
diagnostic_status = good
```

quando:

- `R-hat <= 1,01`;
- `ESS mínimo >= 1000`;
- `divergências = 0`.

## 3. Métricas Preditivas Simples

Arquivo:

```text
tables/model_comparison/hat_p_7_b/predictive_metric_comparison.csv
```

Métricas calculadas:

- RMSE;
- MAE;
- erro absoluto mediano;
- média dos resíduos;
- desvio padrão dos resíduos;
- desvio padrão dos resíduos padronizados;
- cobertura de intervalo preditivo 94%;
- número de pontos.

Essas métricas são simples e diagnósticas. Elas não substituem comparação
bayesiana formal por LOO/WAIC.

## 4. Comparação de Resíduos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/residual_comparison.csv
```

Formato longo:

- `model_id`;
- `phase`;
- `observed_flux`;
- `predicted_mean`;
- `residual`;
- `standardized_residual`;
- `normalized_flux_err`.

Para M1, a escala de resíduo padronizado foi reconstruída usando:

```text
sqrt(normalized_flux_err^2 + extra_sigma_mean^2)
```

Para M2 e M3, os resíduos padronizados foram lidos das tabelas já geradas.

## 5. LOO/WAIC Opcional

Arquivo:

```text
tables/model_comparison/hat_p_7_b/loo_waic_comparison.csv
```

O script tenta usar ArviZ para calcular LOO e WAIC, mas apenas se o arquivo
`trace.nc` contiver grupo `log_likelihood`.

Resultado atual:

```text
M1: unavailable
M2: unavailable
M3: unavailable
```

Motivo:

```text
trace.nc does not contain a log_likelihood group
```

O M4 registra essa limitação explicitamente e não inventa valores.

## 6. Recomendação de Modelo

Arquivo:

```text
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
```

Critérios:

- `interpretability_score`;
- `predictive_score`;
- `physical_structure_score`;
- `diagnostic_score`;
- `complexity_score`;
- `recommended_role`.

Papéis:

- `baseline_reference`;
- `predictive_description`;
- `primary_preliminary_result`;
- `future_extension_needed`, quando aplicável em etapas futuras.

Resultado:

- M1: `baseline_reference`;
- M2: `predictive_description`;
- M3: `primary_preliminary_result`.

## 7. Figuras

Diretório:

```text
figures/model_comparison/hat_p_7_b/
```

Figuras:

1. `01_depth_comparison.png`;
2. `02_rp_rs_comparison.png`;
3. `03_model_fit_comparison.png`;
4. `04_residual_comparison.png`;
5. `05_predictive_interval_comparison.png`;
6. `06_diagnostic_comparison.png`;
7. `07_model_complexity_interpretability_map.png`.

---

# Arquivo 25: `docs/modeling/model_comparison_hat_p_7_b/03_resultados_comparativos.md`

```text
Origem: docs/modeling/model_comparison_hat_p_7_b/03_resultados_comparativos.md
```

# 03 - Resultados Comparativos do M4

## 1. Profundidade

Arquivo:

```text
tables/model_comparison/hat_p_7_b/parameter_comparison.csv
```

| Modelo | Tipo | Profundidade média | HDI 3% | HDI 97% |
|---|---|---:|---:|---:|
| M1 | direta | `0,00525258` | `0,00464576` | `0,00587726` |
| M2 | exploratória | `0,00721029` | `0,00637213` | `0,00809741` |
| M3 | direta aproximada | `0,00656620` | `0,00594692` | `0,00716767` |

Figura:

![Comparação de profundidade](../../../figures/model_comparison/hat_p_7_b/01_depth_comparison.png)

Leitura:

- M1 produz a menor profundidade, consistente com a rigidez do box model.
- M2 produz a maior profundidade, mas ela é exploratória e derivada da curva
  suave.
- M3 fica entre M1 e M2, com profundidade direta dentro de um modelo
  trapezoidal.

## 2. Rp/Rs

| Modelo | Rp/Rs médio | HDI 3% | HDI 97% |
|---|---:|---:|---:|
| M1 | `0,07243869` | `0,06815983` | `0,07666328` |
| M2 | não estimado diretamente | - | - |
| M3 | `0,08100761` | `0,07711627` | `0,08466210` |

Figura:

![Comparação de Rp/Rs](../../../figures/model_comparison/hat_p_7_b/02_rp_rs_comparison.png)

Leitura:

M2 não aparece como estimativa física de `Rp/Rs`, porque seu
`predicted_depth` não é parâmetro direto do modelo.

## 3. Diagnósticos MCMC

Arquivo:

```text
tables/model_comparison/hat_p_7_b/diagnostic_comparison.csv
```

| Modelo | R-hat máximo | ESS mínimo | Divergências | Status |
|---|---:|---:|---:|---|
| M1 | `1,00088086` | `4553,60020940` | `0` | `good` |
| M2 | `1,00292448` | `2269,80467052` | `0` | `good` |
| M3 | `1,00107423` | `4212,34208408` | `0` | `good` |

Figura:

![Comparação de diagnósticos](../../../figures/model_comparison/hat_p_7_b/06_diagnostic_comparison.png)

Leitura:

Todos os modelos tiveram diagnósticos adequados pelos critérios definidos. M1
tem o menor R-hat máximo; M3 tem ESS mínimo alto e divergências zero; M2 exigiu
`target_accept = 0,99`, mas a execução final também ficou adequada.

## 4. Métricas Preditivas

Arquivo:

```text
tables/model_comparison/hat_p_7_b/predictive_metric_comparison.csv
```

| Modelo | RMSE | MAE | Cobertura 94% |
|---|---:|---:|---:|
| M1 | `0,00358754` | `0,00327957` | `0,961240` |
| M2 | `0,00317888` | `0,00312563` | `1,000000` |
| M3 | `0,00317499` | `0,00315311` | `1,000000` |

Figura:

![Intervalos preditivos](../../../figures/model_comparison/hat_p_7_b/05_predictive_interval_comparison.png)

Leitura:

M2 e M3 ficam praticamente empatados em RMSE, com pequena vantagem numérica
para M3. M1 tem erro maior, o que é esperado pela forma box-shaped fixa.

## 5. Ajustes Visuais

Figura:

![Comparação dos ajustes](../../../figures/model_comparison/hat_p_7_b/03_model_fit_comparison.png)

Leitura:

- M1 é útil como referência simples.
- M2 acompanha suavemente a depressão observada.
- M3 adiciona estrutura de ingresso e egresso sem abrir mão de parâmetros
  interpretáveis.

## 6. Resíduos

Arquivo:

```text
tables/model_comparison/hat_p_7_b/residual_comparison.csv
```

Figura:

![Comparação de resíduos](../../../figures/model_comparison/hat_p_7_b/04_residual_comparison.png)

Leitura:

Os resíduos são comparáveis em escala entre os modelos. M1 mostra o efeito da
forma rígida; M2 e M3 reduzem a diferença média entre forma esperada e pontos
observados.

## 7. Mapa Conceitual

Figura:

![Mapa flexibilidade interpretabilidade](../../../figures/model_comparison/hat_p_7_b/07_model_complexity_interpretability_map.png)

Leitura:

- M1: baixa flexibilidade, interpretabilidade moderada.
- M2: alta flexibilidade, menor interpretabilidade física direta.
- M3: flexibilidade intermediária e maior interpretabilidade física aproximada.

---

# Arquivo 26: `docs/modeling/model_comparison_hat_p_7_b/04_recomendacao_e_limitacoes.md`

```text
Origem: docs/modeling/model_comparison_hat_p_7_b/04_recomendacao_e_limitacoes.md
```

# 04 - Recomendação e Limitações do M4

## 1. Recomendação Principal

Arquivo:

```text
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
```

Recomendação:

```text
M3 - primary_preliminary_result
```

Justificativa:

- possui profundidade direta;
- deriva `Rp/Rs`;
- estima duração total aproximada;
- estima ingresso/egresso;
- apresenta diagnósticos MCMC bons;
- tem desempenho preditivo simples competitivo;
- é mais interpretável fisicamente que M2;
- é mais flexível que M1.

## 2. Papel de Cada Modelo

M1:

```text
baseline_reference
```

Uso recomendado:

- demonstrar uma primeira inferência bayesiana transparente;
- servir como comparação mínima;
- mostrar como uma hipótese rígida afeta a profundidade.

M2:

```text
predictive_description
```

Uso recomendado:

- descrever a curva suave de fluxo por fase;
- avaliar incerteza preditiva;
- ilustrar flexibilidade maior que M1;
- não reportar `predicted_depth` como profundidade física final.

M3:

```text
primary_preliminary_result
```

Uso recomendado:

- reportar resultado preliminar principal;
- discutir profundidade, `Rp/Rs`, duração total e ingresso/egresso;
- reforçar que o modelo ainda é aproximado.

## 3. Por que M3, e não M1

M1 é extremamente útil como baseline, mas sua forma box-shaped ignora ingresso
e egresso. Isso torna o modelo simples demais para ser a principal síntese
preliminar do formato observado.

M3 preserva a profundidade direta, mas adiciona estrutura temporal ao trânsito.

## 4. Por que M3, e não M2

M2 descreve bem a curva suave, mas não estima diretamente `Rp/Rs`.

Seu `predicted_depth` é:

```text
baseline_level - min(f_grid)
```

Esse valor é diagnóstico e exploratório. Ele não deve ser tratado como o mesmo
tipo de parâmetro que `depth` em M1 ou M3.

M3, por outro lado, possui `depth` como parâmetro do modelo.

## 5. Limitações do M4

O M4 ainda não faz comparação formal completa porque:

- os traces atuais não possuem grupo `log_likelihood`;
- LOO/WAIC ficaram indisponíveis;
- os modelos têm objetivos diferentes;
- M2 não possui profundidade física direta;
- todos os modelos usam apenas Kepler;
- nenhum modelo incorpora limb darkening;
- nenhum modelo incorpora geometria orbital completa;
- nenhum modelo usa Mandel & Agol.

## 6. Limitação da Recomendação

A recomendação de M3 é:

```text
principal resultado preliminar
```

Não é:

```text
caracterização física final de HAT-P-7 b
```

Essa distinção é importante para o artigo/TCC.

## 7. Próximo Passo

O próximo passo recomendado é avançar para um modelo físico ou semi-físico:

- incorporar limb darkening;
- usar `batman` ou uma formulação Mandel & Agol;
- gerar `log_likelihood` no `InferenceData`;
- comparar modelos com LOO/WAIC quando adequado;
- avaliar integração por tempo de exposição;
- preservar M1, M2 e M3 como referências comparativas.

## 8. Como Usar na Metodologia

Na metodologia, o M4 pode ser descrito como:

```text
uma etapa de comparação posterior aos ajustes bayesianos, destinada a avaliar
como diferentes pressupostos de forma do trânsito alteram a profundidade,
o comportamento preditivo e a interpretabilidade dos parâmetros.
```

Esse texto ajuda a defender que a escolha do resultado preliminar não foi
arbitrária: ela considerou diagnóstico, predição e interpretação física.

---
