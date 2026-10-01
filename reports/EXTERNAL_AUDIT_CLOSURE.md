# Fechamento da auditoria externa — evidência para TCC

Data: 2026-09-30. Branch: `publication-grade-validation`.
Snapshot avaliado externamente: `4022d16aded5d218d0921a72817ecd05da4df6f1`.
Este relatório descreve o estado auditável desta rodada. A nota do TCC e a
aceitação de um artigo dependem de avaliação externa. Os resultados negativos
continuam no conjunto de evidências.

## A. Disposição dos achados

| Achado | Disposição | Evidência/limite |
|---|---|---|
| A0: possível perda do histórico | protegido e rechecado | `protected_snapshot.json` sela 7.041 arquivos do snapshot original, inclusive `scientific_003`, protocolos, seeds, todas as tentativas e síntese v1. No clone independente restaurado, o check completo retornou 7.041/7.041, zero erros. O check portátil confere 6.520 arquivos Git e vincula 521 arquivos externos ao bundle; não afirma verificar seus bytes no CI. |
| A1: RAW convertido pelo Git | corrigido e confirmado em CI no ledger v3; SHA de fechamento ainda requer conferência | Auditoria de 445 arquivos: 198 blobs divergiam dos bytes originais (197 por LF/CRLF, um com EOL misto). `.gitattributes` impede a conversão. Dois checkouts Git reais, com `autocrlf=false` e `true`, passaram 445/445 após a correção; o workflow remoto `36797666471` também passou o contrato RAW nos dois jobs. |
| A2: CI local tomado como remoto | workflow remoto verde no ledger v3; SHA de fechamento ainda requer conferência | O workflow original `36750457921` passou 266 testes e falhou em checksum RAW. Falhas intermediárias de Ruff foram corrigidas. O workflow remoto `36797666471`, SHA `8febce31eeb5825517e85487a55838414bc3c5e2`, passou nos jobs científico exato e compatível com o ledger v3 congelado. Nenhum sucesso de CI é inferido apenas de teste local. |
| A3: agregação conferida pelo próprio agregador | corrigido | Auditor independente leu os 480 traces P2, recalculou médias, SD amostral, quantis ETI50/80/94 e agregações separadas de 80 e 400. `trace_audit_v1` registra status `PASS`; falhas numéricas não foram removidas. |
| A4: gate interpretado como recuperação física | corrigido em camada v2; limitação científica permanece | Avaliador separa integridade, contrato histórico de input, sampler, PPC, escala, informação por parâmetro e permissões de afirmação. Não modifica gates históricos. |
| A5: alias de `t0` | mecanismo e equivalência testados; eficácia final pendente | Há uma cadeia histórica deslocada cerca de um período. O jitter do inicializador atua em dias no parâmetro direto. A coordenada padronizada conserva prior/likelihood, com Jacobiano e gradientes testados. O diagnóstico não reconstrói o warmup histórico. |
| A6: ablações com ajuste de referência divergente | limitação preservada; estudo prospectivo em execução | Efeitos numéricos históricos continuam descritivos; zero divergências não foi relaxado. O protocolo complementar declara nove ajustes novos e custo antes dos resultados finais. Ainda não há efeito prospectivo agregado. |
| A7: estrutura residual observacional | análise adicional concluída; causa permanece desconhecida | Cinco alvos, quinze segmentos, tempo real, gaps, pontos dentro/fora do trânsito, tendências e checks de input observados; não há atribuição automática a GP. |
| A8: arquivo sem dependências transitivas | restauração independente passou; depósito público pendente | Grafo tipado de 8.201 registros, 1.562 membros externos; o ZIP local tem 496.436.552 bytes e SHA-256 `7396ed1269eb5e996ee4a79488629209e5c3cdda81f345ccd2577629eaade8b3`. Um clone separado restaurou os 1.562 membros e verificou todos os 8.201 checksums. |
| A9: release validadora lê zero runs/aceita qualquer exit 1 | corrigido e executado | `release_audit_v2.json` reconciliou 517 jobs/518 tentativas, passou integridade/claims e classificou `exit 1` apenas como `blocked_public_release` com sete pré-requisitos públicos nomeados; zero erros de integridade. Exit 2 continua reservado para evidência inválida/erro. |
| A10: fontes incompletas para novo TCC | síntese v2 gerada e verificada | Novo diretório com métodos, priors por família, 504 linhas de calibração por coorte/regime/parâmetro/população/nível, 517 avaliações, cinco claims versionados, figuras/captions, limitações e manuscrito. Os 13 arquivos do manifesto conferem byte a byte após cópia; a versão v1 permanece preservada. |

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
  estudo final complementar preparado e depois lançado pelo runner autônomo;
  seus resultados ainda não integram esta síntese histórica.

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

Antes do batch complementar, foram executados **dois pilotos pequenos**, no namespace
`t0_coordinate_pilot_v1`, com 40 tune + 40 draws, duas chains e warmup salvo;
ambos terminaram `COMPLETED_REJECTED` sob diagnósticos insuficientes esperados
para esse tamanho. Duraram aproximadamente 312 s no processo completo. Não
são evidência final de eficácia e não foram selecionados por resultado.

Os estudos `tcc_numerical_complement_v1` e `v2` declararam 24 jobs cada, mas
**nenhum run final foi executado** em nenhum deles. Um ajuste pós-freeze do
verificador de proteção alterou a identidade ampla de source e o runner
bloqueou v1. O ledger `180db76` permanece intocado. O v2 repetiu o desenho
sob novo ID, mas seu primeiro lançamento terminou **antes** da criação de
`campaign_state.json`: um `KeyError` técnico revelou que o preflight de PUB-03
exigia ambiente externo mesmo sem novos jobs externos. O recibo
`numerical_v2_preflight_failure.json` preserva a falha e confirma zero jobs.
Corrigi o preflight para vincular o manifesto externo histórico e o input por
hash sem exigir interpretador externo não utilizado; acrescentei teste de
regressão. O v2 permanece congelado e inalterado.

O namespace prospectivo `tcc_numerical_complement_v3` mantém os mesmos
cenários, priors, draws, contrastes e tamanho; só ID, caminhos de protocolo,
timestamp e seeds derivadas do novo ID diferem. Protocolos v3 foram
versionados em `0a869b1` e o ledger de 24 jobs em `8febce3`, ambos antes de
qualquer resultado. O pré-exame v3 passou com zero erros; hashes do input P3 e
do manifesto externo histórico conferem. Os jobs v3 são: 12 P2 (dois regimes × três novos datasets pareados × direto/
padronizado), três ajustes locais P3 no mesmo input observacional e nove P4
de ablação numérica. O posterior externo histórico é reutilizado como uma
única referência, nunca contado como três réplicas externas. Os protocolos
fixam seeds/política, cenário, configuração, gates, inclusão de rejeitados e
orçamento de 20 h. A identidade v3 está congelada antes de qualquer batch final.
A estimativa de planejamento derivada de 44 tempos de
tentativas históricas é cerca de 5,4 h para os jobs, com grande incerteza de
geometria e compilação; não é ETA. Nenhum dos 517 jobs antigos foi repetido.
Depois de 353 testes locais sem skips e CI remoto verde no ledger v3, o
supervisor iniciou a campanha v3 em `2026-10-01T00:49:00Z`. O primeiro
checkpoint registrou `RUNNING` no primeiro job P2; o recibo está em
`numerical_v3_launch.json`. Isso **não** é resultado final. Progresso,
rejeições e falhas posteriores devem ser lidos do estado vivo e dos artefatos
selados, nunca inferidos desta fotografia de lançamento. A sessão do agente
não é necessária para iniciar o job seguinte.

## G. CI remoto

Consulta autenticada à API do GitHub Actions confirmou o workflow
[`36797666471`](https://github.com/LeonardoMBarca/bayesian-inference-applied-to-astrophysics-data/actions/runs/36797666471)
no SHA `8febce31eeb5825517e85487a55838414bc3c5e2`: conclusão `success`.
Ambos os jobs — `validation (scientific-exact-python)` e
`validation (compatible-latest-patch)` — concluíram `success`. Os dois passaram
instalação/imports, registro de ambiente/SHA, Ruff, contrato estático, testes
e validação dos contratos RAW/Silver/Gold. O check de pins exatos foi
bem-sucedido apenas no job exato; no compatível era intencionalmente `skipped`.
**A reconstrução isolada de Silver/Gold estava `skipped` nesse push porque o
workflow a reserva a `workflow_dispatch`; não a conto como prova remota dessa
execução.** A primeira versão da nova etapa de proteção falhou nos dois jobs
do workflow `36776440486`: tentou exigir, antes do restore, os 521 arquivos
grandes que por contrato ficam no bundle externo. Corrigi a semântica sem
alterar nenhum resultado: o CI agora confere 6.520 arquivos Git byte a byte
e vincula os 521 externos ao inventário selado; o check integral de 7.041
arquivos permanece obrigatório **depois** da restauração independente.
O clone também revelou seis arquivos históricos pequenos ausentes do Git,
versionados com seus hashes originais em `c774a4b`, e dois metadados de cache
históricos que não estavam nem no Git nem no inventário transitivo, também
versionados sem mudança de bytes. A suíte independente pós-transporte passou
oito checks em `local_validation_after_transport/`, incluindo testes, lint,
contratos, histórico integral, traces, síntese v2 e classificação do gate de
release. O exit 1 do último check é o bloqueio público estruturado esperado.
Além disso, `clean_rebuild_after_transport.json` documenta reconstrução local
isolada de Silver/Gold no clone separado, iniciada apenas com source e RAW:
status `passed`, nenhuma chamada de rede tentada pelo guard Python, Gold IDs
inalterados e hashes M5 preservados (`298fca34...` HAT-P-7 b,
`6653fced...` Kepler-10 b). Isso não é o passo remoto de push que foi
`skipped`, nem reexecução de MCMC.
Uma nova consulta é necessária para o SHA do commit de fechamento, após o
push. Python/dependências diretas iguais ao baseline são
verificados no job exato; isso não prova igualdade byte a byte de bibliotecas
nativas no runner Ubuntu.

## H. Release

O gate de release separa integridade do pacote, sinal científico e prontidão
para distribuição pública. Um resultado negativo pode ser íntegro. Mesmo com
evidência íntegra, revisão de direitos de redistribuição, segurança, citação,
depósito externo/DOI, ambiente exato e clean room numérico requerem recibos
reais. Nenhum upload público, tag ou DOI foi criado nesta rodada.
O recibo atual `release_audit_v2.json` registra `integrity_status=passed`,
`status=blocked_public_release`, `exit_code=1`, 517 jobs, 518 tentativas e
quatro checks centrais aprovados. Faltam recibos fonte-vinculados para
`citation`, `public_safety`, `third_party_redistribution`, `external_archive`,
`exact_scientific_environment`, `clean_room` e `remote_ci` da release final.
Os estados/comandos dos pilotos guardam caminhos absolutos do ambiente WSL;
isso é proveniência operacional, mas também exige revisão de segurança e
privacidade antes de tornar o pacote público. Não serão reescritos para
simular portabilidade ou apagar o histórico.

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
Esta síntese v2 é um snapshot fechado das 517 execuções históricas e dos
diagnósticos de auditoria. Os 24 jobs prospectivos v3, agora em execução, **não**
integram suas tabelas ou claims. Após o término, será necessária uma síntese
sucessora versionada, com todos os 24 resultados/ausências/rejeições e sem
reescrever os números da v2.

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
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v3.json --dry-run
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v3.json --status
```

O supervisor v3 já está ativo. **Não abra um segundo controller enquanto o
estado estiver RUNNING.** Após parada, o operador pode retomar com
`python scripts/run_publication_campaign.py --config
configs/publication/tcc_numerical_complement_v3.json --resume`, retomar pelo
mesmo comando, e acompanhar logs em
`logs/publication_campaign/tcc_numerical_complement_v3/`.
O passo final prospectivo continua pendente até seus próprios resultados e
relatórios existirem; código pronto não é experimento concluído.
