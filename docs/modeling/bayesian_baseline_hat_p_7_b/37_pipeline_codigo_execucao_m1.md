# 37 - Pipeline, Código e Execução do M1

## 1. Script Operacional Original

Arquivo:

```text
scripts/run_bayesian_baseline.py
```

Função:

- preparar entrada de modelagem;
- construir o modelo PyMC;
- executar amostragem;
- gerar posterior predictive;
- salvar `trace.nc`;
- salvar tabelas;
- salvar figuras;
- salvar relatório;
- salvar roadmap de modelos.

Esse script permanece como registro da primeira implementação completa do M1.
Ele gerou a execução curta operacional, posteriormente versionada como:

```text
001_operational_metropolis
```

## 2. Script Robusto NUTS

Arquivo:

```text
scripts/run_bayesian_baseline_nuts_robust.py
```

Função:

- preservar a execução operacional em `runs/001_operational_metropolis`;
- preparar a mesma entrada de modelagem;
- construir o mesmo modelo PyMC;
- executar NUTS com `2000` draws, `2000` tune e `4` cadeias;
- gerar posterior predictive;
- salvar `trace.nc` versionado;
- salvar tabelas versionadas;
- salvar figuras versionadas;
- gerar relatório robusto;
- gerar comparação entre runs.

## 3. Notebook

Arquivo:

```text
notebooks/03_bayesian_baseline_hat_p_7_b.ipynb
```

O notebook carrega o script e chama:

```python
run_pipeline()
```

Assim, notebook e script usam a mesma lógica.

## 4. Comandos de Execução

Execução operacional original:

```bash
python scripts/run_bayesian_baseline.py
```

No ambiente validado:

```bash
.venv/bin/python scripts/run_bayesian_baseline.py
```

Execução robusta recomendada:

```bash
.venv-nuts/bin/python scripts/run_bayesian_baseline_nuts_robust.py
```

## 5. Dependências

Dependências principais:

```text
pandas
numpy
matplotlib
pymc
arviz
h5netcdf
h5py
```

Não foi usado `seaborn`.

## 6. Estrutura de Saída

```text
models/
  modeling_roadmap.md
  bayesian_baseline/
    hat_p_7_b/
      trace.nc
      model_config.json
      inference_data_summary.json

reports/
  bayesian_baseline_hat_p_7_b_report.md

figures/
  bayesian_baseline/
    hat_p_7_b/

tables/
  bayesian_baseline/
    hat_p_7_b/
```

Saídas versionadas da robusta:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
tables/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
figures/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

## 7. Ambiente da Execução Operacional Original

O ambiente operacional original não possuía `Python.h`. Isso impediu o backend
C do PyTensor naquela primeira execução.

Para permitir execução, o script configura:

```text
PYTENSOR_FLAGS=base_compiledir=/tmp/pytensor-cache,linker=py,cxx=
MPLCONFIGDIR=/tmp/matplotlib-cache
```

Consequência:

- NUTS 2000/2000 ficou impraticável;
- a execução validada usou `Metropolis`;
- a amostragem foi curta;
- os diagnósticos MCMC ficaram fracos.

## 8. Ambiente da Execução Robusta

A execução robusta usa um ambiente local separado:

```text
.venv-nuts/
```

Esse ambiente usa Python do Conda com `Python.h` disponível e backend C do
PyTensor operacional.

Configuração do PyTensor:

```text
PYTENSOR_FLAGS=base_compiledir=/tmp/pytensor-cache-nuts-robust
MPLCONFIGDIR=/tmp/matplotlib-cache
```

## 9. Configurações Registradas

Arquivo operacional original:

```text
models/bayesian_baseline/hat_p_7_b/model_config.json
```

Resumo:

```text
draws = 300
tune = 300
chains = 4
sampler = Metropolis
requested_draws = 2000
requested_tune = 2000
```

Arquivo robusto:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/model_config.json
```

Resumo robusto:

```text
draws = 2000
tune = 2000
chains = 4
sampler = NUTS
target_accept = 0,9
```

## 10. Política de Reexecução

O script reaproveita `trace.nc` se ele já existir, para evitar repetir a
amostragem quando apenas relatórios, figuras ou tabelas precisam ser
regenerados.

Para a execução robusta, a política adotada foi versionar os resultados em
subpastas `runs/`, preservando a execução operacional e criando a execução
NUTS recomendada sem apagar histórico.
