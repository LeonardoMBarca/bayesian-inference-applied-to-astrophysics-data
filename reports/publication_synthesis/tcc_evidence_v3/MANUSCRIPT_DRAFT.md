# Manuscript draft — bounded existing-evidence version

## Contribution and positioning

An empirical evaluation of a validation-gated, content-addressed reproducible Bayesian transit workflow. The contribution is auditable integration and quantified scope/failure transparency, not a priority claim over exoplanet, juliet or allesfitter. See the primary-source novelty matrix and bibliography.

## Methods

Physical transit likelihood with measured heteroscedastic error plus independent white jitter; finite exposure integration; fixed period/circular assumptions and recorded limb-darkening priors. Ground truth stays separate from inference. Frozen fixed-N cohorts, preserved seeds and failures, and an independent published implementation contract protect against selection. See METHODOLOGY.md and priors_by_family.json for equations and family-specific priors. M5 is not a correlated-noise likelihood.

## Results, numerical evidence and discussion

## Campanhas e populações (não somar como replicações independentes)

### tcc_campaign_v1

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 117; preserved attempts: 118; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 117 | 117 | 111 | 6 | 0 | 0 |
| ALL | sampler | 117 | 111 | 81 | 30 | 6 | 0 |
| ALL | ppc | 117 | 111 | 88 | 23 | 6 | 0 |
| ALL | joint | 117 | 111 | 66 | 45 | 6 | 0 |
| PUB-02 | provenance | 80 | 80 | 80 | 0 | 0 | 0 |
| PUB-02 | sampler | 80 | 80 | 66 | 14 | 0 | 0 |
| PUB-02 | ppc | 80 | 80 | 79 | 1 | 0 | 0 |
| PUB-02 | joint | 80 | 80 | 65 | 15 | 0 | 0 |
| PUB-03 | provenance | 2 | 2 | 2 | 0 | 0 | 0 |
| PUB-03 | sampler | 2 | 2 | 1 | 1 | 0 | 0 |
| PUB-03 | ppc | 2 | 2 | 0 | 2 | 0 | 0 |
| PUB-03 | joint | 2 | 2 | 0 | 2 | 0 | 0 |
| PUB-04 | provenance | 30 | 30 | 24 | 6 | 0 | 0 |
| PUB-04 | sampler | 30 | 24 | 10 | 14 | 6 | 0 |
| PUB-04 | ppc | 30 | 24 | 9 | 15 | 6 | 0 |
| PUB-04 | joint | 30 | 24 | 1 | 23 | 6 | 0 |
| PUB-05 | provenance | 5 | 5 | 5 | 0 | 0 | 0 |
| PUB-05 | sampler | 5 | 5 | 4 | 1 | 0 | 0 |
| PUB-05 | ppc | 5 | 5 | 0 | 5 | 0 | 0 |
| PUB-05 | joint | 5 | 5 | 0 | 5 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.

### tcc_calibration_confirmatory_v1

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 400; preserved attempts: 400; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 400 | 400 | 400 | 0 | 0 | 0 |
| ALL | sampler | 400 | 400 | 339 | 61 | 0 | 0 |
| ALL | ppc | 400 | 400 | 398 | 2 | 0 | 0 |
| ALL | joint | 400 | 400 | 337 | 63 | 0 | 0 |
| PUB-02 | provenance | 400 | 400 | 400 | 0 | 0 | 0 |
| PUB-02 | sampler | 400 | 400 | 339 | 61 | 0 | 0 |
| PUB-02 | ppc | 400 | 400 | 398 | 2 | 0 | 0 |
| PUB-02 | joint | 400 | 400 | 337 | 63 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.

### tcc_numerical_complement_v4

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: COMPLETED.
Declared jobs: 24; preserved attempts: 24; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 24 | 24 | 24 | 0 | 0 | 0 |
| ALL | sampler | 24 | 24 | 13 | 11 | 0 | 0 |
| ALL | ppc | 24 | 24 | 21 | 3 | 0 | 0 |
| ALL | joint | 24 | 24 | 10 | 14 | 0 | 0 |
| PUB-02 | provenance | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | sampler | 12 | 12 | 7 | 5 | 0 | 0 |
| PUB-02 | ppc | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | joint | 12 | 12 | 7 | 5 | 0 | 0 |
| PUB-03 | provenance | 3 | 3 | 3 | 0 | 0 | 0 |
| PUB-03 | sampler | 3 | 3 | 3 | 0 | 0 | 0 |
| PUB-03 | ppc | 3 | 3 | 0 | 3 | 0 | 0 |
| PUB-03 | joint | 3 | 3 | 0 | 3 | 0 | 0 |
| PUB-04 | provenance | 9 | 9 | 9 | 0 | 0 | 0 |
| PUB-04 | sampler | 9 | 9 | 3 | 6 | 0 | 0 |
| PUB-04 | ppc | 9 | 9 | 9 | 0 | 0 | 0 |
| PUB-04 | joint | 9 | 9 | 3 | 6 | 0 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.

### tcc_numerical_complement_v3

Mode: final. Historical controller snapshot: AGGREGATING; current controller state: STOPPED.
Declared jobs: 24; preserved attempts: 13; technical failures: 0. Completion is not scientific acceptance.

| Population | Component | Declared | Evaluated | Passed | Rejected | Unassessed | Invalidated |
|---|---|---:|---:|---:|---:|---:|---:|
| ALL | provenance | 24 | 13 | 13 | 0 | 11 | 0 |
| ALL | sampler | 24 | 13 | 11 | 2 | 11 | 0 |
| ALL | ppc | 24 | 6 | 6 | 0 | 11 | 7 |
| ALL | joint | 24 | 6 | 5 | 1 | 11 | 7 |
| PUB-02 | provenance | 12 | 12 | 12 | 0 | 0 | 0 |
| PUB-02 | sampler | 12 | 12 | 10 | 2 | 0 | 0 |
| PUB-02 | ppc | 12 | 6 | 6 | 0 | 0 | 6 |
| PUB-02 | joint | 12 | 6 | 5 | 1 | 0 | 6 |
| PUB-03 | provenance | 3 | 1 | 1 | 0 | 2 | 0 |
| PUB-03 | sampler | 3 | 1 | 1 | 0 | 2 | 0 |
| PUB-03 | ppc | 3 | 0 | 0 | 0 | 2 | 1 |
| PUB-03 | joint | 3 | 0 | 0 | 0 | 2 | 1 |
| PUB-04 | provenance | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | sampler | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | ppc | 9 | 0 | 0 | 0 | 9 | 0 |
| PUB-04 | joint | 9 | 0 | 0 | 0 | 9 | 0 |

Each pass rate is provided with its evaluated and declared denominators in JSON. Invalidated diagnoses are not counted as currently assessed scientific evidence. Recorded flags remain preserved. Technical fallback flags are not observed diagnostic failures.
The deprecated computational_gates_passed_count keeps its sealed v1 meaning (joint pass), not a sampler count. Use gate_counts.sampler.passed. These corrected reports supersede presentation only, never the original posterior or gate decision.

## Resultados e interpretação

- Useful radius recovery in supported short-cadence regimes coexists with conservative coverage and weak-information geometric undercoverage; fixed truths, not SBC or universal calibration.
- Density-equivalent standardized t0 does not demonstrate general sampler superiority in this small paired cohort.
- All local refits pass the sampler; temporal PPC fails. Posterior proximity under the comparison contract is descriptive; the same historical external posterior is reused.
- High-accuracy integrated references pass; exposure-off variants fail sampling. No jointly sampler-supported physical exposure effect is established.
- Predeclared controls demonstrate sampler-pass but PPC-fail; identity controls fail before sampling, not observed sampler failure.
- All five systems remain reported with predictive limitations. Temporal structure does not uniquely identify stochastic GP noise.
- Direct-coordinate traces are outside this specific conditioning incident; standardized PPC and dependent joint evidence are invalidated, not reclassified as observed failures.

Nas comparações locais de Rp/Rs, diferença padronizada de médias varia entre 0.015301 e 0.04698; razão de larguras ETI94 externo/local entre 1.1452 e 1.1756. Valores descritivos sob contrato, sem teste de equivalência ou promoção astrofísica.
PUB-02, direct: sampler aprovado em 4/6 ajustes; mesmas realizações pareadas, não superioridade geral.
PUB-02, standardized: sampler aprovado em 3/6 ajustes; mesmas realizações pareadas, não superioridade geral.

Controles históricos com sampler aprovado e PPC reprovado: 9. O baseline scientific_003 tem identidade Gold e input preservados no publication/baseline/manifest.json; não é retroativamente aprovado/reprovado pelos protocolos novos.
v4: PUB-02 tem 12 ajustes em 6 datasets pareados; PUB-04 tem 9 ajustes em 3 datasets; PUB-03 tem 3 ajustes locais em 1 input, com uma posterior externa histórica, sem novo ajuste externo.

## Calibração e física

calibration_metrics.csv e coverage_trace_verified.png são reutilizados byte a byte da auditoria independente dos 80 e 400 traces. Mantêm bias, RMSE, SD, ETI50/80/94, Wilson95, larguras, populações all-numeric/sampler-pass/joint-pass e rendimento operacional. Sobre/subcobertura em verdades fixas não é SBC; populações selecionadas pelo gate não estimam cobertura incondicional. Rp/Rs e depth=r² não são validações independentes. Geometria e duração podem continuar pouco identificadas, inclusive com gate aprovado.

## Benchmark e ablações

benchmark_comparisons.csv contém todas as três comparações marginais com diferenças padronizadas, distância CDF, overlap e razões de largura ETI94 (não HDI). Proximidade computacional sob hipóteses comparáveis não resolve inadequação temporal da likelihood. Os contrastes completos, inclusive rejeitados, estão em complement/PUB-04.json; são descritivos, não estimativas físicas definitivas quando um sampler falha.

## Preservação e prontidão

A: fontes auditáveis para redigir/revisar o TCC, com escopo restrito. B: disponibilidade/restauração local requer o recibo versionado de archive; não equivale à reprodução independente de MCMC. C: arquivo público durável, direitos/privacidade e DOI continuam pendentes. D: este manuscript draft ainda exige revisão editorial e adequação ao periódico. M6 permanece fora deste fechamento e ruído correlacionado não foi resolvido. Não há garantia de nota ou aceitação.

## Reprodução e validação (sem inferência)

```sh
python scripts/close_tcc_evidence.py --build --output reports/publication_synthesis/<NEW_VERSION>
python scripts/close_tcc_evidence.py --check
python scripts/close_tcc_evidence.py --check-protected
python scripts/close_tcc_evidence.py --verify-original
```

O destino precisa ser novo; nunca sobrescrever versões seladas. SOURCE_INVENTORY.json lista exatamente fontes, tabelas, figuras, captions, claims e auditorias para a próxima reconstrução do Word. BIBLIOGRAPHY.md mantém as fontes primárias e limita as alegações de novidade.

## Threats to validity and future work

Fixed-truth coverage is conditional; successful sampler diagnostics are necessary but not sufficient. Prior-dominated geometry, multiple comparisons, small paired complement, repeated local MC streams on one input and dependent catalog information prevent universal or population-level conclusions. No favorable target/seed selection or rescue threshold change. Future prospective studies may address correlated noise and independent targets; they were not executed here.
