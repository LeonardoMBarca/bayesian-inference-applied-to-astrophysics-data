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
