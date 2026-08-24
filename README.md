# Inferência Bayesiana aplicada a dados astrofísicos

Software científico do TCC de Leonardo Moraes Barca para ingestão rastreável de
curvas de luz públicas, preparação RAW/Silver/Gold e inferência bayesiana de
trânsitos de exoplanetas.

O estado endurecido suporta dois alvos definidos em uma única configuração:

| alvo | missão Gold | cadência | papel |
|---|---|---|---|
| Kepler-10 b | Kepler | curta, 58,8488 s | alvo primário e M5 validado |
| HAT-P-7 b | Kepler | longa, 1765,46 s | alvo de backup |

A fonte autoritativa de identidade, período, época, duração, profundidade e
política de cadência é [`src/project_config.py`](src/project_config.py). Código
genérico não deve introduzir valores planetários fora desse contrato.

## Pipeline e proveniência

- **RAW** preserva respostas e FITS sem limpeza. O histórico append-only fica em
  `data/raw/_manifests/raw_data_manifest.*`; o estado atual deduplicado e
  verificado por SHA-256 fica em `raw_data_current_state.*`.
- **Silver** lê somente o estado RAW, explicita unidades nos nomes das colunas e
  preserva origem RAW, FITS, missão, quarter/sector/campaign, cadência e tempo de
  exposição.
- **Gold** seleciona a cadência exigida pelo alvo, filtra qualidade e normaliza
  cada `segment_id` separadamente pela mediana fora do trânsito. Os offsets não
  são tratados como ruído astrofísico. O `dataset_id`, a política e os
  diagnósticos por segmento são persistidos. A identidade do dataset é derivada
  do conteúdo científico normalizado e dos SHA-256 dos FITS de origem.
- **M5** só aceita Gold com `preprocessing_status=segment_normalized` e identidade
  compatível com a configuração autoritativa.

Fontes públicas usadas: NASA Exoplanet Archive, MAST/Lightkurve/Astroquery,
Exo.MAST e ETD/VarAstro. Uma nova coleta RAW pode alterar o estado público; para
reproduzir exatamente o dataset publicado, valide os RAW versionados e
reconstrua as camadas derivadas sem baixar novamente.

## Organização do código

`scripts/` é a interface estável de linha de comando e contém apenas entry
points finos. Implementações reutilizáveis ficam agrupadas em `src/`: pipelines
RAW/Silver/Gold, EDA, modelagem Bayesiana e ferramentas de validação. Os modelos
históricos M1–M3 estão isolados em `src/bayesian_modeling/legacy/`, sem alterar
seus comandos ou os imports usados pelos notebooks.

Veja [`scripts/README.md`](scripts/README.md) para o mapa de comandos e
[`src/README.md`](src/README.md) para o mapa dos pacotes. Um teste de arquitetura
impede que novas implementações extensas voltem a ser adicionadas diretamente a
`scripts/`.

## Ambiente

O ambiente científico validado em 24 de agosto de 2026 usa Python 3.14.6. As
dependências diretas são fixadas, inclusive o ecossistema `exoplanet` usado pelo
M5.

O stack foi validado em Linux/WSL com `gcc` e `g++` disponíveis para extensões
compiladas. Em Windows, recomenda-se WSL; a identidade efetiva do toolchain e
das bibliotecas é gravada por run.

```bash
conda env create -f environment.yml
conda activate bayesian-astrophysics
```

Alternativamente:

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Reconstrução

Para validar o estado RAW presente e reconstruir Silver e Gold:

```bash
python scripts/refresh_raw_manifest_state.py
python scripts/build_silver_data.py
python scripts/build_gold_data.py
python scripts/validate_hardened_artifacts.py
```

A coleta de novas evidências, que requer rede, é separada:

```bash
python scripts/download_raw_data.py
```

Artefatos Gold centrais:

```text
data/gold/<target>/modeling/dataset_metadata.json
data/gold/<target>/modeling/segment_normalization_diagnostics.csv
data/gold/<target>/modeling/segment_normalized_lightcurve.csv
data/gold/<target>/modeling/transit_window_lightcurve.csv
```

## Modelo físico M5

Execução recomendada para Kepler-10 b:

```bash
python scripts/run_kepler_10b.py \
  --run-id scientific_003 \
  --draws 800 --tune 800 --chains 4 --cores 4 \
  --target-accept 0.95 --prior-profile baseline
```

O M5 compartilhado está em
[`src/bayesian_modeling/physical_transit.py`](src/bayesian_modeling/physical_transit.py).
Ele implementa:

- órbita Kepleriana circular com período do alvo fixado;
- trânsito com escurecimento de bordo quadrático e parametrização triangular
  `q1/q2` de Kipping;
- integração de cada observação pelo tempo de exposição, com oversampling;
- prior lognormal de `Rp/Rs` centrado em `sqrt(transit_depth_fraction)`;
- likelihood Normal com erro medido e jitter branco independente;
- NUTS, log-likelihood pontual, prior predictive e posterior predictive checks;
- parâmetros derivados e artefatos específicos por alvo e `run_id`.

Evidência do run `scientific_003`:

| diagnóstico/resultado | valor |
|---|---:|
| dataset | `kepler_10_b-b4d1e6ec961c1f4d` |
| R-hat máximo | 1,00508421 |
| ESS mínimo | 582,0677 |
| divergências | 0 |
| BFMI mínimo | 0,7317310 |
| cobertura PPC de 94% | 0,933667 |
| desvio dos resíduos padronizados | 1,003572 |
| `Rp/Rs` médio, HDI 94% | 0,01249085 [0,01092702; 0,01453419] |
| profundidade geométrica média, HDI 94% | 0,00015692 [0,00011940; 0,00021124] |
| gate científico | aprovado |

O checksum SHA-256 da entrada de 3.000 pontos foi
`6653fced1df0b3a29be96d181daa695f86ef709a7aa459bc1b3f837d48ad8791`.
O relatório completo é
[`reports/bayesian_physical_transit_kepler_10_b_scientific_003_report.md`](reports/bayesian_physical_transit_kepler_10_b_scientific_003_report.md).

O modelo **não** contém Gaussian Process nem likelihood de ruído correlacionado.
O termo `extra_sigma` é apenas jitter branco. A interpretação científica só é
liberada quando passam, em conjunto, R-hat, ESS, divergências, BFMI, PPC,
proveniência Gold e verificações de escala. Runs reprovados permanecem
registrados, mas não sustentam conclusões físicas.

## Sensibilidade, ruído e comparação

- `scripts/run_bayesian_sensitivity.py` executa perfis de prior
  `catalog_tighter`, `baseline` e `weak`, cada um com gate independente. Uma
  cadeia dominada pelo prior ou não convergida é resultado negativo, não
  robustez.
- `scripts/run_bayesian_noise_injection.py` separa ruído branco, sinal
  sinusoidal determinístico e ruído AR(1). O gerador testa a injeção; não afirma
  que o M5 recupere ruído correlacionado.
- `scripts/run_model_comparison.py` calcula LOO/WAIC apenas se dataset, checksum
  das observações, likelihood, log-likelihood e gates forem compatíveis. RMSE e
  MAE permanecem métricas preditivas separadas; nenhum score heurístico é
  misturado com evidência Bayesiana formal.

No experimento `sensitivity_002`, os três perfis passaram independentemente os
gates e usaram o mesmo dataset/hash. Em relação ao baseline, o maior deslocamento
relativo foi 0,77% em `Rp/Rs`, 1,59% em profundidade, 0,18% em jitter e 0,34% em
duração; todos os HDIs de 94% contêm a média baseline. Isso é evidência
descritiva de baixa sensibilidade dentro da família de priors testada, não uma
prova universal de robustez.

LOO e WAIC foram calculados para os três runs comparáveis, mas LOO encontrou
15–25 observações com Pareto-k acima de 0,7 (máximo 1,163). Por isso o artefato
[`reports/model_comparison/prior_sensitivity_002/comparison_summary.json`](reports/model_comparison/prior_sensitivity_002/comparison_summary.json)
mantém os valores para auditoria e recusa promovê-los a ranking confiável. A
síntese de sensibilidade está em
[`reports/sensitivity/kepler_10_b/sensitivity_002/sensitivity_report.md`](reports/sensitivity/kepler_10_b/sensitivity_002/sensitivity_report.md).

## Testes e CI

```bash
python scripts/verify_scientific_environment.py
python -m ruff check .
python scripts/run_ci_tests.py
python scripts/validate_hardened_artifacts.py
```

A suíte cobre configuração de alvo, unidades, paths POSIX, seleção de cadência,
exposição FITS, normalização por segmento, isolamento de run, modelo físico,
prior predictive, BFMI do ArviZ atual, gates científicos, comparação formal e
experimentos de ruído. Há também uma integração clean-room com uma guarda
verificada sobre as APIs padrão de socket do Python que cria FITS pequenos e
percorre RAW→Silver→Gold. Essa guarda não equivale a um namespace de rede do
sistema operacional. O workflow em
`.github/workflows/ci.yml` executa a suíte prática e a validação dos artefatos.

## Artefatos históricos e armazenamento

Modelos M1–M3, relatórios antigos, notebooks e context exports anteriores ao
hardening são snapshots históricos. Eles não descrevem automaticamente o M5
atual e não devem ser combinados com o dataset de Kepler-10 b sem validação de
comparabilidade.

Traces NetCDF são grandes e não são versionados no Git; configurações, status,
resumos e tabelas permanecem rastreáveis. Veja
[`docs/STORAGE_POLICY.md`](docs/STORAGE_POLICY.md) para o contrato completo.

## Limitações científicas

O M5 fixa período e excentricidade, não infere parâmetros estelares em conjunto,
usa somente jitter branco e trata a normalização por segmento como hipótese de
pré-processamento. `r²` é profundidade geométrica de referência; a profundidade
aparente depende de limb darkening e integração de exposição. Valores de
catálogo justificam priors e validam escala, mas não são alvos para ajuste dos
resultados.

Licença: [MIT](LICENSE).
