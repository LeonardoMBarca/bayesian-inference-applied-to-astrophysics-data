# 28 - Como Usar a Gold na Metodologia

## 1. Função Metodológica da Gold

Na metodologia do TCC, a Gold pode ser apresentada como a etapa de preparação
analítica inicial.

Depois da coleta RAW e da padronização Silver, a Gold reduz o problema para um
caso de estudo:

```text
HAT-P-7 b observado pela missão Kepler
```

Essa redução é necessária porque a inferência bayesiana futura não será feita
simultaneamente em todos os planetas e fontes coletadas. Ela precisa começar
com um dataset controlado.

## 2. Como Descrever a Seleção

Uma descrição possível:

```text
A seleção do alvo Gold foi conduzida por meio de um scorecard técnico
construído a partir dos resumos Silver. O scorecard considerou disponibilidade
de missões, presença de fluxo corrigido, quantidade de pontos com flag de
qualidade igual a zero e completude de parâmetros orbitais necessários para
faseamento.
```

Em seguida:

```text
HAT-P-7 b foi selecionado porque possuía dados Kepler e TESS, fluxo PDCSAP,
período orbital, tempo central de trânsito e mais de mil pontos com quality
igual a zero. TrES-2 b permaneceu como candidato backup por apresentar
disponibilidade semelhante.
```

## 3. Como Descrever a Preparação da Curva

Uma descrição possível:

```text
A curva Gold primária foi construída a partir da tabela Silver MAST/Kepler de
HAT-P-7 b. Foi selecionado o fluxo PDCSAP como variável principal e o erro
PDCSAP correspondente como incerteza observacional associada. Linhas sem tempo
ou fluxo foram removidas por inviabilidade técnica de uso temporal.
```

Depois:

```text
Foi criada uma versão filtrada por qualidade, mantendo apenas pontos com
quality igual a zero. Esse filtro utiliza flags instrumentais da missão e não
constitui remoção estatística de outliers.
```

## 4. Como Descrever o Faseamento

Uma descrição possível:

```text
O faseamento orbital foi realizado usando o período orbital e o tempo central
de trânsito do catálogo NASA consolidado na Silver. Como os tempos Kepler são
expressos em escala relativa ao BJDREF dos FITS, o tempo central da NASA foi
convertido para a escala temporal da curva antes da aplicação da fórmula de
fase.
```

Fórmula:

```python
phase = ((time - transit_midpoint_used + 0.5 * period) % period) - 0.5 * period
```

## 5. Como Descrever a Janela Gold Inicial

Uma descrição possível:

```text
A janela Gold inicial foi definida em torno da fase zero com meia largura
igual a três vezes a duração catalográfica do trânsito, respeitando o critério
mínimo configurado no pipeline. Para HAT-P-7 b, essa regra resultou em uma
janela de aproximadamente ±0,48527 dias e 1.664 pontos.
```

É importante acrescentar:

```text
Essa janela foi criada como ponto de partida para diagnóstico e modelagem
futura. A definição final da janela de modelagem depende da etapa EDA.
```

## 6. O Que Enfatizar

Na metodologia, vale enfatizar:

- separação clara entre coleta, padronização e preparação analítica;
- rastreabilidade da Gold até a Silver e a RAW;
- uso de critérios explícitos;
- ausência de dados sintéticos;
- ausência de inferência nesta etapa;
- preservação de incerteza observacional via `flux_err`;
- documentação de conversão temporal;
- documentação de filtros aplicados.

## 7. O Que Evitar

Evite escrever que a Gold:

- estimou parâmetros físicos;
- ajustou o trânsito;
- validou cientificamente o modelo;
- produziu resultado bayesiano;
- encontrou posterior;
- comparou com literatura;
- removeu outliers por inferência;
- normalizou a curva de forma final.

Essas afirmações pertenceriam a etapas posteriores e não foram feitas.

## 8. Ponte Para a EDA

A Gold terminou com o arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

A etapa EDA leu esse arquivo e avaliou:

- forma visual do trânsito;
- dispersão;
- disponibilidade de `flux_err`;
- largura da janela;
- janelas alternativas para modelagem.

Portanto, na metodologia, a Gold pode ser apresentada como preparação e a EDA
como diagnóstico antes da inferência.

## 9. Frase-Síntese

Uma frase-síntese possível:

```text
A camada Gold consolidou um dataset analítico inicial para HAT-P-7 b a partir
da Silver, selecionando a missão Kepler, o fluxo PDCSAP, pontos com qualidade
instrumental igual a zero e uma janela inicial faseada em torno do trânsito,
mantendo proveniência e checksums para todos os artefatos derivados.
```
