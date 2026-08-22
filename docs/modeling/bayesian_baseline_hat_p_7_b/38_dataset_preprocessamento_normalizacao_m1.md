# 38 - Dataset, Pré-processamento e Normalização do M1

## 1. Entrada

Arquivo Gold lido:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas na janela Gold original:

```text
1.664
```

## 2. Filtro de Fase

Critério:

```python
abs(phase) <= 0.15
```

Linhas após filtro:

```text
516
```

## 3. Filtro de Qualidade

Critério:

```python
quality == 0
```

Linhas após filtro:

```text
516
```

Como a janela Gold já vinha da curva filtrada por qualidade, esse filtro não
removeu linhas adicionais.

## 4. Ausências e Erros Inválidos

Foram removidas linhas:

- sem `flux`;
- sem `flux_err`;
- com `flux_err <= 0`.

Resultado:

```text
516 pontos usados no modelo
```

## 5. Região de Baseline Local

Critério:

```python
0.08 <= abs(phase) <= 0.15
```

Pontos nessa região:

```text
232
```

Mediana do baseline:

```text
1040715,45
```

## 6. Normalização

Foram criadas:

```python
normalized_flux = flux / baseline_median
normalized_flux_err = flux_err / baseline_median
```

Mediana de `normalized_flux`:

```text
0,993836144164094
```

Mediana de `normalized_flux_err`:

```text
2,487015879316484e-05
```

## 7. Núcleo Inicial de Trânsito

Critério:

```python
abs(phase) <= 0.05
```

Pontos no núcleo:

```text
179
```

Essa região define onde o modelo box aplica:

```text
mu = baseline - depth
```

## 8. Dataset Salvo

Arquivo:

```text
tables/bayesian_baseline/hat_p_7_b/modeling_input_baseline.csv
```

Colunas:

```text
planet_name
host_star
mission
time
phase
flux
flux_err
normalized_flux
normalized_flux_err
quality
is_core_transit_initial
is_baseline_region
source_gold_path
```

## 9. Interpretação

A normalização local é simples e explícita. Ela não é uma normalização final
para todo o TCC.

Ela serve apenas para colocar o fluxo em escala próxima de `1` e permitir a
interpretação direta de `depth` como queda relativa média.
