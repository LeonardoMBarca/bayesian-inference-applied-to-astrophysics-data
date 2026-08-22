# 39 - Modelo Probabilístico, Priors e Likelihood do M1

## 1. Tipo de Modelo

M1 é um modelo bayesiano simples do tipo:

```text
box-shaped transit
```

Ele aproxima o trânsito como uma queda constante de fluxo dentro de uma janela
central fixa.

## 2. Dados

Para cada observação `i`:

```text
y_i = normalized_flux_i
sigma_obs_i = normalized_flux_err_i
phase_i = phase_i
```

## 3. Regra do Box Transit

Se:

```python
abs(phase_i) <= 0.05
```

então:

```text
mu_i = baseline - depth
```

Caso contrário:

```text
mu_i = baseline
```

## 4. Parâmetros

Parâmetros amostrados:

```text
baseline
depth
extra_sigma
```

Parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

## 5. Priors

Baseline:

```text
baseline ~ Normal(1.0, 0.01)
```

Profundidade:

```text
depth ~ HalfNormal(0.02)
```

Dispersão extra:

```text
extra_sigma ~ HalfNormal(0.005)
```

## 6. Likelihood

Incerteza efetiva:

```text
sigma_eff_i = sqrt(sigma_obs_i^2 + extra_sigma^2)
```

Likelihood:

```text
y_i ~ Normal(mu_i, sigma_eff_i)
```

## 7. Por Que Existe `extra_sigma`

A coluna `normalized_flux_err` representa a incerteza observacional tabular.

Porém, a dispersão real da curva pode ser maior por:

- ruído instrumental residual;
- estrutura de baseline;
- simplificação do modelo box;
- ausência de limb darkening;
- ausência de ingresso/egresso.

`extra_sigma` permite absorver parte dessa dispersão adicional.

## 8. Interpretação de `depth`

`depth` representa a queda média relativa do fluxo no núcleo definido pelo box.

Ela não deve ser interpretada como profundidade física final do trânsito.

## 9. Interpretação de `rp_rs`

O parâmetro:

```text
rp_rs = sqrt(depth)
```

é uma aproximação útil para demonstrar a relação entre profundidade e razão de
raios.

Como M1 ignora efeitos físicos importantes, `rp_rs` também é preliminar.
