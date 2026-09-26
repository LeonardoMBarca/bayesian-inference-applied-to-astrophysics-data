# Bibliografia comentada para consulta

Snapshot de fontes primárias consultadas em 2026-09-26. Revisão direcionada, não sistemática nem exaustiva. Os metadados abaixo são os verificados na matriz; DOI ausente não significa que o trabalho não tenha DOI. Títulos abreviados são identificadores de leitura, não uma exportação bibliográfica formal para submissão.

Fonte machine-readable: [`NOVELTY_MATRIX.json`](NOVELTY_MATRIX.json). Posicionamento e limites: [`NOVELTY_MATRIX.md`](NOVELTY_MATRIX.md).

## Trabalhos e normas

### 1. Mandel & Agol — Analytic Light Curves for Planetary Transit Searches (2002)

Status: published. Identificador da matriz: `mandel_agol_2002`.

Relevância: Physical transit prediction. Established physical foundation; no new transit equation claimed here.

DOI: [10.1086/345520](https://doi.org/10.1086/345520).

- [Fonte primária](https://arxiv.org/abs/astro-ph/0210099)

### 2. Kipping — Binning is sinning (2010)

Status: published. Identificador da matriz: `kipping_exposure_2010`.

Relevância: Bias from finite exposure. Our exposure ablation quantifies an established effect within the frozen workflow, not discovery of that effect.

- [Fonte primária](https://arxiv.org/abs/1004.3741)

### 3. Kipping — Efficient, uninformative sampling of limb darkening coefficients (2013)

Status: published. Identificador da matriz: `kipping_ld_2013`.

Relevância: Physical limb-darkening prior support. Adopted parameterization, not original contribution.

- [Fonte primária](https://arxiv.org/abs/1308.0009)

### 4. Kreidberg — batman (2015)

Status: published. Identificador da matriz: `batman_2015`.

Relevância: Fast transit forward calculation. Independent forward primitive for juliet comparison; agreement is computational, not independent astrophysical evidence.

DOI: [10.1086/683602](https://doi.org/10.1086/683602).

- [Fonte primária 1](https://arxiv.org/abs/1507.08285)
- [Fonte primária 2](https://lkreidberg.github.io/batman/docs/html/index.html)

### 5. Foreman-Mackey et al. — exoplanet (2021)

Status: published. Identificador da matriz: `exoplanet_2021`.

Relevância: Probabilistic astronomical time series. M5 depends on this work; cannot present its differentiable physical modeling as our invention.

DOI: [10.21105/joss.03285](https://doi.org/10.21105/joss.03285).

- [Fonte primária 1](https://joss.theoj.org/papers/10.21105/joss.03285)
- [Fonte primária 2](https://arxiv.org/abs/2105.01994)

### 6. Espinoza, Kossakowski & Brahm — juliet (2019)

Status: published. Identificador da matriz: `juliet_2019`.

Relevância: Joint transit and radial-velocity inference. Already solves flexible Bayesian transit fitting; proposed extra contribution is experimentally evaluated evidence promotion/lineage.

DOI: [10.1093/mnras/stz2688](https://doi.org/10.1093/mnras/stz2688).

- [Fonte primária](https://academic.oup.com/mnras/article/490/2/2262/5583056)

### 7. Günther & Daylan — allesfitter (2021)

Status: published. Identificador da matriz: `allesfitter_2021`.

Relevância: Joint star/exoplanet inference. Do not claim fitters lack injection/recovery or publication products.

DOI: [10.3847/1538-4365/abe70e](https://doi.org/10.3847/1538-4365/abe70e).

- [Fonte primária 1](https://arxiv.org/abs/2003.14371)
- [Fonte primária 2](https://arxiv.org/html/2003.14371v2)

### 8. Abril-Pla et al. — PyMC (2023)

Status: published. Identificador da matriz: `pymc_2023`.

Relevância: General probabilistic programming. Existing inference engine; our contribution must reside in experiment contracts/evidence, not NUTS availability.

DOI: [10.7717/peerj-cs.1516](https://doi.org/10.7717/peerj-cs.1516).

- [Fonte primária](https://www.pymc.io/welcome.html)

### 9. Hoffman & Gelman — The No-U-Turn Sampler (2014)

Status: published. Identificador da matriz: `nuts_2014`.

Relevância: HMC trajectory adaptation. Sampler is prior art; numerical convergence alone cannot establish data-model adequacy.

- [Fonte primária](https://jmlr.org/papers/v15/hoffman14a.html)

### 10. Vehtari et al. — Rank-normalization, folding, and localization (2021)

Status: published. Identificador da matriz: `rhat_2021`.

Relevância: MCMC convergence/efficiency diagnosis. We implement and empirically examine application gates; no diagnostic invention claimed.

DOI: [10.1214/20-BA1221](https://doi.org/10.1214/20-BA1221).

- [Fonte primária](https://arxiv.org/abs/1903.08008)

### 11. Talts et al. — Validating Bayesian Inference Algorithms with Simulation-Based Calibration (2018)

Status: preprint; revised author version exists. Identificador da matriz: `sbc_2018`.

Relevância: Posterior algorithm validation. SBC theory is established; fixed-truth scenario experiments must not be relabeled SBC.

- [Fonte primária 1](https://arxiv.org/abs/1804.06788)
- [Fonte primária 2](https://sites.stat.columbia.edu/gelman/research/unpublished/sbc.pdf)

### 12. Gelman et al. — Bayesian Workflow (2020)

Status: preprint. Identificador da matriz: `bayesian_workflow_2020`.

Relevância: Reliability beyond posterior computation. The overarching workflow philosophy is prior art; our intended value is concrete transit evidence and auditability.

- [Fonte primária](https://arxiv.org/abs/2011.01808)

### 13. Vehtari et al. — Pareto Smoothed Importance Sampling (2024)

Status: published. Identificador da matriz: `psis_2024`.

Relevância: Unstable importance weights. No LOO ranking without a valid predictive contract and reliable importance diagnostics.

- [Fonte primária](https://arxiv.org/abs/1507.02646)

### 14. Christiansen et al. — Measuring Transit Signal Recovery III (2016)

Status: published. Identificador da matriz: `kepler_injection_2016`.

Relevância: Kepler detection efficiency. Injection/recovery and failure transparency pre-exist; our estimand is physical-parameter uncertainty under declared regimes.

- [Fonte primária](https://arxiv.org/abs/1605.05729)

### 15. Twicken et al. — Kepler Data Validation I (2018)

Status: published. Identificador da matriz: `kepler_dv_2018`.

Relevância: Vetting transit candidates. Validation gates in transit pipelines are established; our gates address posterior interpretability, not planet confirmation.

- [Fonte primária](https://arxiv.org/abs/1803.04526)

### 16. Gibson et al. — A Gaussian process framework for modelling instrumental systematics (2012)

Status: published. Identificador da matriz: `gibson_gp_2012`.

Relevância: Transit systematics and uncertainty. GP transit inference is established; M6 must earn benefit through controlled validation, not complexity.

DOI: [10.1111/j.1365-2966.2011.19915.x](https://doi.org/10.1111/j.1365-2966.2011.19915.x).

- [Fonte primária](https://academic.oup.com/mnras/article/419/3/2683/1070795)

### 17. Gibson — Reliable inference of exoplanet light curve parameters (2014)

Status: published. Identificador da matriz: `gibson_reliability_2014`.

Relevância: Reliability under deterministic/stochastic systematics. Direct methodological precursor; simulated demonstrations of unreliable uncertainty are not new.

DOI: [10.1093/mnras/stu1975](https://doi.org/10.1093/mnras/stu1975).

- [Fonte primária](https://arxiv.org/abs/1409.5668)

### 18. Foreman-Mackey et al. — Fast and Scalable Gaussian Process Modeling (2017)

Status: published. Identificador da matriz: `celerite_2017`.

Relevância: Scalable astronomical covariance. Existing covariance algorithm; GP absorption/coverage must be evaluated in our parameter regimes.

DOI: [10.3847/1538-3881/aa9332](https://doi.org/10.3847/1538-3881/aa9332).

- [Fonte primária 1](https://arxiv.org/abs/1703.09710)
- [Fonte primária 2](https://celerite2.readthedocs.io/en/latest/user/citation/)

### 19. Thompson et al. — Octofitter (2023)

Status: published. Identificador da matriz: `octofitter_2023`.

Relevância: Multimethod exoplanet orbit inference/detection. Bayesian exoplanet software already integrates calibration/PPC; transit-specific audit contract remains candidate contribution only.

DOI: [10.3847/1538-3881/acf5cc](https://doi.org/10.3847/1538-3881/acf5cc).

- [Fonte primária 1](https://arxiv.org/abs/2402.01971)
- [Fonte primária 2](https://nrc-publications.canada.ca/eng/view/ft/?id=4a8d7043-fbeb-42fb-8058-00a5b077d601)

### 20. Martin & Mortlock — An approach to robust Bayesian regression in astronomy (2025)

Status: published. Identificador da matriz: `tcup_2025`.

Relevância: Astronomical regression under misspecification. Contemporary astronomy already distinguishes these calibration designs; adopt precise terminology.

DOI: [10.1093/rasti/rzaf035](https://doi.org/10.1093/rasti/rzaf035).

- [Fonte primária](https://academic.oup.com/rasti/article/doi/10.1093/rasti/rzaf035/8233173)

### 21. Servillat et al. — IVOA Provenance Data Model 1.0 (2020)

Status: IVOA Recommendation. Identificador da matriz: `ivoa_provenance_2020`.

Relevância: Astronomical data lineage interchange. Provenance as scientific trust evidence is established; our SHA manifests are not automatically IVOA-conformant.

- [Fonte primária](https://www.ivoa.net/documents/ProvenanceDM/)

### 22. IVOA — Data Origin in the VO 1.2 (2026)

Status: Endorsed Note, 2026-03-31. Identificador da matriz: `ivoa_origin_2026`.

Relevância: Basic origin metadata from VO services. Current origin-metadata guidance complements, not replaces, content checks and inferential validation.

- [Fonte primária](https://www.ivoa.net/documents/DataOrigin/20260331/EN-data-origin-1.2-20260331.html)

### 23. Akhlaghi et al. — Toward Long-Term and Archivable Reproducibility (2021)

Status: published. Identificador da matriz: `maneage_2021`.

Relevância: Long-term reproducibility/archiving. Neither lineage nor generated manuscript quantities are new; our narrower empirical transit validation is the intended addition.

DOI: [10.1109/MCSE.2021.3072860](https://doi.org/10.1109/MCSE.2021.3072860).

- [Fonte primária 1](https://arxiv.org/abs/2006.03018)
- [Fonte primária 2](https://gitlab.com/makhlaghi/maneage-paper)

### 24. Halchenko et al. — DataLad (2021)

Status: published. Identificador da matriz: `datalad_2021`.

Relevância: Joint versioning of data/code/process. Content-addressed scientific evidence is prior art; lightweight repository manifests are an integration choice, not an invented paradigm.

DOI: [10.21105/joss.03262](https://doi.org/10.21105/joss.03262).

- [Fonte primária 1](https://joss.theoj.org/papers/10.21105/joss.03262)
- [Fonte primária 2](https://docs.datalad.org/en/maint/design/provenance_capture.html)
- [Fonte primária 3](https://docs.datalad.org/en/stable/basics.html)

## Documentação das ferramentas e do benchmark

Estas páginas documentam o software e não substituem os artigos acima. Recursos `latest`/`master` podem mudar: a comparação executável deve usar a versão fixada e seus hashes.

- [juliet: parâmetros e distribuições a priori](https://juliet.readthedocs.io/en/latest/user/priorsnparameters.html). Mapeamento físico, unidades de jitter e famílias de prior.
- [juliet: modelos lineares](https://juliet.readthedocs.io/en/latest/tutorials/linearmodels.html). Baseline aditivo por regressor constante.
- [juliet: ajuste de trânsitos](https://juliet.readthedocs.io/en/latest/tutorials/transitfits.html). Diluição, fluxo e uso das curvas.
- [juliet: API](https://juliet.readthedocs.io/en/latest/user/api.html). Supersampling e tempo de exposição.
- [juliet: código-fonte oficial](https://github.com/nespinoza/juliet). Fonte para verificar convenções, sem substituir testes da versão instalada.
- [juliet: metadados de release](https://pypi.org/project/juliet/2.2.10/). Benchmark selecionado antes dos resultados finais.
- [allesfitter: documentação oficial](https://www.allesfitter.com/). Candidato avaliado, não descartado por desacordo numérico.
- [allesfitter: metadados de release](https://pypi.org/project/allesfitter/1.2.10/). Idade da release não prova abandono.

## Uso recomendado

Leia primeiro juliet, allesfitter, exoplanet e Gibson (2014) para entender a forte sobreposição metodológica já existente. Talts et al., Bayesian Workflow, diagnósticos R-hat e PSIS delimitam quais conclusões estatísticas são permitidas. IVOA, Maneage e DataLad fundamentam a camada de rastreabilidade. Nenhuma fonte isolada comprova a novidade ou a validade dos novos resultados deste repositório.

