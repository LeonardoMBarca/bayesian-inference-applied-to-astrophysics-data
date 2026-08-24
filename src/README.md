# Organização do código-fonte

O código reutilizável está separado por responsabilidade:

- `raw_ingestion/`: coleta, proveniência e manifesto RAW;
- `silver_processing/`: transformação semântica e validação Silver;
- `gold_processing/`: seleção, normalização por segmento e produtos Gold;
- `gold_analysis/`: EDA dos produtos Gold;
- `bayesian_modeling/`: contratos, M5, experimentos e comparação;
- `bayesian_modeling/legacy/`: implementações históricas M1–M3;
- `repository_tools/`: CI local, inventários e validações de reprodutibilidade;
- módulos de topo: configuração autoritativa, caminhos portáveis e políticas de
  cadência/seleção compartilhadas entre camadas.

Os arquivos em `scripts/` devem permanecer finos: inicializam o caminho do
projeto, interpretam argumentos quando necessário e delegam para estes pacotes.
O teste `tests/test_repository_layout.py` protege essa fronteira e os imports de
compatibilidade usados por notebooks e automações existentes.
