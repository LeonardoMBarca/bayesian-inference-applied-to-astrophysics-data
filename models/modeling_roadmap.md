# Roadmap de Modelagem Bayesiana

## 1. Objetivo Geral

O objetivo da sequência de modelos é demonstrar como inferência bayesiana pode
representar incerteza observacional em curvas de luz de trânsito, passando de
um baseline simples para modelos com maior estrutura física e preditiva.

## 2. M1 - Baseline Box Transit

Objetivo:

- estimar uma profundidade média de trânsito como distribuição posterior;
- derivar `Rp/Rs = sqrt(depth)`;
- criar um baseline comparativo simples.

Status atual:

- execução operacional curta preservada como `001_operational_metropolis`;
- execução robusta recomendada criada como `002_nuts_robust`;
- amostrador robusto: NUTS;
- draws/tune/chains: `2000 / 2000 / 4`;
- diagnóstico robusto: `R-hat máximo = 1,00088086`, `ESS mínimo = 4553,60020940`, `divergências = 0`.

Parâmetros:

- `baseline`;
- `depth`;
- `extra_sigma`;
- `rp_rs`.

Limitações:

- forma box-shaped fixa;
- meia largura de trânsito fixa;
- sem limb darkening;
- sem geometria orbital;
- sem ingresso/egresso;
- assume independência condicional dos erros.

## 3. M2 - Modelo Bayesiano Preditivo

Objetivo:

- prever fluxo em função da fase;
- avaliar distribuição preditiva;
- permitir forma mais flexível do trânsito.

Status atual:

- implementado como `bayesian_predictive_phase_regression`;
- planeta: `HAT-P-7 b`;
- missão: `Kepler`;
- entrada: `data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv`;
- pontos usados: `516`;
- funções de base radial gaussianas fixas;
- `n_basis = 12`;
- `basis_width = 0,035`;
- amostrador: NUTS;
- draws/tune/chains: `2000 / 2000 / 4`;
- `target_accept` final: `0,99`;
- diagnóstico: `R-hat máximo = 1,00292448`, `ESS mínimo = 2269,80467052`, `divergências = 0`;
- `predicted_depth` exploratório médio: `0,00721029`.

Possibilidades:

- spline bayesiana;
- base radial;
- regressão local em fase;
- GP simples, se o custo computacional e a interpretação forem adequados.

Observação:

O M2 atual usa base radial, não GP. Ele melhora a descrição visual da curva em
relação ao box model do M1, mas não é modelo físico final.

## 4. M3 - Modelo Bayesiano Trapezoidal

Objetivo:

- estimar profundidade do trânsito;
- estimar centro posterior do trânsito;
- estimar duração total aproximada;
- estimar duração de ingresso/egresso;
- derivar `Rp/Rs = sqrt(depth)`;
- criar uma ponte entre o box model do M1 e modelos físicos futuros.

Status atual:

- implementado como `bayesian_trapezoid_transit`;
- planeta: `HAT-P-7 b`;
- missão: `Kepler`;
- entrada: `data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv`;
- pontos usados: `516`;
- amostrador: NUTS;
- draws/tune/chains: `2000 / 2000 / 4`;
- `target_accept` final: `0,90`;
- diagnóstico: `R-hat máximo = 1,00107423`, `ESS mínimo = 4212,34208408`, `divergências = 0`;
- profundidade posterior média: `0,00656620`;
- `Rp/Rs` posterior médio: `0,08100761`;
- duração total posterior média: `0,17664741` dias, ou `4,23954` horas.

Parâmetros:

- `baseline`;
- `depth`;
- `center`;
- `half_duration`;
- `ingress_fraction`;
- `ingress_duration`;
- `extra_sigma`;
- `rp_rs`;
- `full_duration`;
- `flat_duration`;
- `ingress_egress_total`.

Observação:

O M3 aproxima melhor o formato do trânsito que M1 por incluir ingresso e
egresso. Também é mais interpretável que M2 por estimar parâmetros explícitos.
Ainda assim, M3 não é modelo físico final: ele não inclui limb darkening, não
usa Mandel & Agol e não incorpora geometria orbital completa.

## 5. M4 - Comparação de Modelos

Objetivo:

- comparar M1, M2 e M3;
- usar posterior predictive checks;
- avaliar erro preditivo;
- considerar LOO ou WAIC, se os traces tiverem log likelihood compatível;
- selecionar o resultado principal preliminar.

Status atual:

- implementado como `model_comparison`;
- planeta: `HAT-P-7 b`;
- modelos comparados: M1, M2 e M3;
- M1 RMSE: `0,00358754`;
- M2 RMSE: `0,00317888`;
- M3 RMSE: `0,00317499`;
- todos os modelos: `divergências = 0`;
- LOO/WAIC: indisponíveis porque os `trace.nc` atuais não contêm grupo `log_likelihood`;
- recomendação: M3 como `primary_preliminary_result`.

Papel dos modelos após M4:

- M1: baseline de referência;
- M2: descrição preditiva suave;
- M3: principal resultado preliminar;
- próximo passo: modelo físico ou semi-físico com log likelihood para comparação formal.

## 6. Observação Metodológica

M1 não é a conclusão final do TCC.

M1 serve como baseline transparente para mostrar a ideia central:

```text
um parâmetro astrofísico de interesse pode ser descrito por uma distribuição
posterior, não apenas por um ponto estimado.
```
