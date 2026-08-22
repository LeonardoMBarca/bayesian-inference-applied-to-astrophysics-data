# 04 - Limitações e Próximos Passos do M2

## 1. Limitações Científicas

M2 é um modelo bayesiano preditivo flexível, mas não é modelo físico final.

Ele não incorpora:

- geometria orbital;
- limb darkening;
- ingresso e egresso como parâmetros explícitos;
- duração física do trânsito;
- modelo Mandel & Agol;
- batman;
- exoplanet;
- Gaussian Process;
- ajuste multi-missão;
- dados TESS;
- dados ETD;
- estrutura hierárquica.

## 2. Limitação da Profundidade Derivada

O M2 não estima `depth` diretamente.

A profundidade exploratória:

```text
predicted_depth = baseline_level - min(f_grid)
```

é útil para comparar visualmente a depressão da curva com o M1, mas não deve
ser interpretada como equivalente físico exato ao `depth` paramétrico do M1.

Também não se deve derivar `Rp/Rs` a partir desse `predicted_depth` nesta etapa.

## 3. Limitação da Base Radial

As funções de base radial são fixas:

```text
n_basis = 12
basis_width = 0,035
```

Essa escolha controla a flexibilidade do modelo.

Consequências:

- bases muito largas podem suavizar demais a curva;
- bases muito estreitas podem aproximar ruído;
- o número de bases afeta a capacidade preditiva;
- a escolha ainda é metodológica, não física.

## 4. Limitação Preditiva

O intervalo preditivo cobre os dados observados, mas a cobertura de `1,0` para
um intervalo de 94% sugere que o termo `extra_sigma` deixa a predição
conservadora.

Isso não é necessariamente um erro, mas deve ser discutido como:

- possível ruído extra real;
- simplificação do modelo;
- consequência de não modelar efeitos instrumentais ou correlação temporal;
- argumento para comparar modelos no M4.

## 5. Interpretação Correta

M2 pode ser usado para dizer:

```text
O fluxo normalizado foi modelado como função suave da fase, permitindo estimar uma curva preditiva média e sua incerteza.
```

M2 não deve ser usado para dizer:

```text
O raio planetário foi estimado fisicamente pelo M2.
```

ou:

```text
M2 é o modelo final de trânsito.
```

## 6. Relação Com M1

M1:

- estima uma profundidade explícita;
- assume forma box;
- é simples e interpretável.

M2:

- não estima profundidade explícita;
- estima uma função suave;
- descreve melhor a forma visual da curva;
- produz incerteza preditiva.

Os dois modelos são complementares.

## 7. Próximo Modelo Recomendado

O próximo passo é M3:

```text
modelo trapezoidal ou físico aproximado
```

M3 deve buscar uma ponte entre:

- interpretabilidade física;
- flexibilidade de forma;
- estimação explícita de parâmetros relacionados ao trânsito.

Parâmetros candidatos para M3:

- profundidade;
- duração;
- meia largura;
- tempo de ingresso/egresso;
- baseline local;
- dispersão extra.

## 8. Comparação Formal Futuramente

M4 deve comparar M1, M2 e M3 usando:

- posterior predictive checks;
- erro preditivo;
- LOO;
- WAIC, se as hipóteses forem adequadas.

Essa comparação não foi feita no M2 porque o objetivo desta etapa era construir
e diagnosticar o modelo preditivo, não selecionar formalmente o melhor modelo.

## 9. Uso na Metodologia

Na metodologia do TCC, o M2 pode ser descrito como:

```text
um modelo bayesiano preditivo intermediário, baseado em funções de base radial gaussianas, usado para representar a curva de luz faseada como uma função suave com incerteza posterior.
```

Ele ajuda a demonstrar que a inferência bayesiana pode produzir não só
distribuições posteriores de parâmetros, mas também distribuições sobre funções
e predições futuras.
