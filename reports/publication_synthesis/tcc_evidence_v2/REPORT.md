# Evidência científica auditada — TCC v2

Esta revisão é posterior aos resultados. Preserva `tcc_evidence_v1`, as campanhas e `scientific_003`; não reclassifica seus gates históricos. Integridade, computação, predição e recuperação física são perguntas diferentes.

## Inventário e integridade

| Coorte | Jobs | Tentativas | Gate histórico aprovado | Rejeitado |
|---|---:|---:|---:|---:|
| tcc_campaign_v1 | 117 | 118 | 66 | 51 |
| tcc_calibration_confirmatory_v1 | 400 | 400 | 337 | 63 |

Jobs e tentativas não são denominadores intercambiáveis. O cancelamento antes do posterior permanece no histórico. Controles de identidade têm sampler/PPC não avaliados, não zero observado.
A auditoria independente recalculou médias, SD amostral e quantis dos traces, sem importar o agregador original. Coortes de80 e400 permanecem separadas. Compare o inventário transitive e os recibos de restauração antes de afirmar disponibilidade independente.

## Recuperação: regime e parâmetro

Intervalos de caudas iguais (ETI), não HDI. Cobertura condicional em verdades fixas, não SBC. Wilson95 é pontual; não é controle simultâneo de múltiplas comparações. All-numeric inclui saídas numericamente rejeitadas e não presume posteriors exatos. CSV contém populações condicionadas e rendimento operacional, sem confundir os estimandos.

| Coorte | Regime | Parâmetro | Viés | RMSE | Cobertos94 / numéricos | Largura94 |
|---|---|---|---:|---:|---|---:|
| tcc_campaign_v1 | deep_short | r | -0.000199951 | 0.001092717 | 20/20 | 0.006816552 |
| tcc_campaign_v1 | deep_short | depth | -3.536638e-05 | 0.0002167697 | 20/20 | 0.001360563 |
| tcc_campaign_v1 | deep_short | b | -0.02334653 | 0.06476208 | 20/20 | 0.5296094 |
| tcc_campaign_v1 | deep_short | a | -0.0498699 | 0.118176 | 20/20 | 0.8477238 |
| tcc_campaign_v1 | deep_short | t0 | 0.0250535 | 0.07901779 | 20/20 | 0.1007963 |
| tcc_campaign_v1 | deep_short | full_duration | 0.0002272455 | 0.0008036796 | 19/20 | 0.003832899 |
| tcc_campaign_v1 | deep_short | extra_sigma | 3.33929e-05 | 7.929548e-05 | 20/20 | 0.0004611324 |
| tcc_campaign_v1 | intermediate_long | r | 0.001846193 | 0.004258007 | 20/20 | 0.02907593 |
| tcc_campaign_v1 | intermediate_long | depth | 0.0002481515 | 0.0004662687 | 20/20 | 0.002903236 |
| tcc_campaign_v1 | intermediate_long | b | -0.3206714 | 0.3208213 | 20/20 | 0.8987971 |
| tcc_campaign_v1 | intermediate_long | a | 4.07765 | 5.095664 | 20/20 | 19.30133 |
| tcc_campaign_v1 | intermediate_long | t0 | -8.700265e-05 | 0.001421912 | 19/20 | 0.00571877 |
| tcc_campaign_v1 | intermediate_long | full_duration | -0.002750808 | 0.006207583 | 20/20 | 0.02623875 |
| tcc_campaign_v1 | intermediate_long | extra_sigma | 1.704353e-06 | 3.471855e-05 | 19/20 | 0.0001547646 |
| tcc_campaign_v1 | shallow_short | r | -0.0001496837 | 0.000887747 | 20/20 | 0.004127524 |
| tcc_campaign_v1 | shallow_short | depth | -2.190365e-06 | 2.392053e-05 | 20/20 | 0.0001162009 |
| tcc_campaign_v1 | shallow_short | b | -0.04258906 | 0.04350398 | 20/20 | 0.8101093 |
| tcc_campaign_v1 | shallow_short | a | -0.08803392 | 0.1697564 | 20/20 | 1.802142 |
| tcc_campaign_v1 | shallow_short | t0 | -0.0001733721 | 0.002611194 | 19/20 | 0.009390628 |
| tcc_campaign_v1 | shallow_short | full_duration | 0.001381155 | 0.005005163 | 19/20 | 0.02625503 |
| tcc_campaign_v1 | shallow_short | extra_sigma | -1.400596e-06 | 1.104152e-05 | 20/20 | 4.152775e-05 |
| tcc_campaign_v1 | near_limit_long | r | 0.01425149 | 0.01515034 | 19/20 | 0.05136028 |
| tcc_campaign_v1 | near_limit_long | depth | 0.000719167 | 0.0008051196 | 19/20 | 0.003324277 |
| tcc_campaign_v1 | near_limit_long | b | -0.3409019 | 0.3414749 | 20/20 | 0.9449582 |
| tcc_campaign_v1 | near_limit_long | a | 26.41471 | 26.43033 | 1/20 | 43.33786 |
| tcc_campaign_v1 | near_limit_long | t0 | 0.001638231 | 0.006872424 | 19/20 | 0.0839217 |
| tcc_campaign_v1 | near_limit_long | full_duration | -0.03387777 | 0.03392046 | 5/20 | 0.04261854 |
| tcc_campaign_v1 | near_limit_long | extra_sigma | -3.474161e-05 | 0.0001101752 | 19/20 | 0.0003708915 |
| tcc_calibration_confirmatory_v1 | deep_short | r | -0.0002507034 | 0.001055776 | 100/100 | 0.00692885 |
| tcc_calibration_confirmatory_v1 | deep_short | depth | -4.543091e-05 | 0.0002098274 | 100/100 | 0.001382937 |
| tcc_calibration_confirmatory_v1 | deep_short | b | -0.02943118 | 0.08214791 | 100/100 | 0.515909 |
| tcc_calibration_confirmatory_v1 | deep_short | a | -0.05846268 | 0.1627281 | 100/100 | 0.8149834 |
| tcc_calibration_confirmatory_v1 | deep_short | t0 | -0.005015971 | 0.05001242 | 96/100 | 0.04081879 |
| tcc_calibration_confirmatory_v1 | deep_short | full_duration | 0.0004434308 | 0.0008946074 | 98/100 | 0.003860009 |
| tcc_calibration_confirmatory_v1 | deep_short | extra_sigma | 3.50542e-05 | 0.0001051601 | 94/100 | 0.0004433024 |
| tcc_calibration_confirmatory_v1 | intermediate_long | r | 0.002860556 | 0.006381984 | 98/100 | 0.03127392 |
| tcc_calibration_confirmatory_v1 | intermediate_long | depth | 0.0003682268 | 0.0007380076 | 98/100 | 0.003281943 |
| tcc_calibration_confirmatory_v1 | intermediate_long | b | -0.3182919 | 0.3184971 | 100/100 | 0.8984415 |
| tcc_calibration_confirmatory_v1 | intermediate_long | a | 4.839253 | 6.565506 | 97/100 | 20.36945 |
| tcc_calibration_confirmatory_v1 | intermediate_long | t0 | 0.002524597 | 0.02493558 | 93/100 | 0.01582613 |
| tcc_calibration_confirmatory_v1 | intermediate_long | full_duration | -0.003435728 | 0.007613235 | 94/100 | 0.02695381 |
| tcc_calibration_confirmatory_v1 | intermediate_long | extra_sigma | 7.775535e-06 | 4.455039e-05 | 91/100 | 0.0001552248 |
| tcc_calibration_confirmatory_v1 | shallow_short | r | -9.463652e-05 | 0.0006207961 | 100/100 | 0.003944016 |
| tcc_calibration_confirmatory_v1 | shallow_short | depth | -1.17279e-06 | 1.704642e-05 | 100/100 | 0.0001111272 |
| tcc_calibration_confirmatory_v1 | shallow_short | b | -0.04306005 | 0.04503267 | 100/100 | 0.8058178 |
| tcc_calibration_confirmatory_v1 | shallow_short | a | -0.1236117 | 0.1841414 | 100/100 | 1.695259 |
| tcc_calibration_confirmatory_v1 | shallow_short | t0 | 0.0001639013 | 0.002236195 | 95/100 | 0.008478098 |
| tcc_calibration_confirmatory_v1 | shallow_short | full_duration | 0.002356034 | 0.005313193 | 99/100 | 0.02324139 |
| tcc_calibration_confirmatory_v1 | shallow_short | extra_sigma | -1.775428e-06 | 1.135423e-05 | 94/100 | 4.209473e-05 |
| tcc_calibration_confirmatory_v1 | near_limit_long | r | 0.01398363 | 0.01440812 | 98/100 | 0.05092085 |
| tcc_calibration_confirmatory_v1 | near_limit_long | depth | 0.0006887668 | 0.0007214453 | 98/100 | 0.003236526 |
| tcc_calibration_confirmatory_v1 | near_limit_long | b | -0.347696 | 0.348648 | 99/100 | 0.9443119 |
| tcc_calibration_confirmatory_v1 | near_limit_long | a | 25.67661 | 25.80393 | 9/100 | 43.68266 |
| tcc_calibration_confirmatory_v1 | near_limit_long | t0 | -0.0001524341 | 0.006990279 | 100/100 | 0.08621493 |
| tcc_calibration_confirmatory_v1 | near_limit_long | full_duration | -0.03250377 | 0.03294396 | 48/100 | 0.04888738 |
| tcc_calibration_confirmatory_v1 | near_limit_long | extra_sigma | -3.705175e-05 | 9.915154e-05 | 93/100 | 0.0003754939 |

No regime near_limit_long, viés relativo de r=139.8%. Cobertura94 de a/Rs=9.0%, duração=48.0%. Essa falha não é corrigida por condicionar aos aprovados; ver denominadores separados na tabela CSV.
Nos regimes short profundo/raso, pequeno viés médio de raio coexiste com cobertura conservadora. Isso é evidência útil de desempenho condicional, não calibração universal. Impact parameter e geometria podem permanecer pouco informados. r e r² têm eventos de inclusão ligados pela transformação monótona e não são validações independentes.
A prior Uniform(2,50) tem ETI94=[3.44,48.56], excluindo uma verdade3.3 dentro do suporte quando os dados não informam. É uma explicação-limite, não decomposição causal de todo viés. Alterar priors usando a verdade não seria uma correção legítima.

## Benchmark e limitação numérica

O benchmark histórico juliet foi executado sob contrato de dados/priors comparáveis, mas NUTS local não convergiu; ambas predições falharam no teste temporal. Concordância marginal é descritiva, não validação externa positiva nem validação retroativa de scientific_003 (prior de raio diferente).
Médias de t0 por cadeia local (dias), diretamente do trace: [-0.8316449974651853, 0.0004116573064685216, 0.00045667246422965367, 0.00045623048998087663]. Warmup histórico disponível: False.
No experimento diagnóstico do inicializador, 62/100 pontos diretos e 0/100 padronizados ficaram além de meio período. Não são as posições iniciais históricas, nem um teste final de convergência. A verificação de logdensidade/Jacobiano/gradiente demonstra equivalência da alternativa, não sua eficácia final.
O estudo complementar usa novos IDs/protocolo e mantém os runs antigos. Sua execução final e seus resultados não podem ser substituídos por pilotos.

## Ablations: decisões e falhas

9 controles PUB-04 têm sampler aprovado e PPC reprovado. Convergência, portanto, não foi suficiente para adequação. As três sistemáticas senoidais são determinísticas, não uma validação de GP. Baselines longos com divergências limitam efeitos pareados históricos: tabelas são descritivas, não efeitos físicos precisamente estabelecidos.
Controles deliberados de input inválido demonstram bloqueio de identidade, não recuperação de parâmetros. Uma não cobertura individual não define falso positivo do gate. A falha agregada no regime fraco limita a promessa de recuperação de parâmetros mesmo com gate aprovado.

## Resíduos observacionais existentes

Revisão sem refit: ordem temporal real, três segmentos por alvo, gaps entre pontos selecionados, máscaras in/out por duração catalogada e projeções de deslocamento do template. As projeções são aproximações descritivas e não medições independentes de deriva de efeméride.

| Alvo | Segmento | Pontos | Lag1 OOT | Lag1 após tendência linear |
|---|---|---:|---:|---:|
| HAT-P-7 b | hat_p_7_b:kplr010666592-2009131105131_llc.fits | 122 | 0.92012 | 0.3899 |
| HAT-P-7 b | hat_p_7_b:kplr010666592-2009166043257_llc.fits | 367 | 0.83986 | 0.76445 |
| HAT-P-7 b | hat_p_7_b:kplr010666592-2009259160929_llc.fits | 538 | 0.62683 | 0.60054 |
| Kepler-10 b | kepler_10_b:kplr011904151-2009231120729_slc.fits | 1000 | 0.20729 | 0.16669 |
| Kepler-10 b | kepler_10_b:kplr011904151-2009291181958_slc.fits | 1000 | -0.00033722 | 0.0065315 |
| Kepler-10 b | kepler_10_b:kplr011904151-2009350160919_slc.fits | 1000 | 0.69154 | 0.60022 |
| TrES-2 b | tres_2_b:kplr011446443-2009131105131_llc.fits | 45 | 0.85191 | 0.81329 |
| TrES-2 b | tres_2_b:kplr011446443-2009166043257_llc.fits | 179 | 0.50052 | 0.42671 |
| TrES-2 b | tres_2_b:kplr011446443-2009259160929_llc.fits | 388 | 0.70123 | 0.71017 |
| HD 189733 b | hd_189733_b:tess2021204101404-s0041-0000000256364928-0212-s_lc.fits | 1000 | 0.99362 | 0.99292 |
| HD 189733 b | hd_189733_b:tess2022190063128-s0054-0000000256364928-0227-s_lc.fits | 1000 | 0.95228 | 0.95293 |
| HD 189733 b | hd_189733_b:tess2024196212429-s0081-0000000256364928-0276-s_lc.fits | 1000 | 0.98076 | 0.97946 |
| Kepler-4 b | kepler_4_b:kplr011853905-2009131105131_llc.fits | 89 | 0.39691 | 0.40798 |
| Kepler-4 b | kepler_4_b:kplr011853905-2009166043257_llc.fits | 270 | -0.0049977 | -0.0014304 |
| Kepler-4 b | kepler_4_b:kplr011853905-2009259160929_llc.fits | 693 | 0.24808 | 0.21178 |

Estrutura fora do trânsito e persistente após remoção linear descritiva enfraquece uma explicação exclusivamente por forma de trânsito ou simples tendência. Não distingue, sozinha, variabilidade estelar, sistemática determinística ou ruído estocástico. Seleção/thinning muda os pares disponíveis; a escala lag1 não é sempre a cadência instrumental. Os cinco alvos continuam rejeitados no contrato histórico; não foram trocados.

## Escopo de afirmações e reprodução

`run_evaluations.json` separa bytes/proveniência, sampler, PPC, escala física, informação por parâmetro e permissões de claims. Razão SD posterior/prior é exploratória, sem cutoff ajustado; não é novo gate de identificabilidade. `claims.json` vincula cada conclusão às fontes.
M5 continua jitter branco independente. M6 não foi executado e não é requisito para entregar esta evidência TCC limitada. Não há novidade absoluta, generalização populacional ou garantia de exatidão pelos gates. Ver metodologia, limitações e bibliografia.
Restauração exata dos bytes, regeneração de relatórios e nova reprodução numérica são verificações diferentes. Bundle local não é arquivo público/DOI. `validate_publication_release.py` separa evidência inválida (exit2) de pendência editorial/arquivamento explicitamente identificada (exit1). Consulte os recibos finais, não assuma aprovação a partir desta síntese.
