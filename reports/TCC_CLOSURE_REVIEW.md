# Segunda passagem crítica — fechamento do TCC

Escopo: corrigir e auditar derivados de evidências existentes. Não é uma nova
validação prospectiva, uma reprodução independente de MCMC ou aprovação pública.
Índice atual: `publication/TCC_EVIDENCE_INDEX.json`; entrega inicial preservada:
`reports/TCC_EVIDENCE_HANDOFF.md`; verificação final:
`docs/publication/TCC_CLOSURE_VERIFICATION.md`.

## Conferências e decisões

- **Contadores e denominadores:** o recount independente da v4 lê os resultados
  individuais, sem chamar o contador corrigido. Está em
  `tcc_evidence_v3/independent_gate_check.json`; o CSV/JSON separa componentes,
  diagnósticos não avaliados, invalidados, tentativas e jobs declarados.
- **Falhas não escondidas:** a síntese conserva todas as coortes declaradas,
  todos os alvos, rejeições e a tentativa interrompida histórica. Resultados
  invalidados pelo incidente v3 não viraram falhas científicas observadas nem
  aprovação. Pilotos/fixtures não são evidência final.
- **Seleção e pseudorreplicação:** datasets pareados não são novas realizações
  independentes; refits locais não são novos benchmarks externos. Populações
  selecionadas por gates não estimam cobertura incondicional. Coortes não foram
  somadas como uma calibração única.
- **Leakage e circularidade:** este pós-processamento lê verdades apenas para
  avaliar resultados já congelados, não alimenta inferência. Priors e datasets
  não foram ajustados. Dependência de catálogo e proximidade ao benchmark não
  foram apresentadas como validação independente da verdade astrofísica.
- **Identificabilidade e calibração:** cobertura condicional a verdades fixas,
  influência de prior, geometria fraca, sobre/subcobertura e incerteza da própria
  frequência de cobertura continuam explícitas. Convergência não prova adequação.
- **Comparações:** PPC temporal negativo do benchmark foi preservado. Contrastes
  envolvendo sampler reprovado são descritivos, não efeitos físicos conclusivos.
  Não há superioridade geral da parametrização nem ranking LOO acrescentado.
- **Figuras:** denominadores e populações são declarados nas tabelas/captions;
  as barras da v4 representam componentes, não validade científica conjunta.
  As figuras de calibração conservam os bytes da auditoria anterior dos traces.
- **Ruído:** M5 continua white-jitter-only; estrutura temporal não identifica
  sozinha sua causa. GP/M6 não foi executado nem anunciado como solução.
- **Freshness e transporte:** manifests atuais vinculam geradores/fontes;
  originais mantêm hashes. O ZIP novo foi restaurado em checkout separado e
  a síntese foi validada ali. Documentos vivos posteriores ao snapshot do
  inventário têm suas versões antigas resolvidas por blobs Git explícitos.

## Evidência e limites de encerramento

Recibos em `publication/validation/tcc_closure_v1/`: proteção histórica,
revisão dos traces complementares, suíte local completa, regressões adicionais
do CLI, lint/static, CI do código, restauração e verificação da síntese restaurada.
O CI do SHA final de empacotamento deve ser confirmado na resposta de entrega;
etapas condicionais skipped não são apresentadas como executadas.

Não se corrigiram resultados negativos por novas seeds, novos priors, novos
targets, alteração de thresholds ou nova amostragem. Não foi gerado DOCX.
Integridade para revisar/redigir o TCC e restauração local não equivalem a
release pública, depósito durável/DOI, revisão de direitos/privacidade ou
manuscrito pronto para submissão. `release_audit_final_v2.json` discrimina essas
pendências; o draft requer revisão humana/editorial.
