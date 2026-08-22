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
