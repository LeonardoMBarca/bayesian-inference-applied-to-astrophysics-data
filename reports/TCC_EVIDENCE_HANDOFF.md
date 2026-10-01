# Fechamento delimitado para reconstrução do TCC

Referência canônica: `publication/TCC_EVIDENCE_INDEX.json`. Use
`reports/publication_synthesis/tcc_evidence_v3/REPORT.md`, `MANUSCRIPT_DRAFT.md`,
`METHODOLOGY.md`, `LIMITATIONS.md`, `claims.json` e `SOURCE_INVENTORY.json`.
O inventário lista as fontes exatas de tabelas, figuras, captions e auditorias.
O Word não foi gerado e nenhuma inferência final nova é necessária/executada.

## Achados resolvidos

- Contadores distinguem sampler/PPC/conjunto, proveniência, não avaliação,
  invalidação por incidente, jobs, tentativas e falhas técnicas. Taxas têm
  denominadores explícitos. O alias antigo mantém seu significado histórico.
- Correções saem em nova síntese versionada, sem editar resultados ou relatos
  selados. `gate_counts.csv` e `independent_gate_check.json` são gerados.
- VS Code favorece status/integridade/logs da v4 e pós-processamento sem
  inferência, com o ambiente Linux/WSL configurado. Não há launch genérico antigo.
- Registry/plan/runbook distinguem snapshots históricos do controlador atual.
- Complementos têm revisão direta dos traces, inventário transitive e pacote
  local novo. O incidente v3 e seus outputs inválidos são preservados para
  auditoria, não promovidos a validade científica.

## Já resolvidos antes desta rodada

O armazenamento de todas as variáveis livres corrigiu o PPC v4; protocolos,
seeds e 24 resultados v4 foram congelados/executados anteriormente. O baseline
scientific_003, transporte Git dos RAW, auditoria independente dos 480 traces,
equivalência de densidade/Jacobiano/gradiente e reconstrução isolada Silver/Gold
já têm recibos anteriores. Não foram reexecutados como experimentos finais.

## Resultados e limitações preservadas

As coortes parent/confirmatória não são misturadas aos pares v4, aos controles
observacionais, à v3 interrompida ou a pilotos. Recuperação útil de raio sob
regimes delimitados coexiste com cobertura conservadora, subcobertura geométrica
em regimes fracos e influência da prior. Aprovação de sampler não é adequação
preditiva nem identificabilidade. Os três refits locais do benchmark usam um
input e a MESMA posterior juliet histórica; aproximação computacional não é
validação da verdade astrofísica e o PPC temporal segue rejeitado.

O pequeno complemento não demonstra superioridade geral da padronização.
Contrastes com um posterior reprovado no sampler continuam descritivos.
Os cinco alvos continuam visíveis, com inadequação preditiva, sem substituição
favorável. M5 continua likelihood de jitter branco independente; M6/GP não
foi executado, nem ruído correlacionado resolvido. Não há novidade absoluta,
calibração universal, garantia de nota máxima ou de aceitação editorial.

## Preservação e armazenamento

Originals: `scientific_003`, resultados/traces/truth/seeds/protocolos/ledgers,
completion manifests, snapshots e tcc_evidence_v1/v2 mantêm bytes históricos.
`publication/validation/tcc_closure_v1/protected_snapshot.json` congela o
escopo; `--check-protected` verifica todos os arquivos, sem nova amostragem.
Compactos v3 ficam no Git; traces e logs complementares estão vinculados
ao novo bundle externo, não enviados ao Git comum.

Bundle local: `../publication-evidence-tcc-closure-v1/evidence.zip`.
Manifest/inventário/recibo: `publication/validation/tcc_closure_v1/`.
O checkout separado de teste permanece no mesmo diretório externo como
`restored-checkout`. O recibo verifica bytes e dependências da síntese atual;
não afirma reprodução independente de MCMC nem disponibilidade pública.

## Validação e reprodução

```sh
python scripts/close_tcc_evidence.py --check
python scripts/close_tcc_evidence.py --verify-original
python scripts/close_tcc_evidence.py --check-protected
python scripts/close_tcc_evidence.py --build --output reports/publication_synthesis/<NEW_VERSION>
python scripts/validate_publication_release.py
```

Recibo de lint, validação estática, suíte existente com smoke permitido e
contratos RAW/Silver/Gold: `publication/validation/tcc_closure_v1/code_validation_final/`.
Exit1 de release só é aceitável se `blocked_public_release` tiver integridade
aprovada e pré-requisitos explicitamente nomeados; exit2 é erro, não rejeição
científica normal. CI observado de f105317: workflow 36856904566, ambos jobs
green; o último SHA enviado será conferido na resposta final com link direto.
No push, clean rebuild condicional é skipped; no ambiente compatible-latest
a exigência de Python exato também é skipped. Não chamamos isso de executado.

## Pendências reais

A: fontes limitadas e auditáveis para revisão do TCC. B: restauração LOCAL,
auditada em recibo separado. C: revisão pública de direitos/privacidade,
armazenamento durável e DOI não autorizados/concluídos. D: manuscript draft
exige revisão humana/editorial e adequação ao periódico. Essas pendências
não impedem reconstruir o TCC; impedem anunciar release pública/submissão
pronta ou claims científicos mais fortes que a evidência.

Arquivos alterados nesta rodada: contadores/agregador, autorização de claims,
pós-processamento novo, schemas de verificação/arquivo, tarefas, documentos
vivos, registry e novas evidências/recibos derivados. Veja o diff dos commits
coerentes da branch publication-grade-validation. Sem merge em main/backup.
