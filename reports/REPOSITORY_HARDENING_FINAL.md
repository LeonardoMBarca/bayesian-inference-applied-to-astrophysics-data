# Relatório final de hardening do repositório

Data da validação: 2026-08-24  
Branch auditada: `main`  
Commit de partida: `79cc1cc90d2693c686f8c5e7b139d4a0e70bddb2`

## Resultado

O programa de remediação definido em `AGENTS.md`, `.agents/CODEX_TASK.md` e
`.agents/REMEDIATION_PLAN.md` foi executado. Os produtos RAW→Silver→Gold foram
reconstruídos em isolamento, o M5 atual passou gates computacionais,
posterior-preditivos e científicos, os experimentos passaram a declarar somente
o que implementam e a suíte prática de regressão passou integralmente.

Este resultado não transforma snapshots históricos em evidência atual. Apenas
runs com gate explícito são classificados como cientificamente interpretáveis.

## Ambiente validado

- WSL/Linux, Python 3.14.6;
- NumPy 2.4.6, pandas 2.3.3, PyMC 6.3.1, ArviZ 1.3.0,
  exoplanet 0.6.0, Astropy 8.0.1 e Lightkurve 2.6.0;
- `requirements.txt` com versões exatas, SHA-256
  `19dcc3f4ffb974f3d6cb166749fad06dcf9e6fce99e0077c8b3075911a58ad80`;
- `environment.yml`, SHA-256
  `8f88a3da35212a4b44639af2f3ab86ee59548dbab32d60e5ba3c4e373f9e922e`;
- `pyproject.toml`, SHA-256
  `2e6de8653a72f0b601305727fc7d76310f4700251fd254370ab1da63398e91c0`.

O workflow `.github/workflows/ci.yml` instala esse ambiente, executa validação
estática, testes e validação de artefatos; o clean-room completo é acionável
manualmente. Nesta árvore de trabalho os comandos equivalentes passaram
localmente. Não se afirma que um job remoto hospedado tenha sido executado.

## Comandos de validação executados

```bash
python scripts/build_silver_data.py
python scripts/build_gold_data.py
python scripts/rebuild_m5_artifacts.py --target kepler_10_b --run-id scientific_002
python scripts/summarize_bayesian_sensitivity.py \
  --target kepler_10_b --experiment-id sensitivity_001 \
  --catalog-tighter-run sensitivity_001_catalog_tighter \
  --baseline-run scientific_002 --weak-run sensitivity_001_weak
python scripts/run_model_comparison.py \
  models/bayesian_physical_transit/kepler_10_b/runs/sensitivity_001_catalog_tighter/model_config.json \
  models/bayesian_physical_transit/kepler_10_b/runs/scientific_002/model_config.json \
  models/bayesian_physical_transit/kepler_10_b/runs/sensitivity_001_weak/model_config.json \
  --output-dir reports/model_comparison/prior_sensitivity_001
python scripts/validate_clean_rebuild.py
python scripts/build_model_run_inventory.py
python scripts/validate_hardened_artifacts.py
python -m unittest discover -s tests -v
python scripts/static_validate.py
git diff --check
```

As três execuções completas da sensibilidade usaram quatro chains, 800 passos
de tuning e 800 draws por chain, `target_accept=0.95` e semente 42.

## Proveniência e reconstrução de dados

- manifest de estado RAW: 445 caminhos únicos, 445 checksums SHA-256, zero
  arquivos ausentes e zero divergências de checksum;
- caminhos persistidos são relativos ao repositório e usam separadores POSIX;
- Silver registra percentuais e frações de profundidade, horas e dias com
  semântica explícita e conversões testadas;
- HAT-P-7 b Gold: dataset `hat_p_7_b-a40623cca1048e76`, 3 segmentos, 3.909
  pontos após qualidade, 1.027 pontos na janela M5 e cadência longa mediana de
  1.765,463 s;
- Kepler-10 b Gold: dataset `kepler_10_b-06a6ce6b0b39f5b4`, 3 segmentos,
  115.363 pontos após qualidade, 40.836 na janela e cadência curta mediana de
  58,849 s;
- os offsets brutos entre segmentos foram preservados nos diagnósticos e cada
  baseline fora de trânsito foi normalizado a 1,0 antes da concatenação;
- o clean-room, iniciado somente com código/config e RAW e com rede desativada,
  reproduziu os dois IDs e o hash de entrada M5 de cada alvo. O hash da árvore
  RAW usada foi
  `a3b30d6d01575806999d1a74feefb1ecc9ff9d78b2265601b26bc0adcb344376`.
- nenhum dos 445 caminhos do manifesto RAW atual é ocultado pelo `.gitignore`;
  o conjunto versionável contém zero arquivo com 100 MiB ou mais (o maior
  produto publicado atual tem 36,35 MiB).

Evidência: `reports/clean_rebuild_validation.json` e
`scripts/validate_hardened_artifacts.py`.

## M5 atual e diagnóstico

O M5 compartilhado usa órbita circular Kepleriana, limb darkening quadrático
`q1/q2`, período específico do alvo, integração por tempo de exposição,
likelihood Normal com erro medido e jitter branco, NUTS, log-likelihood pontual,
prior predictive e posterior predictive. Não contém GP nem likelihood de ruído
correlacionado.

Run principal `scientific_002`:

| Evidência | Valor |
|---|---:|
| alvo | Kepler-10 b |
| dataset | `kepler_10_b-06a6ce6b0b39f5b4` |
| hash da entrada M5 | `5bd20f7d94ca6f84fe47d4d504a6a817e28aa542065425fb5c01c13466df3845` |
| hash local do trace | `7ed982a0c4d802171f26b270eb76b2076ef49736059482e7375fdd810837df4c` |
| R-hat máximo | 1,00508421 |
| ESS mínimo | 582,0677 |
| divergências | 0 |
| BFMI mínimo | 0,7317310 |
| cobertura PPC 94% | 0,933667 |
| desvio dos resíduos padronizados | 1,003572 |
| jitter/erro medido | 1,017704 |
| `Rp/Rs`, média e HDI 94% | 0,01249085 [0,01092702; 0,01453419] |
| profundidade geométrica, média e HDI 94% | 0,00015692 [0,00011940; 0,00021124] |
| duração média | 1,90182 h |
| gate científico | aprovado |

O valor de catálogo usado como referência de escala cai no HDI, mas também
centraliza o prior de raio. Isso não é validação externa independente e o
posterior não foi ajustado para reproduzir o catálogo.

## Sensibilidade e comparação

Os três perfis `catalog_tighter`, `baseline` e `weak` passaram seus próprios
gates e compartilharam exatamente dataset, entrada e likelihood. O maior
deslocamento relativo em relação ao baseline foi 0,77% para `Rp/Rs`, 1,59% para
profundidade, 0,18% para jitter e 0,34% para duração; os HDIs de 94% contêm a
média baseline. A conclusão é descritiva e limitada a essa família de priors.

LOO e WAIC foram calculados, mas PSIS-LOO encontrou 15–25 pontos com Pareto-k
acima de 0,7, incluindo máximo 1,163. O artefato mantém os valores para auditoria
e marca `ranking_status=not_ranked_due_to_diagnostic_warning`. Nenhum score
estrutural heurístico é misturado às métricas formais ou preditivas.

## Ruído e controles negativos

- `white_001`: injeção Gaussiana independente, lag-1 mediano 0,00294;
- `sinusoid_001`: sistemática determinística, não chamada de ruído estocástico;
- `ar1_001`: injeção correlacionada AR(1), lag-1 mediano 0,79987;
- os três artefatos dizem `inference_status=not_run`: demonstram geração e
  recuperação exata da injeção nos testes, não recuperação Bayesiana de
  correlação pelo M5.

Runs falhos ou não interpretáveis foram preservados:

- `sensitivity_001_weak_interrupted`: processo interrompido, sem trace, marcado
  `failed` e inválido;
- `smoke_003` e `smoke_004`: falhas de compatibilidade preservadas;
- `smoke_005`: executou, mas foi rejeitado (R-hat 3,1043, ESS 3,64 e gates
  científicos falhos);
- `scientific_001`: numericamente convergido, mas rejeitado pelo gate registrado
  antes da correção de extração BFMI; não foi rebatizado retroativamente;
- a sensibilidade histórica de HAT-P-7 b tem R-hat 1,734, ESS 6,10 e 11
  divergências e permanece snapshot histórico não interpretável;
- demais M1–M5 históricos são classificados como não-gated, mesmo quando seus
  diagnósticos de sampler parecem bons.

O inventário completo está em `reports/model_run_inventory.json` e
`reports/model_run_inventory.md`.

## Testes e artefatos

- 45 testes executados, 45 aprovados;
- 83 arquivos Python parseados;
- 6 notebooks parseados;
- 18 dependências científicas críticas verificadas com versões exatas;
- validação integrada dos artefatos aprovada;
- clean-room RAW→Silver→Gold aprovado sem rede;
- M5 principal reconstruído do trace somente após confirmar dataset e hash.

## Limitações restantes

- período e excentricidade do M5 atual são fixos;
- parâmetros estelares não são inferidos conjuntamente;
- normalização por mediana fora de trânsito em cada segmento é uma hipótese
  metodológica explícita;
- o likelihood representa apenas ruído branco heteroscedástico mais jitter;
- `r²` é profundidade geométrica, não necessariamente profundidade aparente com
  limb darkening;
- o alerta Pareto-k impede ranking confiável pela comparação LOO atual;
- traces NetCDF e derivados volumosos não são versionados em Git; checksums,
  manifests, comandos e ambiente permitem regeneração e auditoria local;
- downloads RAW futuros dependem da disponibilidade dos serviços externos, mas
  a reconstrução validada a partir do RAW versionável não usa rede.

Essas limitações são mantidas como limites explícitos do resultado, não como
itens silenciosamente “resolvidos”.
