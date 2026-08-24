# Notebooks

O notebook atual é `07_bayesian_physical_transit.ipynb`, uma interface fina ao
código canônico de `src/bayesian_modeling/physical_transit.py`. Por padrão ele
somente inspeciona artefatos; a execução cara exige alterar explicitamente a
flag da célula.

Os notebooks `02` a `06` são snapshots históricos específicos de HAT-P-7 b.
Eles permanecem para rastreabilidade e não devem ser usados para descrever o M5
ou Kepler-10 b. O notebook `06` usa o comparador atual, que deve rejeitar a
comparação formal quando os configs históricos não contêm o contrato exigido.
Os imports antigos em `scripts/` continuam disponíveis, mas delegam para a EDA
em `src/gold_analysis/` e para M1–M3 em `src/bayesian_modeling/legacy/`.
