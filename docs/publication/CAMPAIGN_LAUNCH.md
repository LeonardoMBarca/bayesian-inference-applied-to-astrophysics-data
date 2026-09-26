# Lançamento autorizado após a validação

Depois da conclusão e do commit da infraestrutura, o usuário autorizou
explicitamente iniciar a campanha, em um terminal visível, sem esperar seu
retorno. Essa instrução substitui apenas a exigência anterior de que o primeiro
lançamento fosse feito manualmente pelo usuário; não altera o protocolo, as
seeds, os gates, as prioridades ou o orçamento científico.

- Campanha: `tcc_campaign_v1`.
- Commit de lançamento registrado pelo controlador:
  `da800144f3a09b0a482534be6367dedf5bde91bf`.
- Criação do estado: `2026-09-26T20:18:21.225846+00:00`.
- Terminal visível: Windows Terminal, título `TCC Publication`.
- Distribuição WSL: `Ubuntu-24.04`; sessão tmux: `tcc-publication`.
- Primeiro trabalho observado: `PUB-02__deep_short__rep_0000`, em `RUNNING`;
  o log confirmou NUTS com quatro chains em quatro jobs. Isso comprova início,
  não convergência nem aprovação científica.
- Painel de status: atualização a cada 60 segundos, independente do Codex.

O estado corrente, os horários, os processos, as tentativas e os resultados
pertencem a `artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json`
e ao journal em `logs/publication_campaign/tcc_campaign_v1/campaign.log`.
Não use este registro de lançamento como contagem atual de resultados.
Não foram feitos commits dos arquivos vivos enquanto estavam sendo escritos.
Os commits posteriores ao lançamento que registram esta autorização são apenas
documentais; fontes Python, configuração, protocolos e ledger permanecem iguais.

`reports/PUBLICATION_CAMPAIGN_HANDOFF.md` e as validações `handoff_v1`–`handoff_v5`
são snapshots **pré-lançamento**, conservados sem reescrever o estado histórico.
A validação v5 aprovou 204 testes com zero skips; não é uma conclusão científica
dos batches agora em andamento. Não se deve executar novamente o verificador
específico de handoff pré-lançamento para avaliar uma campanha já iniciada;
use status e, após a agregação, `scripts/verify_publication_campaign.py`.

## Operação

Na raiz do repositório:

```sh
python scripts/run_publication_campaign.py --status
python scripts/run_publication_campaign.py --stop
python scripts/run_publication_campaign.py --resume
```

Para reconectar no WSL: `tmux attach -t tcc-publication`. Para desconectar sem
parar, pressione `Ctrl+B`, solte e pressione `D`. `Ctrl+B`, depois `Z`, alterna
o zoom do painel de status. Não suspenda/desligue a máquina nem encerre o WSL
se quiser processamento contínuo. Depois de reboot, é necessário retomar;
não há checkpoint dentro de um replicate NUTS interrompido.

O orçamento de 36 horas é suave: o trabalho ativo pode terminar antes da parada,
sem iniciar os trabalhos pendentes. M6 continua desabilitado. Mais instruções,
limites e caminhos em `CAMPAIGN_RUNBOOK.md`.

Referências operacionais: [Windows Terminal CLI](https://learn.microsoft.com/en-us/windows/terminal/command-line-arguments)
e [tmux](https://github.com/tmux/tmux/wiki/Getting-Started).
