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
