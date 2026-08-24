# Documentação M3 - Bayesian Trapezoid Transit - HAT-P-7 b

> Snapshot histórico específico de HAT-P-7 b. Não descreve o M5 atual.

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
