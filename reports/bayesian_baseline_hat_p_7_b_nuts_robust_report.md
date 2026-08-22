# M1 - Robust Bayesian Baseline Run - HAT-P-7 b

## 1. Objetivo da Reexecução Robusta

Esta execução reprocessa o mesmo Modelo 1, `M1 - box transit baseline`, usando
NUTS em vez da execução curta operacional com Metropolis.

O objetivo não é criar um novo modelo. O objetivo é obter uma execução
inferencial mais confiável para o baseline bayesiano, mantendo a mesma entrada,
o mesmo pré-processamento e a mesma especificação probabilística.

## 2. Problema da Execução Anterior

A execução anterior validou a cadeia completa de artefatos, mas foi limitada
operacionalmente pelo ambiente Python usado naquele momento.

- Amostrador anterior: `Metropolis`
- Uso científico recomendado: `False`
- Maior R-hat anterior: `2.33522345`
- Menor ESS anterior: `4.25512801`

Essa execução anterior permanece preservada em:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
```

## 3. Ambiente Usado

- Python: `3.13.13`
- Executável: `/home/leonardo_barca/workspace/personal/bayesian-inference-applied-to-astrophysics-data/.venv-nuts/bin/python`
- `Python.h` disponível: `True`
- Diretório de include: `/home/leonardo_barca/miniconda3/include/python3.13`
- GCC: `/usr/bin/gcc`
- G++: `/usr/bin/g++`
- PyMC: `6.0.1`
- ArviZ: `1.2.0`
- PyTensor: `3.0.7`
- Flags PyTensor: `base_compiledir=/tmp/pytensor-cache-nuts-robust`

O ambiente usado nesta reexecução foi um virtualenv local baseado no Python do
Conda:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

## 4. Configuração NUTS

- Sampler: `NUTS`
- Draws: `2000`
- Tune: `2000`
- Chains: `4`
- Cores: `4`
- Target accept: `0.9`
- Random seed: `42`
- Retry executado: `False`
- Motivo do retry: ``

## 5. Dataset e Pré-processamento

Entrada principal:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Regras mantidas:

- `abs(phase) <= 0.15`
- `quality == 0`
- remoção de `flux` ausente
- remoção de `flux_err` ausente
- remoção de `flux_err <= 0`
- região de baseline local: `0.08 <= abs(phase) <= 0.15`
- núcleo fixo do trânsito: `abs(phase) <= 0.05`

Resumo:

- Linhas iniciais na janela Gold: `1664`
- Linhas após janela de fase: `516`
- Linhas após filtro de qualidade: `516`
- Pontos usados no modelo: `516`
- Baseline mediano usado na normalização: `1040715.45`

## 6. Especificação Probabilística

O M1 usa um trânsito em forma de caixa:

```text
mu_i = baseline - depth, se abs(phase_i) <= transit_half_width
mu_i = baseline, fora do núcleo do trânsito
```

Priors:

```text
baseline ~ Normal(1.0, 0.01)
depth ~ HalfNormal(0.02)
extra_sigma ~ HalfNormal(0.005)
```

Likelihood:

```text
sigma_eff_i = sqrt(normalized_flux_err_i^2 + extra_sigma^2)
normalized_flux_i ~ Normal(mu_i, sigma_eff_i)
```

Parâmetro derivado:

```text
rp_rs = sqrt(depth)
```

## 7. Resultados Posteriores

- Profundidade média posterior: `0.00525258`
- HDI 94% da profundidade: `[0.00464576, 0.00587726]`
- `Rp/Rs` médio posterior: `0.07243869`
- HDI 94% de `Rp/Rs`: `[0.06815983, 0.07666328]`

Tabela completa:

```text
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/posterior_summary.csv
```

## 8. Diagnósticos MCMC

- NUTS rodou corretamente: `True`
- Divergências: `0`
- Maior R-hat: `1.00088086`
- Menor ESS: `4553.60020940`
- Aceitação média: `0.90407575`
- BFMI mínimo: `1.10526248`
- Recomendado para interpretação científica do M1: `True`

Nota:

```text
NUTS diagnostics satisfy the project criteria for M1 baseline interpretation.
```

Observação de runtime:

```text
Durante a adaptação, PyMC/PyTensor registrou RuntimeWarning de overflow em
quadpotential.py. O aviso foi preservado no stdout da execução. A avaliação
final foi baseada nos diagnósticos salvos: zero divergências, R-hat adequado,
ESS adequado e BFMI adequado.
```

## 9. Comparação com Execução Metropolis Curta

Comparação tabular:

```text
tables/bayesian_baseline/hat_p_7_b/model_run_comparison.csv
```

Resumo:

| run_id | sampler | draws | tune | chains | points_used | depth_mean | depth_hdi_3 | depth_hdi_97 | rp_rs_mean | rp_rs_hdi_3 | rp_rs_hdi_97 | r_hat_max | ess_min | divergences | recommended_for_scientific_interpretation | notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 001_operational_metropolis | Metropolis | 300 | 300 | 4 | 516 | 0.00507495 | 0.00439089 | 0.0057799 | 0.07118168 | 0.06626377 | 0.07602563 | 2.33522345 | 4.25512801 |  | False | Short operational Metropolis run preserved for pipeline validation only. |
| 002_nuts_robust | NUTS | 2000 | 2000 | 4 | 516 | 0.00525258 | 0.00464576 | 0.00587726 | 0.07243869 | 0.06815983 | 0.07666328 | 1.00088086 | 4553.6002094 | 0.0 | True | NUTS diagnostics satisfy the project criteria for M1 baseline interpretation. |

## 10. Interpretação Astrofísica Preliminar

Esta execução robusta estima a profundidade média do trânsito dentro de um
modelo box-shaped simplificado. A razão `Rp/Rs` foi obtida pela transformação
`sqrt(depth)`.

O resultado é comparável à profundidade visual exploratória da EDA, mas ainda
não deve ser lido como caracterização física completa do sistema HAT-P-7 b.

## 11. Limitações do M1

O M1 ainda:

- ignora limb darkening;
- ignora geometria orbital completa;
- usa largura de trânsito fixa;
- assume erros gaussianos independentes condicionais;
- usa apenas Kepler PDCSAP na janela selecionada;
- estima uma profundidade média simplificada.

## 12. Próximo Modelo Recomendado

O próximo passo recomendado é o M2: um modelo bayesiano preditivo de fluxo em
função da fase, ainda simples, mas capaz de representar melhor a forma observada
da curva do que uma caixa fixa.

O M1 robusto deve ser usado como baseline comparativo para M2.
