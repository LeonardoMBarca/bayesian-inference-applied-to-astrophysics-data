# Fechamento da auditoria externa — evidência para TCC

Data: 2026-09-30. Branch: `publication-grade-validation`.
Snapshot avaliado externamente: `4022d16aded5d218d0921a72817ecd05da4df6f1`.
Este relatório descreve o estado auditável desta rodada. A nota do TCC e a
aceitação de um artigo dependem de avaliação externa. Os resultados negativos
continuam no conjunto de evidências.

## A. Disposição dos achados

| Achado | Disposição | Evidência/limite |
|---|---|---|
| A0: possível perda do histórico | protegido e rechecado | `protected_snapshot.json` sela 7.041 arquivos do snapshot original, inclusive `scientific_003`, protocolos, seeds, todas as tentativas e síntese v1. O check final retornou 7.041/7.041, zero erros. |
| A1: RAW convertido pelo Git | corrigido localmente; prova de CI final pendente | Auditoria de 445 arquivos: 198 blobs divergiam dos bytes originais (197 por LF/CRLF, um com EOL misto). `.gitattributes` impede a conversão. Dois checkouts Git reais, com `autocrlf=false` e `true`, passaram 445/445 após a correção. |
| A2: CI local tomado como remoto | aberto até workflow do SHA final | O workflow original `36750457921` passou 266 testes e falhou em checksum RAW. O commit intermediário `8bb69f5` revelou erro de ordenação de imports em Ruff, já corrigido no código novo. |
| A3: agregação conferida pelo próprio agregador | corrigido | Auditor independente leu os 480 traces P2, recalculou médias, SD amostral, quantis ETI50/80/94 e agregações separadas de 80 e 400. `trace_audit_v1` registra status `PASS`; falhas numéricas não foram removidas. |
| A4: gate interpretado como recuperação física | corrigido em camada v2; limitação científica permanece | Avaliador separa integridade, contrato histórico de input, sampler, PPC, escala, informação por parâmetro e permissões de afirmação. Não modifica gates históricos. |
| A5: alias de `t0` | mecanismo e equivalência testados; eficácia final pendente | Há uma cadeia histórica deslocada cerca de um período. O jitter do inicializador atua em dias no parâmetro direto. A coordenada padronizada conserva prior/likelihood, com Jacobiano e gradientes testados. O diagnóstico não reconstrói o warmup histórico. |
| A6: ablações com ajuste de referência divergente | limitação preservada; estudo prospectivo preparado | Efeitos numéricos históricos continuam descritivos; zero divergências não foi relaxado. O protocolo complementar declara nove ajustes novos e custo antes dos resultados finais. |
| A7: estrutura residual observacional | análise adicional concluída; causa permanece desconhecida | Cinco alvos, quinze segmentos, tempo real, gaps, pontos dentro/fora do trânsito, tendências e checks de input observados; não há atribuição automática a GP. |
| A8: arquivo sem dependências transitivas | restauração independente passou; depósito público pendente | Grafo tipado de 8.201 registros, 1.562 membros externos; o ZIP local tem 496.436.552 bytes e SHA-256 `7396ed1269eb5e996ee4a79488629209e5c3cdda81f345ccd2577629eaade8b3`. Um clone separado restaurou os 1.562 membros e verificou todos os 8.201 checksums. |
| A9: release validadora lê zero runs/aceita qualquer exit 1 | implementação corrigida; recibo final pendente | Validador atual reconcilia 517 jobs e 518 tentativas. Exit 1 só significa pré-requisito público nomeado com integridade aprovada; exit 2 indica evidência inválida/erro. |
| A10: fontes incompletas para novo TCC | síntese v2 em geração | Métodos, priors por família, dados por parâmetro/regime, ledger de claims, figuras/captions, limitações e manuscrito serão gerados em novo diretório. A versão v1 permanece preservada. |

O plano detalhado com classificação, correção, teste, custo e critério de
conclusão está em `.agents/EXTERNAL_AUDIT_CLOSURE_PLAN.md`.

## B. Alterações de código e justificativa

- `.gitattributes`, `src/repository_tools/raw_byte_audit.py` e seu CLI/testes:
  identidade byte a byte entre manifesto, índice Git e checkout.
- `src/publication/trace_audit.py` e CLI/testes: conferência independente das
  estatísticas individuais e de cobertura, preservando denominadores.
- `src/publication/claim_authorization.py`, `synthesis_v2.py` e testes:
  avaliação posterior por escopo e ligação de afirmações aos arquivos.
- `src/bayesian_modeling/physical_transit.py` e `src/publication/inference.py`:
  parametrização `t0_standardized` opt-in; o default histórico permanece.
- `src/publication/residual_review.py` e `t0_mechanism_audit.py`: verificações
  observacionais/numéricas novas, com hashes do input e do gerador.
- `src/publication/evidence_archive.py`, `campaign_release.py`, CLI/testes:
  travessia transitiva, pacote local/restauração e classificação de release.
- `src/publication/numerical_campaign.py` e protocolos/configuração próprios:
  estudo final complementar preparado para o runner existente, sem execução
  automática durante este fechamento.

## C. Preservação

O snapshot protegido relaciona 7.041 caminhos e SHA-256 no commit original.
Inclui `scientific_003`, duas campanhas (117 e 400 jobs), 518 tentativas
preservadas, seus protocolos/ledgers/truth/traces/completion manifests,
resumos e `tcc_evidence_v1`. A única tentativa cancelada do primeiro lote
permanece como tentativa; não é uma realização com posterior. Nenhum resultado
histórico recebeu novo valor, gate ou seed. O check final confirmou todos os
7.041 arquivos, sem erro.

## D. Integridade de bytes e armazenamento

A divergência RAW originou-se da conversão de fim de linha do Git. Nos 445
arquivos inventariados, 247 blobs já eram exatos, 197 tinham LF em Git contra
CRLF histórico e um tinha EOL misto. A cópia local correspondia ao manifesto
em todos os 445 (23 caminhos Windows longos pareciam ausentes apenas ao acesso
sem prefixo de caminho estendido). A restauração do índice usou somente bytes
que já tinham hash e tamanho históricos; campos SHA dos manifests não foram
recalculados para acomodar corrupção. O CSV `raw_data_current_state.csv`
também foi versionado com os seus bytes CRLF locais originais; seus campos
permaneceram idênticos.

Um primeiro clone independente com `autocrlf=true` expôs mais 18 conversões
de tabelas/metadados de Gold e `scientific_003` (todos LF→CRLF). A política
de bytes desses domínios foi ajustada. Um novo clone no commit `180db76c6`
verificou 6.631 arquivos Git do inventário: 6.630 eram byte a byte idênticos
no checkout; a única diferença foi um adendo posterior ao snapshot em
`docs/publication/FINAL_EVIDENCE_STORAGE.md`, classificado explicitamente como
revisão de fonte e resolvido pelo blob Git do commit original, não por um
arquivo científico alterado. O recibo `clean_checkout_restore.json` registra
`status=passed`, 8.201/8.201 dependências verificadas, 1.562 arquivos externos
restaurados, zero previamente existentes e nenhum MCMC executado. A prova
anterior de 445/445 refere-se especificamente ao RAW.

O ZIP de evidência externa permanece **apenas local**, em
`../publication-audit-local-20260930/evidence_v1.zip`. O manifesto
`local_bundle_manifest_final.json` vincula exatamente seus 1.562 membros ao
inventário final, que também inclui intermediários Silver/Gold e logs de todas
as tentativas. Restauração exata de bytes não equivale a reexecução numérica.
Sem cópia externa durável e direitos revisados, P7 não está completo.

## E. Ciência e afirmações autorizadas

As coortes P2 são separadas: 80 jobs/81 tentativas no primeiro lote, 400/400
no confirmatório. No primeiro, 80 outputs numéricos, 66 aprovados no sampler
e 65 no gate conjunto; no segundo, 400, 339 e 337. Não se usa 517 como
denominador de calibração. O auditor independente encontra zero discrepâncias
de média, SD, ETI e agregação dentro de suas tolerâncias registradas.

O achado principal de limite é `near_limit_long`: no confirmatório, 94% ETI
de `a/Rs` cobriu a verdade em 9/100 (Wilson95 0,048–0,162); a duração teve
cobertura baixa também. O fato de muitos runs passarem gates históricos não
autoriza afirmar recuperação de geometria. Resultados condicionados ao gate
devem vir com seu denominador específico. Intervalos são de **caudas iguais**,
não HDIs; são frequências sob verdade fixa, não SBC. Resultados rejeitados com
posterior numérico permanecem na tabela, qualificados pela falha do sampler.

O benchmark juliet/PyMC usou as mesmas observações, porém o ajuste local
histórico teve R-hat 1,5287 e ESS mínimo 7,15; ambos os motores falharam no
screen temporal. Logo a comparação posterior é descritiva, e o prior Uniform
do benchmark não valida retroativamente o `scientific_003` de prior distinto.
As ablações demonstram casos sampler aprovado/PPC reprovado; pares com sampler
ruim não são efeitos físicos precisos. Os cinco alvos foram preservados, mas
todos falharam no screen temporal: não há validação física positiva de cinco
planetas nem generalização populacional. M6 não foi executado e ruído
correlacionado permanece hipótese/limitação.

## F. Inferência nova nesta rodada

Foram executados apenas **dois pilotos pequenos**, no novo namespace
`t0_coordinate_pilot_v1`, com 40 tune + 40 draws, duas chains e warmup salvo;
ambos terminaram `COMPLETED_REJECTED` sob diagnósticos insuficientes esperados
para esse tamanho. Duraram aproximadamente 312 s no processo completo. Não
são evidência final de eficácia e não foram selecionados por resultado.

O estudo `tcc_numerical_complement_v1` declara 24 **jobs finais ainda não
executados**: 12 P2 (dois regimes × três novos datasets pareados × direto/
padronizado), três ajustes locais P3 no mesmo input observacional e nove P4
de ablação numérica. O posterior externo histórico é reutilizado como uma
única referência, nunca contado como três réplicas externas. Os protocolos
fixam seeds/política, cenário, configuração, gates, inclusão de rejeitados e
orçamento de 20 h. O ledger de 24 jobs foi congelado no commit
`180db76c6ef13ae2e7471220e7b102655efe5079`, antes de qualquer batch final.
A estimativa de planejamento derivada de 44 tempos de
tentativas históricas é cerca de 5,4 h para os jobs, com grande incerteza de
geometria e compilação; não é ETA. Nenhum dos 517 jobs antigos foi repetido.

## G. CI remoto

O estado do CI do commit final deve ser preenchido a partir do workflow real
após push: SHA, workflow ID, jobs Python exato/compatível e conclusão de cada
etapa. O workflow não omite lint, testes nem validação RAW/Silver/Gold.
Python/dependências diretas iguais ao baseline são verificados no job exato;
isso não prova igualdade byte a byte de bibliotecas nativas no runner Ubuntu.

## H. Release

O gate de release separa integridade do pacote, sinal científico e prontidão
para distribuição pública. Um resultado negativo pode ser íntegro. Mesmo com
evidência íntegra, revisão de direitos de redistribuição, segurança, citação,
depósito externo/DOI, ambiente exato e clean room numérico requerem recibos
reais. Nenhum upload público, tag ou DOI foi criado nesta rodada.

## I. Fontes exatas para reconstrução do TCC e paper

Diretório novo: `reports/publication_synthesis/tcc_evidence_v2/`.
Arquivos centrais: `REPORT.md`, `METHODOLOGY.md`, `priors_by_family.json`,
`calibration_metrics.csv`, `claims.json`, `run_evaluations.json`, `summary.json`,
`coverage_trace_verified.png`, `historical_t0_chains.png`, `captions.json`,
`LIMITATIONS.md`, `MANUSCRIPT_DRAFT.md`, `SOURCE_INVENTORY.json` e
`artifact_manifest.json`. Fontes de apoio verificadas:
`publication/validation/trace_audit_v1/`,
`publication/validation/residual_review_v2/`,
`publication/validation/t0_mechanism_v3/`,
`publication/validation/external_audit_closure_v1/transitive_inventory_final.json`,
`docs/publication/BIBLIOGRAPHY.md` e `docs/publication/NOVELTY_MATRIX.json`.
Números para o texto devem ser importados desses artefatos; não transcrever
manualmente a mesma estimativa em vários lugares.

## J. Comandos

Executar da raiz do repo, no Python científico do WSL indicado no runbook:

```text
python scripts/freeze_audit_protection.py --check
python scripts/audit_raw_git_bytes.py --real-checkouts --output <NOVO_RECIBO.json>
python scripts/audit_publication_traces.py --check --output publication/validation/trace_audit_v1
python scripts/publication_evidence_archive.py verify --inventory publication/validation/external_audit_closure_v1/transitive_inventory_final.json
python scripts/build_publication_synthesis_v2.py --check
python scripts/validate_publication_release.py --audit-output <NOVO_RECIBO.json>
python scripts/run_ci_tests.py
python -m ruff check .
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --dry-run
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --status
```

Depois de conferir ledger committed e orçamento, o operador pode executar
`python scripts/run_publication_campaign.py --config
configs/publication/tcc_numerical_complement_v1.json --resume`, retomar pelo
mesmo comando, e acompanhar logs em
`logs/publication_campaign/tcc_numerical_complement_v1/`.
O passo final prospectivo continua pendente até seus próprios resultados e
relatórios existirem; código pronto não é experimento concluído.
