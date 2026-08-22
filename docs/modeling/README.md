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
