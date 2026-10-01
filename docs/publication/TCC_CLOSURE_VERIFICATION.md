# Fechamento do TCC — verificação final da entrega

Esta atualização complementa `reports/TCC_EVIDENCE_HANDOFF.md`, cujo snapshot
foi incluído no inventário selado. Não substitui nem reescreve esse arquivo.
Índice único das fontes científicas atuais: `publication/TCC_EVIDENCE_INDEX.json`.
Síntese para reconstrução do Word: `reports/publication_synthesis/tcc_evidence_v3/`.
O Word não foi gerado; nenhuma inferência final nova foi executada.

## O que foi fechado

Contadores corrigidos na origem distinguem sampler, PPC, conjunto, proveniência,
não avaliação, invalidação, jobs/tentativas e falhas técnicas. O alias antigo
mantém a semântica histórica. As contagens da v4 foram conferidas lendo cada
resultado original independentemente do agregador: veja o REPORT e
`independent_gate_check.json` da síntese atual. Regressões e novos derivados
não alteraram os resultados, gates, priors, seeds, protocols ou ledgers originais.

Tarefas do VS Code favorecem consulta/integridade/logs v4 e pós-processamento,
não retomada automática de v1/v2/v3. Registry e documentos vivos distinguem
snapshot histórico, campanha concluída e aprovação científica. O incidente v3,
todos os seus resultados existentes e os PPC invalidados foram preservados.
Os compactos estão no Git; arquivos grandes não foram enviados ao Git comum.

## Preservação e restauração

Recibos: `publication/validation/tcc_closure_v1/`.
`restore_receipt.json` registra restauração aprovada e hashes/tamanhos/contagens
conferidos. `restored_synthesis_verification.json` verifica claims e declarações/
tentativas usando o código do checkout separado, sem nova inferência.
`protected_verification_final.json` registra a checagem final dos originais.

Bundle local: `../publication-evidence-tcc-closure-v1/evidence.zip`.
Identidade e membros: `bundle_manifest.json`; dependências:
`transitive_inventory.json`. Checkout de teste: `restored-checkout` no mesmo
diretório externo. O ZIP anterior não foi substituído. Preserve uma cópia fora
deste PC: restauração local não equivale a backup durável ou depósito público.
O inventário conserva o snapshot `cd52a6b`; versões posteriores de documentos
vivos em docs/.agents são resolvidas por blobs Git históricos explícitos.

## Testes, CI e comandos

Suíte local completa: `code_validation_final/receipt.json` e logs preservados.
Três regressões adicionais do CLI Windows, lint e static: `archive_cli_validation.json`.
CI do código `25f0030`: workflow **36907836986**, ambos ambientes aprovados;
recibo `archive_cli_commit_remote_ci.json`. `remote_ci_review_v2.json` vincula
os arquivos atuais ao SHA aprovado. No push, clean rebuild foi skipped; no
ambiente compatible-latest a exigência de Python exato também foi skipped.
A CI do SHA final de empacotamento é conferida com link na resposta de entrega.

```sh
python scripts/close_tcc_evidence.py --check
python scripts/close_tcc_evidence.py --check-protected
python scripts/close_tcc_evidence.py --verify-original
python scripts/validate_publication_release.py
```

Para regenerar derivados, use `--build --output reports/publication_synthesis/<NEW_VERSION>`
no primeiro script. O destino deve ser novo, sem sobrescrever versões seladas.
Comando completo de restauração está em `EVIDENCE_ARCHIVE_RUNBOOK.md`.

## Limites e pendências

`release_audit_final_v2.json` separa integridade do TCC, CI e requisitos públicos.
Exit 1 só representa bloqueio público com integridade aprovada e pendências
nomeadas; exit 2 continua erro. Recibos anteriores ficam históricos, inclusive
o erro operacional de fornecer caminho absoluto a um argumento lógico do
validador de release; isso não invalida a restauração científica. A edição
temporária do handoff também foi detectada em `release_audit_final.json` e
revertida, preservando os bytes vinculados ao inventário. A atualização está
neste documento separado; nenhum check foi removido ou hash científico trocado.
Python/pins diretos foram verificados nos testes e na CI. O requisito público
de ambiente/clean-room refere-se ao recibo formal da release, não à ausência
de testes: restauração de bytes não é reprodução integral de inferência.

Resultados mistos permanecem: cobertura condicional, influência da prior,
geometria fraca, inadequação preditiva dos alvos/benchmark e contrastes de
ablação apenas descritivos quando sampler falha. Proximidade computacional
não é verdade astrofísica; o complemento não prova superioridade geral.
M5 é white-jitter-only, M6 não foi executado. Não há calibração universal,
seleção favorável de seeds/alvos ou garantia editorial/nota.

As fontes estão destinadas à redação/revisão do TCC. Publicação durável/DOI,
direitos/privacidade e revisão humana/editorial do manuscript permanecem
separados. A segunda passagem crítica está em `reports/TCC_CLOSURE_REVIEW.md`.
Somente a branch publication-grade-validation recebeu commits; sem merge
em main/backup e sem novos batches científicos.
