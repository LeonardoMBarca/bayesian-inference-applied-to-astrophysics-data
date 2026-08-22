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
