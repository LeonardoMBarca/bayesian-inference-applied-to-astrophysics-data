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
[`publication/validation/post_campaign_audit_v3/validation.json`](../../publication/validation/post_campaign_audit_v3/validation.json).
Os stdout/stderr de cada comando ficam no mesmo diretório. Falhas de validação
não devem ser escondidas; uma nova execução do harness exige novo diretório.
A execução v3 concluiu como `passed`: 266 testes, nenhum ignorado, lint,
validação estática, baseline histórico e integridade da síntese aprovados.
O verificador da síntese confirmou 517 jobs e 518 tentativas preservadas.
O retorno não zero do gate de release é esperado e não constitui aprovação
da release. Algumas linhas de falha no stdout da suíte pertencem ao teste
deliberado do recibo ausente; o resultado agregado da suíte está ao final
desse log. Consulte `validation.json` para os resultados dos comandos reais.
A primeira tentativa (`post_campaign_audit_v1`) iniciou a checagem da síntese
antes de sua geração concluir; seus logs e a explicação da falha de ordenação
permanecem preservados. Ela não é a aprovação final.
A segunda tentativa (`post_campaign_audit_v2`) passou 263 testes, lint e
baseline, mas foi encerrada como falha após detectar dependência da ordem das
chaves JSON na apresentação do relatório. O snapshot anterior e o recibo
`ORDERING_FAILURE.md` preservam essa ocorrência. As métricas científicas não
mudaram; a correção é protegida por testes de round-trip de textos e figuras.

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

## Escopo exato das verificações de armazenamento

Uma conferência independente em PowerShell nativo verificou os 6.932 arquivos
explicitamente enumerados em `source_checksums` dos dois resumos, sem importar
código do projeto: todos coincidiram. O recibo é
[`independent_native_source_hashes_v1.json`](../../publication/validation/independent_native_source_hashes_v1.json).
Essa conferência não substitui a checagem dos artefatos/manifests filhos feita
pelo validador da síntese, nem é uma auditoria transitiva de todo RAW/preparo.

Correção de escopo ao snapshot `FINAL_EVIDENCE_STORAGE.md`: os hashes das
tabelas Silver/Gold completas de PUB-05 constam nos `preparation_manifest.json`,
mas essas tabelas **não estão enumeradas** nos `source_checksums` globais nem
no `STORAGE_MANIFEST.json` desta síntese. O validador confere o manifest de
preparação como arquivo; não percorre automaticamente todo JSON de proveniência
para verificar seus descendentes. Portanto, não se deve interpretar a frase
do snapshot sobre os validadores vincularem esses intermediários como prova
de verificação transitiva de seus bytes. Os traces explicitamente enumerados
são verificados; restauração/auditoria integral do pipeline e inventário de
arquivo externo completo continuam requisitos separados de release.
