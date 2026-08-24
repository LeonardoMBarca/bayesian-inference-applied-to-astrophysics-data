# M5 — trânsito físico Bayesiano

O M5 é genérico para os alvos suportados e não contém nomes, períodos ou paths
hard-coded de outro planeta. A execução combina:

- Gold com offsets removidos por segmento e proveniência até o FITS RAW;
- órbita circular `exoplanet.KeplerianOrbit`;
- `exoplanet.LimbDarkLightCurve` quadrática;
- `q1/q2` de Kipping transformados em `u1/u2` físicos;
- integração pelo `exposure_time_seconds` de cada observação;
- likelihood Normal com erro medido e jitter branco;
- NUTS, log-likelihood, prior predictive, PPC, resíduos e gates.

O arquivo `model_config.json` é gerado a partir do modelo executado e registra
target, dataset/checksum, priors, likelihood, exposição, sampler, diagnósticos,
PPC, escalas e decisão de interpretação. O relatório humano é gerado do mesmo
objeto de configuração.

## Gate científico

Uma execução é interpretável somente se cumprir simultaneamente:

- R-hat máximo ≤ 1,01;
- ESS mínimo ≥ 400;
- zero divergências;
- BFMI mínimo ≥ 0,30;
- PPC criado, cobertura de 94% entre 0,80 e 0,99 e resíduos padronizados com
  desvio entre 0,5 e 2,0;
- Gold `segment_normalized`, `dataset_id`, segmentos e exposição presentes;
- razão jitter/erro medido ≤ 20 e posterior de raio sem saturar limites de
  revisão.

O status `completed` significa que os artefatos foram produzidos; não substitui
`scientifically_interpretable=true`. Falhas registram traceback e permanecem
disponíveis para auditoria.

## Limitações

O período e a excentricidade são fixos, parâmetros estelares não são inferidos
conjuntamente, não existe GP/covariância temporal e `r²` é uma profundidade
geométrica. A validade física também depende da hipótese de normalização Gold e
da qualidade do PDCSAP_FLUX.
