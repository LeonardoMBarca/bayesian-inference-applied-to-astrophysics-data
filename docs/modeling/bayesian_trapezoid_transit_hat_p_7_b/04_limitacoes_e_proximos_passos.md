# 04 - Limitações e Próximos Passos do M3

## 1. Limitações Científicas

O M3 é mais estruturado que M1 e mais interpretável que M2, mas ainda é um
modelo aproximado.

Ele não incorpora:

- limb darkening;
- geometria orbital completa;
- inclinação orbital;
- razão semi-eixo maior/raio estelar;
- excentricidade;
- argumento do periastro;
- integração por tempo de exposição;
- modelo Mandel & Agol;
- `batman`;
- `exoplanet`;
- Gaussian Process;
- ajuste multi-missão;
- TESS;
- ETD;
- comparação formal LOO/WAIC.

Portanto, os parâmetros estimados devem ser lidos como aproximações sob uma
hipótese trapezoidal, não como caracterização física final de HAT-P-7 b.

## 2. Limitações Estatísticas

O modelo assume:

- independência condicional dos erros;
- likelihood Gaussiana;
- erro efetivo `sqrt(flux_err^2 + extra_sigma^2)`;
- janela fixa `abs(phase) <= 0.15`;
- normalização local por mediana;
- forma simétrica em torno do centro posterior;
- ingresso e egresso com mesma duração;
- profundidade constante no fundo do trânsito.

Essas hipóteses são úteis para um modelo intermediário, mas podem ser relaxadas
em etapas futuras.

## 3. Limitações de Interpretação

O parâmetro:

```text
rp_rs = sqrt(depth)
```

é uma razão aproximada. Em um modelo físico completo, a profundidade observada
depende de outros elementos, como limb darkening, geometria e integração da
exposição.

A duração total estimada:

```text
full_duration = 2 * half_duration
```

também deve ser interpretada como duração trapezoidal aproximada, não como uma
medida física final de contato primeiro-quarto.

## 4. Relação com M1 e M2

M1:

- fornece um baseline transparente;
- estima profundidade diretamente;
- ignora ingresso e egresso.

M2:

- descreve uma curva suave;
- é mais flexível;
- não possui profundidade física direta.

M3:

- estima profundidade e durações;
- introduz ingresso/egresso;
- permanece simples o bastante para documentação metodológica;
- serve como melhor ponte para modelos físicos futuros.

## 5. Próximo Passo: M4

O próximo passo recomendado é:

```text
M4 - Comparação de Modelos
```

O M4 deve comparar M1, M2 e M3 usando:

- posterior predictive checks;
- métricas de erro preditivo;
- análise comparativa de resíduos;
- consistência entre profundidades;
- possivelmente LOO ou WAIC, se as hipóteses forem adequadas.

O M4 não deve apagar as diferenças conceituais entre os modelos. A comparação
deve deixar claro que:

- M1 estima uma profundidade sob hipótese box;
- M2 estima uma curva preditiva suave;
- M3 estima uma forma trapezoidal paramétrica aproximada.

## 6. Como Usar na Metodologia

Na metodologia do TCC, o M3 pode ser descrito como:

```text
um modelo bayesiano paramétrico aproximado, usado para representar o trânsito
por uma forma trapezoidal e estimar distribuições posteriores de profundidade,
centro e durações, preservando a incerteza observacional.
```

Pontos úteis para o texto metodológico:

- os dados vêm da Gold de HAT-P-7 b;
- a janela de fase foi definida pela EDA;
- a normalização local foi mantida igual à de M1 e M2;
- a forma trapezoidal foi escolhida como compromisso entre simplicidade e
  interpretabilidade;
- os diagnósticos de NUTS indicaram convergência adequada;
- o resultado não é caracterização física final.

## 7. Arquivos para Consulta

Relatório técnico:

```text
reports/bayesian_trapezoid_transit_hat_p_7_b_report.md
```

Resumo posterior:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_summary.csv
```

Resumo de parâmetros derivados:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
```

Curva trapezoidal:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
```

Posterior predictive:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
```

Resíduos:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/residual_summary.csv
```
