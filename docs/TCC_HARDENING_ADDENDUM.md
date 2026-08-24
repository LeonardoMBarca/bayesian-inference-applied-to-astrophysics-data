# Adendo metodológico e de resultados após hardening

Este texto é a fonte Markdown atual para incorporar ao TCC. Os DOCX/PDF em
`tcc-docs/` são snapshots binários e não foram reescritos automaticamente.

## Dados e pré-processamento

O estado atual suporta HAT-P-7 b e Kepler-10 b a partir de configuração única.
Cada RAW usado possui origem, path relativo POSIX, status e SHA-256. O histórico
de obtenções é separado do manifesto deduplicado de estado atual. A Silver
preserva FITS, missão, quarter/sector/campaign, cadência, exposição e unidades
explícitas.

Para Kepler-10 b foram selecionados três FITS Kepler de cadência curta, com
exposição mediana de 58,848763 s. A Gold filtra qualidade e normaliza cada
segmento pela mediana fora do trânsito antes da concatenação. As medianas RAW
dos segmentos (556934,94; 524924,40; 527039,10) tornam-se exatamente 1,0 nas
regiões de baseline. O dataset é
`kepler_10_b-b4d1e6ec961c1f4d`, com 115.363 linhas e janela de 40.836 linhas. A
identidade vincula o conteúdo normalizado e os checksums dos FITS de origem.

## Modelo M5 executado

O M5 usa órbita Kepleriana circular, limb darkening quadrático com
parametrização `q1/q2`, período fixo de 0,8374907 d e integração por exposição
com oversampling 15. O prior de `Rp/Rs` é lognormal, positivo e centrado em
`sqrt(transit_depth_fraction)`; o perfil baseline usa sigma log 0,5. A
likelihood é Normal com `sqrt(flux_err² + extra_sigma²)`, onde `extra_sigma` é
jitter branco independente. Não há GP nem modelo de ruído correlacionado.

O run `scientific_003` usou 3.000 pontos estratificados por fase e segmento,
quatro cadeias, 800 iterações de tuning e 800 draws por cadeia, NUTS,
`target_accept=0,95` e semente 42. A entrada possui SHA-256
`6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791`.

## Resultados e diagnóstico

- R-hat máximo: 1,00508421;
- ESS mínimo: 582,0677;
- divergências: 0;
- BFMI mínimo: 0,7317310;
- cobertura posterior-preditiva de 94%: 0,933667;
- desvio dos resíduos padronizados: 1,003572;
- razão jitter/erro medido: 1,017704;
- `Rp/Rs`: média 0,01249085, HDI 94% [0,01092702; 0,01453419];
- profundidade geométrica: média 0,00015692, HDI 94%
  [0,00011940; 0,00021124];
- duração total: média 1,90182 h, HDI 94% aproximadamente
  [1,69601; 2,19077] h.

Os gates de sampler, PPC e validade científica passaram. O valor de escala de
catálogo para `Rp/Rs` (0,0138528) está no HDI posterior; contudo, a profundidade
catalogada também centraliza o prior. Isso é uma verificação de escala, não
validação externa independente e não foi usado para ajustar a saída.

## Sensibilidade, ruído e comparação

A sensibilidade usa três priors justificados (`catalog_tighter`, `baseline` e
`weak`), cada um com prior predictive e gate independente. Somente runs que
passem todos os gates podem ser comparados. Injeções distintas foram geradas
para ruído branco, sistemática sinusoidal determinística e ruído AR(1). O M5
atual não modela a covariância AR(1); portanto, esses artefatos não demonstram
recuperação de ruído correlacionado.

LOO/WAIC/ELPD só são autorizados entre as mesmas observações e likelihood, com
log-likelihood pontual e gates aprovados. RMSE/MAE são relatados separadamente.

O experimento completo `sensitivity_002` satisfez esse contrato nos três perfis.
Todos passaram R-hat, ESS, divergências, BFMI, PPC e gates de escala. O maior
deslocamento em relação ao posterior baseline foi 0,77% em `Rp/Rs`, 1,59% em
profundidade, 0,18% em jitter e 0,34% em duração, com sobreposição dos HDIs de
94%. A conclusão é limitada à família de priors efetivamente testada.

Os valores formais de LOO/WAIC foram preservados, mas o PSIS-LOO emitiu alerta:
15, 22 e 25 observações apresentaram Pareto-k acima de 0,7 nos três runs, com
máximo 1,163. Consequentemente, nenhum ranking é defendido; o alerta faz parte
do resultado científico, não é descartado como detalhe computacional.

## Limitações

Período e excentricidade são fixos; parâmetros estelares não são inferidos em
conjunto; a normalização por segmento é hipótese metodológica; o jitter é
branco; e `r²` é profundidade geométrica, não necessariamente a profundidade
aparente sob limb darkening. Traces NetCDF não são versionados no Git e devem
ser regenerados pelo ambiente fixado quando auditoria amostra-a-amostra for
necessária.
