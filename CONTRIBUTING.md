# Contribuições

Este é um artefato de pesquisa. Correções devem melhorar código, documentação ou
evidência sem apagar os resultados que motivaram a mudança.

## Antes de alterar

Leia o [guia do avaliador](docs/REVIEWER_GUIDE.md), a
[disponibilidade dos materiais](docs/REPRODUCIBILITY.md) e `AGENTS.md`.
Abra uma branch de trabalho a partir da `main`; não reescreva o histórico.
O índice `publication/TCC_EVIDENCE_INDEX.json` identifica as fontes atuais.

## Relatar um problema

Uma issue técnica deve conter a pergunta ou comportamento esperado, o commit,
o comando executado, o ambiente, a saída relevante e os caminhos dos artefatos.
Para resultados científicos, inclua campanha, cenário, parâmetro e população
avaliada. Um resultado negativo não é automaticamente um bug.

Não envie CPF, endereço, assinatura, credencial ou documentos acadêmicos pessoais.
Questões sensíveis seguem [SECURITY.md](SECURITY.md), não uma issue pública.

## Regras para alterações

- Preserve RAW, inputs, protocolos, sementes, tentativas, traces, resultados e
  relatórios selados. Novo resultado exige novo identificador.
- Não descarte seeds, alvos, cadeias ou rejeições para melhorar a apresentação.
- Uma correção de relatório não autoriza mudar o resultado individual.
- Não afirme GP/ruído correlacionado, calibração universal ou equivalência entre
  programas sem evidência correspondente.
- Mantenha interfaces em `scripts/` pequenas e implementação reutilizável em `src/`.
- Acrescente regressões para defeitos de comportamento; confira links e escopo
  de afirmações em mudanças documentais.

## Verificar uma contribuição

No ambiente descrito em [Reprodução](docs/REPRODUCIBILITY.md):

```bash
python -m ruff check .
python scripts/static_validate.py
python scripts/run_ci_tests.py
python scripts/validate_hardened_artifacts.py
```

Identifique na PR quais verificações foram executadas, quais exigiram arquivos
externos e quais não foram possíveis. Não declare um lote final executado porque
um smoke test passou. Não inicie campanhas demoradas em uma alteração editorial.

O programa de publicação em `.agents/` registra planejamento e histórico. Próximas
fases, como M6/GP, não devem ser iniciadas automaticamente durante manutenção.
