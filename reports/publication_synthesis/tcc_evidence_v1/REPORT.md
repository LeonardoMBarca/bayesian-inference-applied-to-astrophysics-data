# Relatório consolidado de evidência para TCC e paper

Análise posterior às campanhas; números gerados a partir dos resultados selados. Integridade dos artefatos e conclusão computacional não equivalem a calibração ou validade física universal.

## Execução e denominadores

| Campanha | Jobs declarados | Tentativas preservadas | Gates aprovados | Rejeitados | Falhas técnicas finais |
|---|---:|---:|---:|---:|---:|
| tcc_campaign_v1 | 117 | 118 | 66 | 51 | 0 |
| tcc_calibration_confirmatory_v1 | 400 | 400 | 337 | 63 | 0 |

Total: 517 jobs e 518 tentativas. Tentativas canceladas anteriores permanecem em `attempt_inventory.csv`; não são novos replicates independentes. Os controles de identidade são rejeições deliberadas, não falhas de execução.

A extensão foi decidida após observar a campanha inicial, com protocolo prospectivo, novos seeds e N fixo. As coortes são apresentadas separadamente; não há pooling nem seleção dos melhores seeds.

## P2 — confirmação independente da precisão das estimativas de calibração

Cobertura de intervalos de caudas iguais em verdades fixas, com IC de Wilson de 95%. Não é SBC: os parâmetros verdadeiros não foram sorteados do prior. Intervalos Bayesianos não têm garantia de cobertura frequentista nominal em cada verdade fixa. Sub/sobrecobertura descreve o desempenho condicional deste workflow, sem demonstrar, isoladamente, erro do sampler. Os intervalos de Wilson são pontuais, não simultâneos; não se fazem descobertas por múltiplos testes sem ajuste.

A tabela inclui todos os posteriors numéricos, inclusive os rejeitados. As colunas condicionadas ao sampler/gate, seus denominadores, viés, RMSE, SD e larguras em todos os níveis estão em `calibration_metrics.csv`. A taxa coberto-e-aprovado sobre todos os declarados é operacional, não cobertura.

### Coorte tcc_campaign_v1

| Regime | N | Sampler aprovado | PPC aprovado | Gate final aprovado |
|---|---:|---:|---:|---:|
| deep_short | 20 | 15 | 19 | 14 |
| intermediate_long | 20 | 14 | 20 | 14 |
| shallow_short | 20 | 17 | 20 | 17 |
| near_limit_long | 20 | 20 | 20 | 20 |

| Regime | Parâmetro | Viés | Viés relativo | RMSE | Cobertura 50% | Cobertura 80% | Cobertura 94% | Largura média 94% |
|---|---|---:|---:|---:|---|---|---|---:|
| deep_short | r | -0.000199951 | -0.2% | 0.00109272 | 14/20 (70.0%; IC95 48.1%–85.5%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.00681655 |
| deep_short | depth | -3.53664e-05 | -0.4% | 0.00021677 | 14/20 (70.0%; IC95 48.1%–85.5%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.00136056 |
| deep_short | b | -0.0233465 | -7.8% | 0.0647621 | 17/20 (85.0%; IC95 64.0%–94.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.529609 |
| deep_short | a | -0.0498699 | -1.0% | 0.118176 | 17/20 (85.0%; IC95 64.0%–94.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.847724 |
| deep_short | t0 | 0.0250535 | 2505.3% | 0.0790178 | 12/20 (60.0%; IC95 38.7%–78.1%) | 17/20 (85.0%; IC95 64.0%–94.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.100796 |
| deep_short | full_duration | 0.000227245 | 0.3% | 0.00080368 | 13/20 (65.0%; IC95 43.3%–81.9%) | 18/20 (90.0%; IC95 69.9%–97.2%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.0038329 |
| deep_short | extra_sigma | 3.33929e-05 | 16.7% | 7.92955e-05 | 18/20 (90.0%; IC95 69.9%–97.2%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.000461132 |
| intermediate_long | r | 0.00184619 | 4.6% | 0.00425801 | 15/20 (75.0%; IC95 53.1%–88.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.0290759 |
| intermediate_long | depth | 0.000248151 | 15.5% | 0.000466269 | 15/20 (75.0%; IC95 53.1%–88.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.00290324 |
| intermediate_long | b | -0.320671 | -42.8% | 0.320821 | 0/20 (0.0%; IC95 0.0%–16.1%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.898797 |
| intermediate_long | a | 4.07765 | 58.3% | 5.09566 | 2/20 (10.0%; IC95 2.8%–30.1%) | 14/20 (70.0%; IC95 48.1%–85.5%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 19.3013 |
| intermediate_long | t0 | -8.70027e-05 | -8.7% | 0.00142191 | 12/20 (60.0%; IC95 38.7%–78.1%) | 15/20 (75.0%; IC95 53.1%–88.8%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.00571877 |
| intermediate_long | full_duration | -0.00275081 | -8.3% | 0.00620758 | 12/20 (60.0%; IC95 38.7%–78.1%) | 16/20 (80.0%; IC95 58.4%–91.9%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.0262388 |
| intermediate_long | extra_sigma | 1.70435e-06 | 0.6% | 3.47186e-05 | 12/20 (60.0%; IC95 38.7%–78.1%) | 16/20 (80.0%; IC95 58.4%–91.9%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.000154765 |
| shallow_short | r | -0.000149684 | -1.1% | 0.000887747 | 12/20 (60.0%; IC95 38.7%–78.1%) | 17/20 (85.0%; IC95 64.0%–94.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.00412752 |
| shallow_short | depth | -2.19037e-06 | -1.1% | 2.39205e-05 | 12/20 (60.0%; IC95 38.7%–78.1%) | 17/20 (85.0%; IC95 64.0%–94.8%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.000116201 |
| shallow_short | b | -0.0425891 | -9.5% | 0.043504 | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.810109 |
| shallow_short | a | -0.0880339 | -2.7% | 0.169756 | 18/20 (90.0%; IC95 69.9%–97.2%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 1.80214 |
| shallow_short | t0 | -0.000173372 | -17.3% | 0.00261119 | 10/20 (50.0%; IC95 29.9%–70.1%) | 15/20 (75.0%; IC95 53.1%–88.8%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.00939063 |
| shallow_short | full_duration | 0.00138116 | 1.5% | 0.00500516 | 11/20 (55.0%; IC95 34.2%–74.2%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.026255 |
| shallow_short | extra_sigma | -1.4006e-06 | -1.4% | 1.10415e-05 | 10/20 (50.0%; IC95 29.9%–70.1%) | 16/20 (80.0%; IC95 58.4%–91.9%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 4.15277e-05 |
| near_limit_long | r | 0.0142515 | 142.5% | 0.0151503 | 0/20 (0.0%; IC95 0.0%–16.1%) | 16/20 (80.0%; IC95 58.4%–91.9%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.0513603 |
| near_limit_long | depth | 0.000719167 | 719.2% | 0.00080512 | 0/20 (0.0%; IC95 0.0%–16.1%) | 16/20 (80.0%; IC95 58.4%–91.9%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.00332428 |
| near_limit_long | b | -0.340902 | -37.9% | 0.341475 | 0/20 (0.0%; IC95 0.0%–16.1%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 20/20 (100.0%; IC95 83.9%–100.0%) | 0.944958 |
| near_limit_long | a | 26.4147 | 800.4% | 26.4303 | 0/20 (0.0%; IC95 0.0%–16.1%) | 0/20 (0.0%; IC95 0.0%–16.1%) | 1/20 (5.0%; IC95 0.9%–23.6%) | 43.3379 |
| near_limit_long | t0 | 0.00163823 | 163.8% | 0.00687242 | 19/20 (95.0%; IC95 76.4%–99.1%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.0839217 |
| near_limit_long | full_duration | -0.0338778 | -73.5% | 0.0339205 | 0/20 (0.0%; IC95 0.0%–16.1%) | 0/20 (0.0%; IC95 0.0%–16.1%) | 5/20 (25.0%; IC95 11.2%–46.9%) | 0.0426185 |
| near_limit_long | extra_sigma | -3.47416e-05 | -11.6% | 0.000110175 | 9/20 (45.0%; IC95 25.8%–65.8%) | 12/20 (60.0%; IC95 38.7%–78.1%) | 19/20 (95.0%; IC95 76.4%–99.1%) | 0.000370891 |
### Coorte tcc_calibration_confirmatory_v1

| Regime | N | Sampler aprovado | PPC aprovado | Gate final aprovado |
|---|---:|---:|---:|---:|
| deep_short | 100 | 75 | 100 | 75 |
| intermediate_long | 100 | 85 | 99 | 84 |
| shallow_short | 100 | 93 | 100 | 93 |
| near_limit_long | 100 | 86 | 99 | 85 |

| Regime | Parâmetro | Viés | Viés relativo | RMSE | Cobertura 50% | Cobertura 80% | Cobertura 94% | Largura média 94% |
|---|---|---:|---:|---:|---|---|---|---:|
| deep_short | r | -0.000250703 | -0.3% | 0.00105578 | 71/100 (71.0%; IC95 61.5%–79.0%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.00692885 |
| deep_short | depth | -4.54309e-05 | -0.5% | 0.000209827 | 71/100 (71.0%; IC95 61.5%–79.0%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.00138294 |
| deep_short | b | -0.0294312 | -9.8% | 0.0821479 | 74/100 (74.0%; IC95 64.6%–81.6%) | 99/100 (99.0%; IC95 94.6%–99.8%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.515909 |
| deep_short | a | -0.0584627 | -1.2% | 0.162728 | 75/100 (75.0%; IC95 65.7%–82.5%) | 96/100 (96.0%; IC95 90.2%–98.4%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.814983 |
| deep_short | t0 | -0.00501597 | -501.6% | 0.0500124 | 49/100 (49.0%; IC95 39.4%–58.7%) | 86/100 (86.0%; IC95 77.9%–91.5%) | 96/100 (96.0%; IC95 90.2%–98.4%) | 0.0408188 |
| deep_short | full_duration | 0.000443431 | 0.7% | 0.000894607 | 61/100 (61.0%; IC95 51.2%–70.0%) | 91/100 (91.0%; IC95 83.8%–95.2%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 0.00386001 |
| deep_short | extra_sigma | 3.50542e-05 | 17.5% | 0.00010516 | 73/100 (73.0%; IC95 63.6%–80.7%) | 90/100 (90.0%; IC95 82.6%–94.5%) | 94/100 (94.0%; IC95 87.5%–97.2%) | 0.000443302 |
| intermediate_long | r | 0.00286056 | 7.2% | 0.00638198 | 70/100 (70.0%; IC95 60.4%–78.1%) | 94/100 (94.0%; IC95 87.5%–97.2%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 0.0312739 |
| intermediate_long | depth | 0.000368227 | 23.0% | 0.000738008 | 70/100 (70.0%; IC95 60.4%–78.1%) | 94/100 (94.0%; IC95 87.5%–97.2%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 0.00328194 |
| intermediate_long | b | -0.318292 | -42.4% | 0.318497 | 0/100 (0.0%; IC95 0.0%–3.7%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.898442 |
| intermediate_long | a | 4.83925 | 69.1% | 6.56551 | 22/100 (22.0%; IC95 15.0%–31.1%) | 69/100 (69.0%; IC95 59.4%–77.2%) | 97/100 (97.0%; IC95 91.5%–99.0%) | 20.3694 |
| intermediate_long | t0 | 0.0025246 | 252.5% | 0.0249356 | 52/100 (52.0%; IC95 42.3%–61.5%) | 82/100 (82.0%; IC95 73.3%–88.3%) | 93/100 (93.0%; IC95 86.3%–96.6%) | 0.0158261 |
| intermediate_long | full_duration | -0.00343573 | -10.4% | 0.00761324 | 47/100 (47.0%; IC95 37.5%–56.7%) | 80/100 (80.0%; IC95 71.1%–86.7%) | 94/100 (94.0%; IC95 87.5%–97.2%) | 0.0269538 |
| intermediate_long | extra_sigma | 7.77553e-06 | 2.6% | 4.45504e-05 | 51/100 (51.0%; IC95 41.3%–60.6%) | 77/100 (77.0%; IC95 67.8%–84.2%) | 91/100 (91.0%; IC95 83.8%–95.2%) | 0.000155225 |
| shallow_short | r | -9.46365e-05 | -0.7% | 0.000620796 | 67/100 (67.0%; IC95 57.3%–75.4%) | 96/100 (96.0%; IC95 90.2%–98.4%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.00394402 |
| shallow_short | depth | -1.17279e-06 | -0.6% | 1.70464e-05 | 67/100 (67.0%; IC95 57.3%–75.4%) | 96/100 (96.0%; IC95 90.2%–98.4%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.000111127 |
| shallow_short | b | -0.04306 | -9.6% | 0.0450327 | 100/100 (100.0%; IC95 96.3%–100.0%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.805818 |
| shallow_short | a | -0.123612 | -3.7% | 0.184141 | 95/100 (95.0%; IC95 88.8%–97.8%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 1.69526 |
| shallow_short | t0 | 0.000163901 | 16.4% | 0.00223619 | 56/100 (56.0%; IC95 46.2%–65.3%) | 79/100 (79.0%; IC95 70.0%–85.8%) | 95/100 (95.0%; IC95 88.8%–97.8%) | 0.0084781 |
| shallow_short | full_duration | 0.00235603 | 2.6% | 0.00531319 | 58/100 (58.0%; IC95 48.2%–67.2%) | 86/100 (86.0%; IC95 77.9%–91.5%) | 99/100 (99.0%; IC95 94.6%–99.8%) | 0.0232414 |
| shallow_short | extra_sigma | -1.77543e-06 | -1.8% | 1.13542e-05 | 47/100 (47.0%; IC95 37.5%–56.7%) | 85/100 (85.0%; IC95 76.7%–90.7%) | 94/100 (94.0%; IC95 87.5%–97.2%) | 4.20947e-05 |
| near_limit_long | r | 0.0139836 | 139.8% | 0.0144081 | 0/100 (0.0%; IC95 0.0%–3.7%) | 73/100 (73.0%; IC95 63.6%–80.7%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 0.0509208 |
| near_limit_long | depth | 0.000688767 | 688.8% | 0.000721445 | 0/100 (0.0%; IC95 0.0%–3.7%) | 73/100 (73.0%; IC95 63.6%–80.7%) | 98/100 (98.0%; IC95 93.0%–99.4%) | 0.00323653 |
| near_limit_long | b | -0.347696 | -38.6% | 0.348648 | 0/100 (0.0%; IC95 0.0%–3.7%) | 97/100 (97.0%; IC95 91.5%–99.0%) | 99/100 (99.0%; IC95 94.6%–99.8%) | 0.944312 |
| near_limit_long | a | 25.6766 | 778.1% | 25.8039 | 0/100 (0.0%; IC95 0.0%–3.7%) | 2/100 (2.0%; IC95 0.6%–7.0%) | 9/100 (9.0%; IC95 4.8%–16.2%) | 43.6827 |
| near_limit_long | t0 | -0.000152434 | -15.2% | 0.00699028 | 92/100 (92.0%; IC95 85.0%–95.9%) | 99/100 (99.0%; IC95 94.6%–99.8%) | 100/100 (100.0%; IC95 96.3%–100.0%) | 0.0862149 |
| near_limit_long | full_duration | -0.0325038 | -70.5% | 0.032944 | 2/100 (2.0%; IC95 0.6%–7.0%) | 7/100 (7.0%; IC95 3.4%–13.7%) | 48/100 (48.0%; IC95 38.5%–57.7%) | 0.0488874 |
| near_limit_long | extra_sigma | -3.70518e-05 | -12.4% | 9.91515e-05 | 49/100 (49.0%; IC95 39.4%–58.7%) | 77/100 (77.0%; IC95 67.8%–84.2%) | 93/100 (93.0%; IC95 86.3%–96.6%) | 0.000375494 |

### Interpretação e resultados negativos

No regime near_limit_long, o viés relativo médio de Rp/Rs é 139.8%; a cobertura 94% de a/Rs é 9/100 (9.0%; IC95 4.8%–16.2%), e a de duração é 48/100 (48.0%; IC95 38.5%–57.7%). Mesmo assim, 85/100 passam pelo gate final. A aprovação é insuficiente para garantir identificação/calibração dos parâmetros. A contribuição sustentada aqui inclui delimitar essa falha, não afirmar recuperação confiável nesse regime.

Nos regimes profundo e raso, a cobertura de Rp/Rs excede o nominal em vários níveis; boa inclusão da verdade pode coexistir com intervalos conservadores. Compare largura e viés. A geometria pouco identificada, os priors e a correlação entre parâmetros são explicações plausíveis, não causas isoladas demonstradas por esta grade, que varia diversos fatores simultaneamente.

As rejeições são detalhadas por execução em `diagnostics.csv` e por cenário em `gate_summary.csv`. Critérios de rejeição se sobrepõem; não some motivos como se fossem runs distintos. Modos periódicos presos em cadeias de t0 estão documentados na revisão dos traces. Esses runs permanecem rejeitados e nos agregados; não houve descarte de cadeias ou substituição de seeds.

## P3 — benchmark independente

Estado da comparação: `compared_descriptively`; ambas implementações interpretáveis: `False`. As duas implementações foram executadas sobre a mesma entrada sob o contrato publicado. A concordância marginal de alguns parâmetros é apenas descritiva: NUTS local falhou numericamente e o resultado externo falhou no PPC temporal. Não há validação externa positiva da inferência física.

| Parâmetro | Diferença de médias / SD combinada | Sobreposição ETI94 (Jaccard) | Largura externa/local ETI94 | Discrepância marcada |
|---|---:|---:|---:|---|
| a | 0.0524049 | 0.975622 | 0.983553 | False |
| b | 0.0236358 | 0.985272 | 1.00881 | False |
| depth | 0.069578 | 0.811297 | 1.15081 | False |
| extra_sigma | 0.0398738 | 0.990692 | 0.99885 | False |
| full_duration | 0.155309 | 0.795362 | 0.808972 | False |
| r | 0.0700562 | 0.825151 | 1.11772 | False |
| t0 | 0.577412 | 0.00790715 | 0.00840365 | True |

Um modo de t0 separado por aproximadamente um período reteve uma cadeia local. O prior de t0 e a inicialização devem ser investigados prospectivamente. Não se remove a cadeia para fabricar concordância. A revisão registra evidência e hipóteses causais separadas.

## P4 — ablations e falhas

30 controles/intervenções; 9 casos com sampler aprovado e PPC/ciência reprovados. Isso demonstra empiricamente que convergência não basta para promoção. Controles de hash/identidade rejeitados antes da inferência têm sampler/PPC indisponíveis, não medidos como falhos.

Os efeitos por replicate e parâmetro estão em `ablation_paired_effects.csv`. São diferenças descritivas entre saídas numéricas: os baselines longos falharam no sampler, o que limita sua interpretação como efeitos físicos precisos. Há somente três realizações por par. O controle senoidal é sistemática determinística e não valida ruído estocástico correlacionado.

## P5 — todos os alvos pré-selecionados

| Alvo | Estado | Proveniência | Sampler | PPC | Gate final |
|---|---|---|---|---|---|
| HAT-P-7 b | rejected | True | True | False | False |
| Kepler-10 b | rejected | True | True | False | False |
| TrES-2 b | rejected | True | True | False | False |
| HD 189733 b | rejected | True | True | False | False |
| Kepler-4 b | rejected | True | False | False | False |

Nenhum alvo foi trocado ou omitido. Estes fits de publicação não sustentam generalização positiva. O histórico scientific_003 é outro contrato experimental preservado; não foi sobrescrito ou reclassificado. Catálogo/PDCSAP e efemérides condicionam a análise, portanto comparação com catálogo não é validação independente. Correlações residuais motivam investigação de adequação; não provam sozinhas que um GP resolveria o problema.

## P6, novidade e limites

M6 e calibração sob ruído OU continuam não executados. M5 contém ruído branco adicional independente, não covariância temporal. A prioridade atual é resolver/entender identificação, inicialização e adequação sob os contratos já testados. Não há superioridade de GP demonstrada.

A contribuição defensável é a integração e avaliação empírica de proveniência, inferência e critérios de interpretação, incluindo seus limites e falhas. O estudo não reivindica prioridade, novo modelo de trânsito, novo sampler ou invenção de SBC/gates. Consulte NOVELTY_MATRIX e BIBLIOGRAPHY.

A física geradora e a inferência compartilham primitivas; esta calibração não é totalmente independente da implementação. A grade contém quatro verdades fixas, sem amostragem de população. Aprovação em gates é um diagnóstico sob um contrato, não certificado de exatidão física. O estudo de sensibilidade/prior do baseline não substitui sensibilidade nesses novos regimes.

## Reprodutibilidade e reprodução

`artifact_manifest.json` vincula fontes, gerador, ambiente, tabelas e figuras; `SOURCE_INVENTORY.json` lista os arquivos exatos para a próxima reconstrução do TCC/paper. Os manifests das campanhas verificam recursivamente os resultados originais e seus traces. O código de síntese recalcula as métricas P2 e exige igualdade com os agregados selados.

```sh
python scripts/build_publication_synthesis.py
python scripts/build_publication_synthesis.py --check
python scripts/run_ci_tests.py
python scripts/validate_publication_release.py
```

O último comando é um gate de release distinto e ainda pode falhar: a síntese não concede aprovação para publicação/tag/DOI. Clean-room completo da nova release, arquivo externo dos traces, revisão de distribuição/privacidade e integração do validador de release com o registry de campanhas permanecem pendentes. Não há afirmação de reprodução integral em máquina limpa nesta revisão.

Os originais foram preservados. Para refazer agregações históricas use o checkout/ambiente identificado no manifest da campanha; o comando acima refaz esta síntese no checkout atual.

## Fontes de interpretação

[Talts et al., SBC](https://arxiv.org/abs/1804.06788), [Vehtari et al., diagnósticos MCMC](https://arxiv.org/abs/1903.08008), [Gelman et al., Bayesian Workflow](https://arxiv.org/abs/2011.01808). Fontes primárias reconferidas em 2026-09-30 e registradas na bibliografia do repositório.
