# Entrega da revisão pós-campanha

Esta etapa revisa as campanhas concluídas na branch
`publication-grade-validation`. Não reconstrói o DOCX do TCC, não altera
`scientific_003`, não reclassifica gates históricos e não inicia nova inferência.

## Fontes para a próxima versão do TCC

O ponto de entrada é
[`REPORT.md`](../../reports/publication_synthesis/tcc_evidence_v1/REPORT.md).
Os números são gerados a partir dos resultados selados, com as coortes inicial
e confirmatória separadas. Use junto:

- [`MANUSCRIPT_DRAFT.md`](../../reports/publication_synthesis/tcc_evidence_v1/MANUSCRIPT_DRAFT.md): fonte inicial para metodologia, resultados e discussão.
- [`summary.json`](../../reports/publication_synthesis/tcc_evidence_v1/summary.json) e [`claims.json`](../../reports/publication_synthesis/tcc_evidence_v1/claims.json): métricas e limites das afirmações.
- [`SOURCE_INVENTORY.json`](../../reports/publication_synthesis/tcc_evidence_v1/SOURCE_INVENTORY.json): lista exata das fontes, tabelas e figuras, incluindo hashes.
- [`calibration_metrics.csv`](../../reports/publication_synthesis/tcc_evidence_v1/calibration_metrics.csv): parâmetros, níveis, vieses, larguras e todos os denominadores.
- [`captions.json`](../../reports/publication_synthesis/tcc_evidence_v1/captions.json): legendas e limites das novas figuras.
- [`CALIBRATION_REVIEW.md`](CALIBRATION_REVIEW.md) e [`POST_CAMPAIGN_SCIENTIFIC_REVIEW.md`](POST_CAMPAIGN_SCIENTIFIC_REVIEW.md): revisão adversarial e investigação das falhas.
- [`BIBLIOGRAPHY.md`](BIBLIOGRAPHY.md) e [`NOVELTY_MATRIX.md`](NOVELTY_MATRIX.md): referências e posicionamento sem prioridade não demonstrada.

As figuras e tabelas dos experimentos anteriores permanecem vinculadas pelos
manifests das campanhas. Aprovação em um gate é uma decisão sob o contrato
congelado, não garantia atual de exatidão de todos os parâmetros. A síntese
expõe as falhas de recuperação mesmo entre runs aprovados.

## Reprodução da análise

No ambiente científico declarado, a partir da raiz do repositório:

```sh
python scripts/build_publication_synthesis.py
python scripts/build_publication_synthesis.py --check
```

A construção verifica as duas campanhas recursivamente, recalcula as métricas
de calibração dos resultados por replicate e gera apenas artefatos derivados
em `reports/publication_synthesis/tcc_evidence_v1/`. O segundo comando não
escreve artefatos. A validação inclui todos os arquivos vinculados, inclusive
traces; uma cópia incompleta deve falhar. Em WSL sobre `/mnt/c`, essa auditoria
pode ser demorada por latência de metadados. Não é MCMC.

A evidência local de testes, lint, baseline e integridade está em
[`publication/validation/post_campaign_audit_v2/validation.json`](../../publication/validation/post_campaign_audit_v2/validation.json).
Os stdout/stderr de cada comando ficam no mesmo diretório. Falhas de validação
não devem ser escondidas; uma nova execução do harness exige novo diretório.
A primeira tentativa (`post_campaign_audit_v1`) iniciou a checagem da síntese
antes de sua geração concluir; seus logs e a explicação da falha de ordenação
permanecem preservados. Ela não é a aprovação final.

```sh
python tests/manual/validate_post_campaign_synthesis.py --output publication/validation/novo_id
```

O harness espera que o gate legado de release ainda rejeite o pacote. Essa
rejeição esperada só demonstra que uma release incompleta não é aprovada, e
não substitui integração futura do gate com os manifests de campanhas.

## Próximas investigações e release

Os resultados restringem os claims: calibração universal, compatibilidade
externa positiva e generalização física multi-alvo não foram demonstradas.
As revisões listam questões prospectivas sobre inicialização de t0,
identificação/informação, baselines das ablations e adequação temporal. Qualquer
mudança de modelo/sampler exige novo protocolo, seeds previamente declarados,
novos IDs e preservação desta evidência. Não basta aumentar o número de seeds
do mesmo desenho para resolver viés ou falta de identificação.

M6 permanece adiado. A fase de publicação pública ainda exige arquivo externo
dos traces/intermediários, restauração em checkout limpo, revisão de
distribuição/privacidade/licenças e validação de release que consuma as duas
campanhas. [`FINAL_EVIDENCE_STORAGE.md`](FINAL_EVIDENCE_STORAGE.md) e
[`STORAGE_MANIFEST.json`](../../reports/publication_synthesis/tcc_evidence_v1/STORAGE_MANIFEST.json)
registram a situação local e o que falta arquivar. Nenhuma tag de paper, DOI,
publicação remota ou aprovação de release foi efetuada nesta revisão.
