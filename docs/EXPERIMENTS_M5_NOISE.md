# Contratos dos experimentos M5

Este documento descreve o que os experimentos implementam e, igualmente
importante, o que eles não demonstram.

## Sensibilidade de priors

`scripts/run_bayesian_sensitivity.py` executa o mesmo M5, no mesmo dataset, com
três perfis registrados em `src/bayesian_modeling/contracts.py`:

| perfil | sigma log de Rp/Rs | escala de jitter | finalidade |
|---|---:|---:|---|
| `catalog_tighter` | 0,25 | max(3 × erro mediano, 3e-4) | limite mais informativo |
| `baseline` | 0,50 | max(5 × erro mediano, 5e-4) | execução principal |
| `weak` | 0,90 | max(10 × erro mediano, 1e-3) | limite mais amplo |

Os três priors de raio são lognormais, positivos e centrados na escala
catalogada `sqrt(transit_depth_fraction)`. Antes do NUTS, cada run salva um
prior predictive check com curvas latentes e observações simuladas.

Só se comparam deslocamentos posteriores entre runs cujos gates de sampler,
PPC e validade científica passaram. Não convergência, dominância do prior ou
escala absurda é resultado negativo e impede a palavra “robusto”.

```bash
python scripts/run_bayesian_sensitivity.py \
  --target kepler_10_b --run-prefix sensitivity_001 \
  --draws 800 --tune 800 --chains 4 --cores 4
```

## Injeções de ruído e sistemática

`scripts/run_bayesian_noise_injection.py` gera datasets isolados e não altera a
Gold original. As classes são distintas:

- `white_gaussian`: ruído estocástico independente;
- `deterministic_sinusoid`: sinal sistemático determinístico, não “ruído
  vermelho” estocástico;
- `correlated_ar1`: ruído estocástico AR(1), reiniciado em cada segmento.

A implementação usa cópia profunda, gerador aleatório local e semente
registrada. O artefato mede a autocorrelação lag-1 da componente injetada e fica
com `inference_status=not_run` até que um modelo seja efetivamente ajustado.

```bash
python scripts/run_bayesian_noise_injection.py \
  --target kepler_10_b --kind correlated_ar1 \
  --amplitude 0.0002 --ar1-rho 0.8 --seed 42 \
  --experiment-id ar1_001
```

O M5 atual contém likelihood Normal condicionalmente independente e jitter
branco. Ele não contém GP nem likelihood AR(1). Portanto, uma injeção
correlacionada valida apenas a mecânica do experimento; não autoriza afirmar
recuperação ou modelagem de ruído correlacionado.

## Comparação

LOO/WAIC/ELPD só são calculados por `scripts/run_model_comparison.py` quando os
runs têm o mesmo `dataset_id`, checksum exato da entrada, definição de
likelihood, log-likelihood pontual e gate científico aprovado. Caso contrário,
o relatório registra a rejeição e não produz ranking formal. RMSE/MAE são
mantidos separados, e nenhum score estrutural heurístico é usado como evidência
Bayesiana.
