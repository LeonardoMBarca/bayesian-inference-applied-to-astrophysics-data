# 02 - Especificação do Modelo M3

## 1. Entrada e Dataset Efetivo

Entrada original:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Dataset salvo para modelagem:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/modeling_input_trapezoid.csv
```

O dataset efetivo contém `516` pontos após filtros e normalização.

## 2. Pré-processamento

Foram aplicadas as mesmas regras de M1 e M2 para manter comparabilidade:

1. Manter somente linhas com `abs(phase) <= 0.15`.
2. Manter somente `quality == 0`, quando a coluna existe.
3. Remover linhas sem `phase`.
4. Remover linhas sem `flux`.
5. Remover linhas sem `flux_err`.
6. Remover linhas com `flux_err <= 0`.
7. Normalizar por baseline local.

Resumo da entrada:

| Etapa | Linhas |
|---|---:|
| Janela Gold original | `1664` |
| Após filtro de fase | `516` |
| Após filtro de qualidade | `516` |
| Após filtro de ausentes | `516` |
| Após filtro de `flux_err > 0` | `516` |
| Linhas usadas | `516` |

## 3. Normalização Local

A região de baseline local foi definida como:

```text
0.08 <= abs(phase) <= 0.15
```

A mediana do fluxo nessa região foi:

```text
baseline_median = 1040715.45
```

As colunas normalizadas foram criadas como:

```text
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Essa normalização é a mesma usada em M1 e M2. Ela não altera a Gold; apenas
gera o dataset derivado de modelagem do M3.

## 4. Variáveis do Modelo

Variável de entrada:

```text
x_i = phase_i
```

Variável observada:

```text
y_i = normalized_flux_i
```

Incerteza observacional:

```text
sigma_obs_i = normalized_flux_err_i
```

## 5. Forma Trapezoidal

O modelo define a distância em fase ao centro do trânsito:

```text
d_i = abs(x_i - center)
```

A forma trapezoidal é:

```text
transit_shape_i = clip((half_duration - d_i) / ingress_duration, 0, 1)
```

Média esperada:

```text
mu_i = baseline - depth * transit_shape_i
```

Essa construção gera:

- fora do trânsito: `transit_shape = 0`, portanto `mu = baseline`;
- fundo do trânsito: `transit_shape = 1`, portanto `mu = baseline - depth`;
- ingresso/egresso: `0 < transit_shape < 1`, com transição linear.

## 6. Parametrização Estável do Ingresso

A restrição importante é:

```text
ingress_duration < half_duration
```

Em vez de amostrar `ingress_duration` diretamente com uma restrição dura, foi
usada uma fração:

```text
ingress_fraction ~ Beta(2, 5)
ingress_duration = ingress_fraction * half_duration
```

Essa parametrização é mais estável para NUTS, porque evita regiões inválidas
do espaço de parâmetros.

## 7. Priors

Priors usados:

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
center ~ Normal(0.0, 0.01)
half_duration ~ Uniform(0.03, 0.12)
ingress_fraction ~ Beta(2, 5)
extra_sigma ~ HalfNormal(0.005)
```

Leitura dos priors:

- `baseline` fica concentrado próximo de 1, porque o fluxo foi normalizado.
- `depth` é positivo por construção.
- `center` permite pequeno deslocamento em torno da fase zero.
- `half_duration` cobre durações totais aproximadas entre `0.06` e `0.24`
  dias.
- `ingress_fraction` favorece ingressos menores que a duração total, mas sem
  fixar um valor rígido.
- `extra_sigma` captura dispersão adicional não explicada por `flux_err`.

## 8. Likelihood

A incerteza efetiva combina erro observacional e ruído extra:

```text
sigma_eff_i = sqrt(sigma_obs_i^2 + extra_sigma^2)
```

Likelihood:

```text
y_i ~ Normal(mu_i, sigma_eff_i)
```

## 9. Parâmetros Derivados

O modelo calcula:

```text
rp_rs = sqrt(depth)
full_duration = 2 * half_duration
flat_duration = 2 * maximum(half_duration - ingress_duration, 0)
ingress_egress_total = 2 * ingress_duration
```

Esses parâmetros são salvos no trace e resumidos em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/derived_parameters_summary.csv
```

## 10. Amostragem

Configuração final:

```text
sampler = NUTS
draws = 2000
tune = 2000
chains = 4
cores = 4
target_accept = 0.90
random_seed = 42
```

O script possui política de retry:

1. tenta `target_accept = 0.90`;
2. se houver divergências, tenta `0.95`;
3. se ainda houver divergências, tenta `0.99`.

Nesta execução, não foi necessário retry.

## 11. Posterior Predictive

O posterior predictive foi calculado para os pontos observados e resumido em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/posterior_predictive_summary.csv
```

O resumo contém:

- `phase`;
- `observed_flux`;
- `predicted_mean`;
- `predicted_hdi_3`;
- `predicted_hdi_97`;
- `residual`.

## 12. Grade Trapezoidal

Foi criada uma grade:

```text
phase_grid = linspace(-0.15, 0.15, 300)
```

Para cada amostra posterior, a curva trapezoidal foi avaliada nessa grade. O
resumo foi salvo em:

```text
tables/bayesian_trapezoid_transit/hat_p_7_b/trapezoid_curve_summary.csv
```

Campos principais:

- `phase`;
- `model_mean`;
- `model_hdi_3`;
- `model_hdi_97`;
- `predictive_mean`;
- `predictive_hdi_3`;
- `predictive_hdi_97`.
