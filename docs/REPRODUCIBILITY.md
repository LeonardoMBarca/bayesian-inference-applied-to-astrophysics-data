# Reprodução e disponibilidade

[Projeto](../README.md) · [Guia do avaliador](REVIEWER_GUIDE.md)

## O que significa reproduzir neste repositório

| Nível | Operação | O que demonstra |
|---|---|---|
| Leitura | Examinar relatório, métricas e fontes no GitHub | Rastreabilidade documental |
| Verificação portátil | Conferir arquivos Git e referências externas seladas | Identidade dos bytes presentes e consistência das referências |
| Restauração completa | Obter o pacote externo e verificá-lo em outro checkout | Disponibilidade dos mesmos bytes naquele checkout |
| Nova inferência | Reexecutar código e protocolo científicos em novo destino | Nova realização computacional, a ser comparada e diagnosticada |

Um nível não substitui o seguinte. Um hash não comprova a hipótese física; um
recibo local não torna um ZIP publicamente disponível.

## Acesso aos materiais

- **Públicos no Git:** código, configurações, protocolos, inputs e resumos
  versionados, decisões, tabelas, figuras e recibos de validação.
- **Externos ao Git comum:** traces completos e parte dos intermediários grandes,
  identificados no [inventário](../publication/validation/tcc_closure_v1/transitive_inventory.json)
  e no [manifesto do pacote](../publication/validation/tcc_closure_v1/bundle_manifest.json).
  O arquivo permanece local ao autor; solicite acesso antes de planejar uma
  restauração completa. Não há endereço público de download nem DOI registrado.
- **Separados da distribuição científica:** documentos pessoais de matrícula,
  históricos e materiais de curso com identificação individual. Eles não são
  necessários para executar os modelos.

A abertura do repositório não equivale a aprovação de uma release arquivada ou
à revisão de todos os direitos de terceiros. A [política de armazenamento](STORAGE_POLICY.md)
e o [runbook de arquivo](publication/EVIDENCE_ARCHIVE_RUNBOOK.md) mantêm o detalhe.

## Verificação sem nova inferência

Obtenha um clone normal, preservando o histórico necessário às referências de
código congelado. Os caminhos longos de alguns produtos favorecem Linux/WSL;
em Windows, habilite `core.longpaths`.

```bash
git -c core.longpaths=true clone https://github.com/LeonardoMBarca/bayesian-inference-applied-to-astrophysics-data.git
cd bayesian-inference-applied-to-astrophysics-data

python scripts/freeze_audit_protection.py --check-portable \
  --output publication/validation/tcc_closure_v1/protected_snapshot.json \
  --inventory publication/validation/tcc_closure_v1/transitive_inventory.json
```

Essa operação verifica o histórico protegido presente no Git e os vínculos dos
objetos externos. Ela **não verifica os bytes do ZIP ausente**, não amostra
posteriors e não aprova automaticamente a validade científica dos resultados.
Leia o escopo e os contadores da saída JSON.

## Ambiente científico

Os arquivos [requirements.txt](../requirements.txt) e
[environment.yml](../environment.yml) registram o ambiente. A referência
científica utiliza **Python 3.14.6**, dependências diretas fixadas e toolchain
compilado em Linux/WSL. Um ambiente com versões diferentes não deve ser anunciado
como idêntico. Dependências transitivas e bibliotecas nativas também importam.

```bash
conda env create -f environment.yml
conda activate bayesian-astrophysics
python scripts/verify_scientific_environment.py
python -m ruff check .
python scripts/run_ci_tests.py
python scripts/validate_hardened_artifacts.py
```

A suíte inclui inferências pequenas de teste, **não as campanhas finais**.
O [workflow](../.github/workflows/ci.yml) distingue Python científico exato de
compatibilidade. A reconstrução completa de Silver/Gold é condicional ao
acionamento manual; um push verde não significa que essa etapa foi executada.

## Restauração e pós-processamento completo

Somente após obter o pacote externo identificado pelo índice canônico:

1. Verifique seu SHA-256 contra o manifesto, sem substituir os hashes esperados.
2. Siga o [runbook](publication/EVIDENCE_ARCHIVE_RUNBOOK.md) para restaurar em
   checkout separado. Nunca sobrescreva arquivos divergentes automaticamente.
3. Verifique a síntese e, quando necessário, gere derivados em um destino novo.

No ambiente científico instalado, a interface de módulo evita o caminho absoluto
do interpretador do computador do autor:

```bash
PYTHONPATH=src python -m publication.tcc_closure --check
PYTHONPATH=src python -m publication.tcc_closure --check-protected
# Apenas com todos os inputs externos disponíveis; o destino deve ser novo:
PYTHONPATH=src python -m publication.tcc_closure --build \
  --output reports/publication_synthesis/reproducao_local_001
```

O atalho `scripts/close_tcc_evidence.py` utiliza o interpretador e a distribuição
WSL da configuração histórica v4. Não pressuponha que esses caminhos existam em
outra máquina, nem altere um protocolo selado para acomodar seu computador.

O [índice](../publication/TCC_EVIDENCE_INDEX.json) aponta para o pacote atual.
O [recibo de restauração](../publication/validation/tcc_closure_v1/restore_receipt.json)
registra 9.158 arquivos verificados e 1.701 objetos externos restaurados **no
ambiente local documentado**, sem novas inferências.

## Novos experimentos e avaliação de release

Não reutilize IDs históricos como `scientific_003` nem retome campanhas finalizadas
para experimentar a ferramenta. Para um estudo novo, defina protocolo,
identificador, sementes e orçamento próprios; consulte o
[runbook de campanhas](publication/CAMPAIGN_RUNBOOK.md).

`python scripts/validate_publication_release.py` exige o conjunto completo de
evidências. Suas saídas distinguem `passed`, `blocked_public_release` e
`invalid_evidence`/`validator_error`. Ausência inesperada de arquivos não é um
resultado científico negativo. A visibilidade pública do GitHub não muda essas
classificações nem preenche automaticamente revisões de direitos, arquivo e DOI.
