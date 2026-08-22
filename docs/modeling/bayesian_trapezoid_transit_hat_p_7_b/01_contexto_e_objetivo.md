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
