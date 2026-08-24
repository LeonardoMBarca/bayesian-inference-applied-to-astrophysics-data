# Documentação do repositório científico

O índice atual separa contratos validados de snapshots históricos.

## Contratos atuais

- [README principal](../README.md) — execução e estado suportado;
- [política de armazenamento](STORAGE_POLICY.md) — o que é versionado ou
  regenerado;
- [modelagem](modeling/README.md) — M5 atual e modelos históricos;
- [experimentos M5](EXPERIMENTS_M5_NOISE.md) — priors, injeções e comparação;
- [adendo atual do TCC](TCC_HARDENING_ADDENDUM.md) — metodologia, resultados e limitações validados;
- [RAW](raw/README.md), [Silver](silver/README.md) e [Gold](gold/README.md) —
  documentação das camadas, sujeita à configuração e aos manifestos atuais.

## Fonte de verdade

Em caso de divergência, valide primeiro código/configuração executável,
manifestos/checksums e artefatos machine-readable. README, notebooks e exports
antigos não prevalecem sobre essa evidência. Divergências encontradas devem ser
corrigidas; a hierarquia não justifica manter documentação obsoleta.

As pastas `docs/context_exports/`, a EDA antiga de HAT-P-7 b e a documentação
M1–M3 são snapshots históricos anteriores ao hardening de 24 de agosto de
2026. Elas podem apoiar rastreabilidade do desenvolvimento, mas não sustentam
claims sobre o M5 ou o dataset Kepler-10 b atual sem nova validação.
