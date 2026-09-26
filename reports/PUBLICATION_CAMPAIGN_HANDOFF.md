# Entrega do runner e estado científico

Validação de infraestrutura: **PASS**. Commit testado: `bf739762cdeecaa4d8d477cffafe5c78f7579bab`.
Suíte prática: 204 testes aprovados, 0 ignorados; um valor nulo significa ausência de confirmação. Detalhes e stderr preservados em `publication/validation/handoff/handoff_v5/validation.json`.

## Escopo entregue

Runner autônomo, protocolos pré-batch, ledger de seeds/IDs, isolamento de tentativas, checkpoint/retomada, limite de CPU/tempo, logs separados, estados e gates distintos, agregação por família, freshness e hashes, tarefas VSCode e operação tmux. Não depende de Codex.
Campanha final declarada: 117 trabalhos. Estimativa de planejamento: 31.86 h; teto suave configurado: 36 h. Não é garantia de conclusão.

| Família | Trabalhos finais declarados | Estado da evidência |
|---|---:|---|
| PUB-02 | 80 | Não executados pelo agente |
| PUB-03 | 2 | Não executados pelo agente |
| PUB-04 | 30 | Não executados pelo agente |
| PUB-05 | 5 | Não executados pelo agente |
| PUB-06 | 0 | Adiado; não há implementação/validação M6 |

Runs científicos finais realizados nesta entrega: **0**; aprovados/reprovados/falhos finais: **0/0/0**. A campanha não foi inicializada. Os arquivos futuros não são evidência já obtida.

## Evidência já disponível e resultados negativos

Baseline científico histórico e 26 artefatos protegidos verificados; 15 entradas FITS disponíveis. Matriz de 24 fontes primárias delimita contribuição como integração e avaliação, sem alegação de prioridade. Benchmark escolhido antes das comparações.
Dois pilotos P2 de sizing fizeram sampling e falharam na etapa ArviZ; traces/falhas preservados. O primeiro smoke externo revelou seed ignorada pela ponte juliet/dynesty: corrigido sem alterar priors/likelihood. Dois pilotos corrigidos repetiram o hash canônico, mas foram rejeitados pelo orçamento intencionalmente insuficiente. Isso não prova concordância posterior final.
Smoke runner v2: cinco trabalhos, seis tentativas; três fixtures concluídas e duas rejeições (uma física com 20 draws). Uma falha técnica anterior ao retry permanece. Stop/resume e nova chamada não duplicaram concluídos. Nenhum fixture/piloto é promovido a conclusão científica. Smoke v1 interrompido permanece auditável.

## Perguntas ainda abertas

Coverage/bias finais, compatibilidade independente, efeitos de ablations e generalização multi-alvo aguardam a execução do usuário. Intervalos de coverage terão precisão limitada com 20 replicações. P4 tem 3 pares: efeitos descritivos, não taxas de erro precisas. Não foi demonstrado ainda um caso final sampler-converged/scientifically-invalid.
M5 usa jitter branco independente. OU exploratório e M6/GP foram adiados por prazo; não há alegação de tratamento de ruído correlacionado. Normalização P2 é exata e conhecida; P4/P5 estimam medianas e não propagam toda essa incerteza. Período/catálogos condicionam análise observacional, portanto comparação de catálogo não é validação independente. Diagnósticos temporais após thinning não excluem correlação na cadência nativa.

## Auditoria e reprodutibilidade

Testes incluem truth leakage, determinismo, identidade de dataset, falhas preservadas, denominadores, mapping externo, gates, corrupção, processo órfão, budget, isolamento e freshness. Preflight verifica ambientes e fontes antes do P2. A revisão hostil corrigiu inconsistência de dataset embutido, RNG externo, códigos exatos de controle e subprocesso não-zero, entre outros. Nenhum threshold foi afrouxado para salvar observações.
A release científica completa permanece INCOMPLETA. Ainda não houve clean-room de todos os 117 resultados, arquivamento público integral de traces nem DOI. As fixtures clean-room/testes de infraestrutura não substituem isso. `publication/release_audit.json` não é autorização para publicação.

## Operação e fontes para TCC/paper

```sh
python scripts/run_publication_campaign.py --dry-run
python scripts/run_publication_campaign.py --resume
python scripts/run_publication_campaign.py --status
python scripts/run_publication_campaign.py --stop
python scripts/run_publication_campaign.py --aggregate
python scripts/verify_publication_campaign.py
```

Instruções completas: `docs/publication/CAMPAIGN_RUNBOOK.md`. Lista exata de fontes atuais e outputs futuros: `docs/publication/TCC_PAPER_SOURCE_INVENTORY.json`. Relatórios científicos derivados serão gerados sob `reports/publication_campaign/tcc_campaign_v1/`; não copiar números de pilotos para a versão final do TCC.
