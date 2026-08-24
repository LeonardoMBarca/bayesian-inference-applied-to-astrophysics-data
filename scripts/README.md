# Scripts e comandos

Esta pasta contém somente pontos de entrada estáveis para execução direta. A
lógica reutilizável, científica e de validação fica em pacotes temáticos sob
`src/`. Assim, comandos históricos e notebooks continuam funcionando sem
manter implementações extensas soltas junto dos executáveis.

## Pipeline de dados

- RAW: `download_raw_data.py` e os coletores específicos;
- Silver: `build_silver_data.py` e os executores por tipo de produto;
- Gold: `build_gold_data.py` e `build_gold_selection_report.py`.

As configurações canônicas ficam em `src/raw_ingestion/config.py`,
`src/silver_processing/config.py` e `src/gold_processing/config.py`. Os antigos
`*_data_config.py` permanecem como imports de compatibilidade.

## Modelagem e experimentos

- M5 atual: `run_bayesian_physical_transit.py` e `run_kepler_10b.py`;
- sensibilidade, ruído e comparação: os scripts `run_bayesian_*` correspondentes;
- M1–M3 históricos: entry points compatíveis que delegam para
  `src/bayesian_modeling/legacy/`.

## Validação do repositório

- ambiente: `verify_scientific_environment.py`;
- lint/estrutura: Ruff e `static_validate.py`;
- testes: `run_ci_tests.py`;
- contratos de artefatos: `validate_hardened_artifacts.py`;
- reprodução isolada: `validate_clean_rebuild.py`;
- inventário de runs: `build_model_run_inventory.py`.

As implementações desses utilitários ficam em `src/repository_tools/`. Os
caminhos de comando em `scripts/` são preservados como interface pública.
