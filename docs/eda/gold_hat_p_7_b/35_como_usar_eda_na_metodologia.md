# 35 - Como Usar a EDA na Metodologia

## 1. Função Metodológica da EDA

Na metodologia, a EDA pode ser apresentada como uma etapa de diagnóstico antes
da modelagem bayesiana.

Ela verifica se o dataset Gold:

- tem trânsito visualmente identificável;
- tem incerteza observacional utilizável;
- tem janela de trânsito adequada;
- tem quantidade suficiente de pontos;
- exige ajustes adicionais antes da inferência.

## 2. Como Descrever a EDA

Uma descrição possível:

```text
Após a construção da camada Gold, foi realizada uma análise exploratória da
curva de luz de HAT-P-7 b com o objetivo de verificar a adequação do dataset
para modelagem bayesiana preliminar. A análise considerou a curva primária, a
curva filtrada por qualidade, a curva faseada e a janela de trânsito definida
na Gold.
```

## 3. Como Descrever as Métricas

Uma descrição possível:

```text
Foram calculadas métricas descritivas, incluindo contagem de linhas, intervalo
temporal, intervalo de fase, valores ausentes em fluxo e erro de fluxo,
estatísticas de fluxo, distribuição das flags de qualidade e comparação de
janelas em torno da fase zero.
```

## 4. Como Descrever a Profundidade Visual

Use uma formulação cuidadosa:

```text
Como diagnóstico visual, foi calculada uma aproximação exploratória da
profundidade por contraste entre a mediana do fluxo fora do núcleo do trânsito
e a mediana do fluxo dentro do núcleo. Essa medida não foi tratada como
estimativa física final nem como resultado inferencial.
```

Evite:

```text
A profundidade foi estimada pelo modelo.
```

Porque isso não aconteceu nesta etapa.

## 5. Como Descrever as Figuras

Uma descrição possível:

```text
Foram geradas visualizações da curva primária, da curva filtrada por qualidade,
da curva faseada completa, da janela de trânsito, da janela com binning visual,
das distribuições de fluxo e erro de fluxo, além de uma comparação de janelas
com diferentes larguras em torno da fase zero.
```

## 6. Como Descrever a Recomendação de Janela

Uma descrição possível:

```text
A janela Gold inicial de aproximadamente ±0,48527 dias mostrou-se adequada
para inspeção ampla, mas relativamente larga para uma primeira modelagem. A
comparação exploratória de janelas indicou que ±0,15 dias preserva o evento de
trânsito e fornece baseline local suficiente, sendo recomendada como janela
preliminar para o primeiro modelo bayesiano.
```

## 7. Como Descrever `flux_err`

Uma descrição possível:

```text
A coluna de incerteza observacional `flux_err` estava disponível para todos os
pontos da janela de trânsito analisada, com mediana próxima de 25,89 unidades
de fluxo. Isso permite sua utilização em uma likelihood gaussiana preliminar,
embora a adequação dos resíduos ainda deva ser avaliada na etapa de modelagem.
```

## 8. O Que Enfatizar

Enfatize:

- a EDA é posterior à Gold;
- a EDA não altera as camadas de dados;
- a EDA é diagnóstica;
- a EDA não estima parâmetros físicos finais;
- a EDA orienta a janela inicial da modelagem;
- o resultado principal é uma recomendação operacional.

## 9. O Que Evitar

Evite afirmar que a EDA:

- ajustou um modelo de trânsito;
- produziu posterior;
- estimou parâmetros por inferência;
- validou um modelo bayesiano;
- comparou com literatura;
- decidiu a Gold definitiva do TCC.

## 10. Ponte Para a Modelagem

A próxima etapa poderá ser descrita como:

```text
A partir dos diagnósticos da EDA, a modelagem bayesiana preliminar deverá usar
a curva Gold de janela de trânsito, restringindo inicialmente os dados a
abs(phase) <= 0,15, com normalização local explícita e likelihood baseada em
flux_err.
```

## 11. Frase-Síntese

Uma frase-síntese possível:

```text
A EDA funcionou como uma etapa de controle de qualidade analítico da Gold,
confirmando a presença visual do trânsito, avaliando a largura da janela,
verificando a disponibilidade de incertezas observacionais e recomendando uma
janela preliminar de ±0,15 dias para a futura modelagem bayesiana.
```
