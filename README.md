# Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos

Projeto de TCC do MBA em Data Science e Analytics.

- Aluno: Leonardo Moraes Barca
- Orientadora: Patrícia Belfiore Fávero
- Tema: inferência bayesiana aplicada à estimação de parâmetros físicos em
  sistemas astrofísicos sob incerteza observacional, com ênfase em curvas de
  luz de trânsitos de exoplanetas.

## Objetivo das etapas implementadas

O projeto possui camadas **RAW**, **Silver** e uma **Gold inicial**
implementadas para um pequeno datalake local.

A RAW baixa dados públicos e registra respostas, metadados, páginas
consultadas, logs e checksums sem limpar, normalizar, fasear, remover outliers
ou modelar os dados.

A Silver lê exclusivamente a RAW, valida manifestos, consolida catálogos,
extrai tabelas de curvas de luz a partir dos FITS/JSONs locais e registra
proveniência linha a linha. A RAW permanece imutável.

A Gold inicial seleciona um planeta candidato e prepara uma curva de luz
operacional para modelagem bayesiana futura. Ela ainda não contém inferência
bayesiana.

## Fontes

1. **NASA Exoplanet Archive**
   Consultas ADQL no endpoint TAP síncrono para as tabelas `pscomppars` e
   `ps`, incluindo um snapshot controlado dos planetas em trânsito.
2. **MAST / Lightkurve / Astroquery**
   Busca nas missões Kepler, K2 e TESS. Os resultados completos das buscas
   são registrados e no máximo três produtos FITS por planeta e missão são
   selecionados. Astroquery é usado como fallback quando Lightkurve falha.
3. **Exo.MAST**
   A API pública é usada para resolver identificadores, propriedades e listas
   de TCEs disponíveis. Os FITS originais continuam sendo obtidos pelo MAST.
4. **ETD / VarAstro**
   Coleta conservadora de páginas HTML públicas, metadados tabulares e links
   diretos de arquivos quando expostos pelo portal. A lista pública de
   trânsitos e até cinco respostas JSON de curvas por planeta também são
   preservadas sem conversão. Não há login, Selenium, automação de navegador
   ou tentativa de contornar proteções.

Planetas configurados: HAT-P-7 b, TrES-2 b, HD 189733 b, HD 209458 b,
WASP-12 b, WASP-10 b, WASP-4 b e HAT-P-32 b.

## Instalação

Use um ambiente virtual local. O projeto não requer instalação global de
pacotes e foi validado com Python 3.12:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Se o módulo `venv` não estiver disponível, use um ambiente Conda local:

```bash
conda create --prefix .venv python=3.12 pip
conda activate ./.venv
python -m pip install -r requirements.txt
```

## Execução

Pipeline RAW completo:

```bash
python scripts/download_raw_data.py
```

Coletores RAW separados:

```bash
python scripts/download_nasa_exoplanet_archive.py
python scripts/download_mast_lightcurves.py
python scripts/download_etd_varastro.py
```

Os parâmetros de coleta ficam em
[`scripts/raw_data_config.py`](scripts/raw_data_config.py), incluindo planetas,
estrelas hospedeiras, missões, limites, timeout, User-Agent e delay do ETD.

## Camada Silver

Pipeline Silver completo:

```bash
python scripts/build_silver_data.py
```

Execuções Silver separadas:

```bash
python scripts/build_silver_catalogs.py
python scripts/build_silver_lightcurves.py
python scripts/build_silver_etd.py
```

A saída da Silver fica em:

```text
data/silver/
```

A configuração fica em
[`scripts/silver_data_config.py`](scripts/silver_data_config.py). A Silver não
depende de rede e não faz novos downloads; ela usa
`data/raw/_manifests/raw_data_manifest.csv` como referência primária de
proveniência.

A documentação técnica da Silver fica em:

```text
docs/silver/
```

Principais artefatos:

- `data/silver/catalogs/nasa/pscomppars_selected_planets.csv`;
- `data/silver/catalogs/nasa/ps_all_solutions.csv`;
- `data/silver/catalogs/exomast/exomast_identifiers.csv`;
- `data/silver/catalogs/exomast/exomast_properties.csv`;
- `data/silver/catalogs/exomast/exomast_tces.csv`;
- `data/silver/lightcurves/mast/mast_fits_metadata.csv`;
- `data/silver/lightcurves/mast/{planet_slug}/{mission}_lightcurve.csv`;
- `data/silver/etd/etd_observations.csv`;
- `data/silver/etd/etd_lightcurve_points.csv`;
- `data/silver/validation/silver_summary_by_planet.csv`;
- `data/silver/manifests/silver_data_manifest.csv`;
- `data/silver/logs/build_silver_data.log`.

Nesta etapa ainda não há normalização final, faseamento orbital, remoção de
outliers, modelagem física ou inferência bayesiana.

## Camada Gold

Pipeline Gold completo:

```bash
python scripts/build_gold_data.py
```

Relatório de seleção Gold:

```bash
python scripts/build_gold_selection_report.py
```

A saída da Gold fica em:

```text
data/gold/
```

A configuração fica em
[`scripts/gold_data_config.py`](scripts/gold_data_config.py). A Gold lê
exclusivamente `data/silver/` e não modifica RAW ou Silver.

Planeta selecionado na execução inicial:

```text
HAT-P-7 b
```

Missão selecionada:

```text
Kepler
```

Artefato principal para modelagem futura:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

A Gold inicial inclui seleção de candidato, seleção de fluxo, filtro simples
por qualidade, fase orbital e janela de trânsito. Ela ainda não executa PyMC,
ArviZ, batman, exoplanet, Gaussian Process, ajuste de trânsito ou posterior
sampling.

## EDA da Gold

Diagnóstico exploratório da Gold de HAT-P-7 b:

```bash
python scripts/analyze_gold_lightcurve.py
```

Artefatos gerados:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
reports/gold_eda_hat_p_7_b_report.md
figures/gold_eda/hat_p_7_b/
tables/gold_eda/hat_p_7_b/
```

A EDA lê `data/gold/`, mas não modifica RAW, Silver ou Gold. Ela confirmou
trânsito visualmente identificável, disponibilidade de `flux_err` e recomendou
uma janela preliminar de `±0,15` dias para a primeira modelagem.

## Modelo Bayesiano M1

Baseline bayesiano simples para HAT-P-7 b:

```bash
python scripts/run_bayesian_baseline.py
```

Reexecução robusta recomendada do mesmo M1 com NUTS:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

Artefatos principais:

```text
notebooks/03_bayesian_baseline_hat_p_7_b.ipynb
models/modeling_roadmap.md
models/bayesian_baseline/hat_p_7_b/trace.nc
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
reports/bayesian_baseline_hat_p_7_b_report.md
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
figures/bayesian_baseline/hat_p_7_b/
tables/bayesian_baseline/hat_p_7_b/
```

O M1 usa `abs(phase) <= 0,15`, normalização local por mediana de baseline e um
modelo box-shaped para estimar uma posterior de `depth` e derivar
`Rp/Rs = sqrt(depth)`.

A primeira execução curta com Metropolis foi preservada como histórico
operacional em `runs/001_operational_metropolis`. A execução recomendada para
interpretação preliminar do M1 é `runs/002_nuts_robust`, criada em ambiente
local `.venv-nuts` com NUTS:

- pontos usados: `516`;
- draws/tune/chains: `2000 / 2000 / 4`;
- profundidade posterior média: `0,00525258`;
- HDI 94% da profundidade: `[0,00464576, 0,00587726]`;
- `Rp/Rs` posterior médio: `0,07243869`;
- HDI 94% de `Rp/Rs`: `[0,06815983, 0,07666328]`;
- maior R-hat: `1,00088086`;
- menor ESS: `4553,60020940`;
- divergências: `0`.

Mesmo com bons diagnósticos, o M1 continua sendo baseline comparativo, não
caracterização física final do planeta.

## Modelo Bayesiano M2

Regressão bayesiana preditiva do fluxo normalizado em função da fase:

```bash
.venv-nuts/bin/python scripts/run_bayesian_predictive_phase_regression.py
```

Artefatos principais:

```text
notebooks/04_bayesian_predictive_phase_regression_hat_p_7_b.ipynb
models/bayesian_predictive_phase_regression/hat_p_7_b/runs/001_nuts/trace.nc
reports/bayesian_predictive_phase_regression_hat_p_7_b_report.md
figures/bayesian_predictive_phase_regression/hat_p_7_b/
tables/bayesian_predictive_phase_regression/hat_p_7_b/
docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/
```

O M2 usa a mesma janela e normalização do M1, mas modela o fluxo como função
suave da fase com funções de base radial gaussianas fixas. Ele não estima
diretamente `Rp/Rs` e não é modelo físico final.

Resumo da execução:

- pontos usados: `516`;
- `n_basis`: `12`;
- `basis_width`: `0,035`;
- sampler: `NUTS`;
- draws/tune/chains: `2000 / 2000 / 4`;
- `target_accept` final: `0,99`;
- maior R-hat: `1,00292448`;
- menor ESS: `2269,80467052`;
- divergências: `0`;
- `predicted_depth` exploratório médio: `0,00721029`;
- `depth` robusto M1 para comparação: `0,00525258`.

O M2 é um modelo preditivo intermediário: descreve a curva suave e a incerteza
preditiva, mas a interpretação física mais estruturada fica para M3.

## Modelo Bayesiano M3

Modelo bayesiano trapezoidal aproximado para HAT-P-7 b:

```bash
.venv-nuts/bin/python scripts/run_bayesian_trapezoid_transit.py
```

Artefatos principais:

```text
notebooks/05_bayesian_trapezoid_transit_hat_p_7_b.ipynb
models/bayesian_trapezoid_transit/hat_p_7_b/runs/001_nuts/trace.nc
reports/bayesian_trapezoid_transit_hat_p_7_b_report.md
figures/bayesian_trapezoid_transit/hat_p_7_b/
tables/bayesian_trapezoid_transit/hat_p_7_b/
docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/
```

O M3 usa a mesma entrada, janela e normalização de M1/M2, mas modela o trânsito
por uma forma trapezoidal com profundidade, centro, duração total e
ingresso/egresso. Ele é mais interpretável que M2 e mais flexível que M1, mas
ainda não é modelo físico final.

Resumo da execução:

- pontos usados: `516`;
- sampler: `NUTS`;
- draws/tune/chains: `2000 / 2000 / 4`;
- `target_accept` final: `0,90`;
- maior R-hat: `1,00107423`;
- menor ESS: `4212,34208408`;
- divergências: `0`;
- profundidade posterior média: `0,00656620`;
- HDI 94% da profundidade: `[0,00594692, 0,00716767]`;
- `Rp/Rs` posterior médio: `0,08100761`;
- HDI 94% de `Rp/Rs`: `[0,07711627, 0,08466210]`;
- duração total posterior média: `0,17664741` dias, ou `4,23954` horas;
- duração média de ingresso: `0,03697592` dias, ou `0,88742` horas.

O M3 serve como modelo paramétrico aproximado e deve ser comparado com M1 e M2
em uma etapa M4. Ele não incorpora limb darkening, Mandel & Agol ou geometria
orbital completa.

## Modelo Bayesiano M4

Comparação entre M1, M2 e M3 para HAT-P-7 b:

```bash
.venv-nuts/bin/python scripts/run_model_comparison.py
```

Artefatos principais:

```text
notebooks/06_model_comparison_hat_p_7_b.ipynb
models/model_comparison/hat_p_7_b/model_comparison_config.json
models/model_comparison/hat_p_7_b/model_comparison_summary.json
reports/model_comparison_hat_p_7_b_report.md
figures/model_comparison/hat_p_7_b/
tables/model_comparison/hat_p_7_b/
docs/modeling/model_comparison_hat_p_7_b/
```

O M4 não cria um novo modelo bayesiano. Ele compara os modelos já executados (M1, M2, M3)
usando parâmetros, diagnósticos, métricas preditivas simples, resíduos e uma recomendação metodológica.

## Experimentos Avançados (M5, Injeção de Ruído, Sensibilidade)

Acesse a documentação completa dos novos experimentos metodológicos avançados:
[docs/EXPERIMENTS_M5_NOISE.md](docs/EXPERIMENTS_M5_NOISE.md)

### Notas sobre a Execução dos Modelos
- **M1 (Caixa), M2 (Suave), M3 (Trapezoidal), M4 (Comparador):** Rodam nativamente no Windows/Mac.
- **M5 (Físico Mandel & Agol), Sensibilidade e Ruído:** Exigem a biblioteca `exoplanet` e compiladores C++. Portanto, execute-os exclusivamente via **Linux/WSL ou Google Colab**.

Resumo da comparação:

- M1 profundidade média: `0,00525258`;
- M2 `predicted_depth` exploratório médio: `0,00721029`;
- M3 profundidade média: `0,00656620`;
- M1 RMSE: `0,00358754`;
- M2 RMSE: `0,00317888`;
- M3 RMSE: `0,00317499`;
- todos os modelos tiveram `divergências = 0`;
- LOO/WAIC ficaram indisponíveis porque os traces atuais não contêm
  `log_likelihood`;
- recomendação: M3 como `primary_preliminary_result`.

M1 permanece como baseline de referência. M2 permanece como descrição
preditiva suave. M3 é o resultado principal preliminar, ainda sem ser
caracterização física final.

## Documentação Técnica

Índice geral:

```text
docs/README.md
```

Documentação por etapa:

```text
docs/raw/
docs/silver/
docs/gold/
docs/eda/
docs/modeling/
```

## Estrutura RAW

```text
data/raw/
├── nasa_exoplanet_archive/
│   ├── pscomppars/
│   ├── ps/
│   └── manifests/
├── mast/
│   ├── lightkurve/
│   ├── astroquery/
│   └── manifests/
├── exomast/
│   └── manifests/
├── etd_varastro/
│   ├── html_snapshots/
│   ├── extracted_metadata/
│   ├── downloaded_lightcurves/
│   └── manifests/
├── _manifests/
│   ├── raw_data_manifest.csv
│   └── raw_data_manifest.json
└── _logs/
    └── download_raw_data.log
```

Os CSV retornados pelo TAP, JSON retornados pelas APIs, HTML público e FITS do
MAST são gravados sem transformação analítica. Arquivos existentes não são
substituídos; a reexecução registra `skipped_existing` e, quando necessário,
cria sidecars versionados por hash. O manifesto global é uma visão acumulada
e atualizada atomicamente, com data UTC, origem, planeta, missão, produto,
caminho, status, tamanho e SHA256 de cada artefato local.

## Comportamento e limites

- O limite padrão do MAST é de três curvas por planeta e missão.
- A tabela completa de resultados da busca é preservada mesmo quando nenhum
  produto é baixado.
- Falhas são isoladas por fonte, planeta e missão; o pipeline continua e
  registra o erro no manifesto e no log.
- O ETD/VarAstro não oferece nesta implementação um contrato de API estável.
  O coletor usa os endpoints anônimos consumidos pela própria página pública.
  Os JSON de curva são respostas da API de visualização e não devem ser
  confundidos com o arquivo originalmente enviado pelo observador.
- O conteúdo remoto pode mudar e os serviços podem impor indisponibilidade,
  rate limit ou resolver nomes de forma diferente.

## Próxima etapa

A próxima etapa recomendada é um modelo físico ou semi-físico de trânsito,
preservando M1, M2, M3 e M4 como trilha comparativa. Esse próximo modelo deve
considerar limb darkening, uma formulação Mandel & Agol ou `batman`, e salvar
`log_likelihood` no `InferenceData` para permitir LOO/WAIC.
