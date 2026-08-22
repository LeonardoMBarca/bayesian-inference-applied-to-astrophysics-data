# 25 - Curvas Gold e Preparação Para Modelagem

## 1. Objetivo

Este documento descreve como a Gold preparou as curvas de luz de HAT-P-7 b
para uma futura modelagem bayesiana.

A preparação é mínima e explícita. Ela não executa ajuste físico, inferência,
normalização final ou remoção estatística de outliers.

## 2. Entrada Silver

A curva principal veio de:

```text
data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv
```

Essa tabela Silver foi construída a partir de FITS Kepler baixados na RAW e
tabularizados na Silver.

## 3. Curva Primária Gold

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
```

Linhas:

```text
6.163
```

Colunas principais:

```text
planet_name
host_star
planet_slug
mission
time
flux
flux_err
flux_source
quality
quality_is_zero
cadence_number
source_silver_path
source_raw_path
source_fits_file
gold_created_at_utc
```

## 4. Seleção do Fluxo

A coluna preferida foi:

```text
pdcsap_flux
```

A coluna de erro preferida foi:

```text
pdcsap_flux_err
```

Na Gold, elas foram renomeadas para:

```text
flux
flux_err
```

O campo:

```text
flux_source
```

registra a origem do fluxo selecionado. Para esta execução:

```text
pdcsap_flux
```

## 5. Remoção de Linhas Sem Tempo ou Fluxo

A Gold removeu linhas sem `time` ou sem fluxo utilizável.

Resumo registrado no manifesto:

```text
Selected pdcsap_flux; removed 306 rows with missing time or flux.
```

Essa remoção é técnica. Ela evita linhas impossíveis de usar em qualquer modelo
temporal, mas não remove outliers e não altera valores de fluxo.

## 6. Curva Filtrada Por Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
```

Linhas:

```text
3.909
```

Critério:

```python
quality == 0
```

Resumo registrado no manifesto:

```text
Kept rows with quality == 0. rows_before=6163; rows_after=3909; removed=2254.
```

Esse filtro usa a flag técnica da missão. Ele não é uma detecção estatística de
outliers feita pelo projeto.

## 7. Curva Faseada

Arquivo:

```text
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
```

Linhas:

```text
3.909
```

Fórmula:

```python
phase = ((time - transit_midpoint_used + 0.5 * period) % period) - 0.5 * period
```

Parâmetros usados:

```text
period = 2.20474 dias
transit_midpoint_used = 121.35857200017199
```

Interpretação:

- `phase = 0` representa o centro esperado do trânsito;
- valores negativos ocorrem antes do centro do trânsito;
- valores positivos ocorrem depois do centro do trânsito;
- a unidade da fase neste arquivo é dias, não fração adimensional de ciclo.

## 8. Janela de Trânsito Gold Inicial

Arquivo:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Linhas:

```text
1.664
```

Critério registrado:

```text
abs(phase) <= 0.48527000000000003
```

A largura veio da regra Gold:

```text
janela = max(3 * duração_em_dias, 0,2 dias)
```

Como a duração catalográfica foi:

```text
3,88216 horas = 0,1617566667 dias
```

Então:

```text
3 * 0,1617566667 = 0,48527 dias
```

## 9. Colunas da Janela de Trânsito

Campos principais:

```text
planet_name
host_star
planet_slug
mission
time
phase
flux
flux_err
quality
flux_source
orbital_period_days
transit_midpoint_used
phase_formula
source_gold_lightcurve
gold_created_at_utc
in_transit_window
transit_window_half_width_days
transit_duration_hours_used
```

## 10. O Que Ainda Precisa Ser Decidido

A Gold inicial ainda não decide:

- normalização final do fluxo;
- janela ótima para modelagem;
- modelo físico;
- priors;
- likelihood definitiva;
- tratamento de ruído correlacionado;
- estratégia de amostragem posterior.

A EDA posterior recomendou iniciar a modelagem com uma janela mais estreita:

```python
abs(phase) <= 0.15
```

Essa recomendação está documentada em:

```text
docs/eda/gold_hat_p_7_b/
```

## 11. Interpretação Correta

O arquivo `transit_window_lightcurve.csv` é uma base de trabalho.

Ele não é ainda o dataset final de inferência.

Ele deve ser usado como entrada para:

- inspeção visual;
- normalização local futura;
- testes de modelo simples;
- definição de priors;
- validação de likelihood.
