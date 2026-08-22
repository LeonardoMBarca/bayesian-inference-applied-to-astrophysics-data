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
