# Campanha em segundo plano no Windows

Na raiz do repositorio, depois das validacoes/protocolo e da autorizacao para
retomar a campanha:

```powershell
powershell.exe -NoProfile -File .\scripts\start_publication_campaign_background.ps1
```

Aceita `-RepoRoot` e `-Config` (padrao `configs/publication/tcc_final_campaign.json`).
Le `runtime.scientific_python` e `runtime.wsl_distribution` desse config.
Sempre solicita `--resume`; o runner preserva tentativas e aplica seu lock,
protocolo, orcamento e regras de retomada. O wrapper nao decide retries.

O comando retorna logo com JSON contendo PID Windows e diretorio de logs.
Um PowerShell oculto independente mantem `wsl.exe` conectado ao controller
ate o processo terminar. Fechar o monitor ou a janela que iniciou o comando
nao e um comando de parada. Nao depende de tmux, de Codex ou do monitor.
O comportamento de processos Windows independentes e descrito em
[Start-Process](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/start-process?view=powershell-5.1).

Cada invocacao cria um diretorio exclusivo em
`logs/publication_campaign/<campaign_id>/<UTC_UUID>/`, com `launch.json`,
`supervisor.started.json`, stdout/stderr do supervisor e do controller, e
`supervisor.exit.json`. Nao sobrescreve logs anteriores. Retorno do lancador
nao comprova inicio cientifico: confira o arquivo `supervisor.started.json`,
os logs e o status oficial da campanha. Se o runner recusar um segundo
controller, o wrapper registra sua saida; nao insiste nem reinicia.

Para consultar ou pedir parada graciosa, use o CLI existente:

```powershell
python scripts/run_publication_campaign.py --config configs/publication/tcc_final_campaign.json --status
python scripts/run_publication_campaign.py --config configs/publication/tcc_final_campaign.json --stop
```

`--stop` segue as regras do runner; nao mate o supervisor para parar a ciencia.
O monitor somente leitura pode ser aberto e fechado separadamente.

O supervisor solicita apenas `ES_CONTINUOUS | ES_SYSTEM_REQUIRED` enquanto
acompanha o cliente WSL. Nao mantem tela ligada nem altera plano de energia ou
`.wslconfig`. Libera a solicitacao em `finally`, inclusive apos erro/saida;
se a solicitacao inicial falhar, nao inicia controller. Nao impede suspensao
manual, fechamento da tampa, desligamento, logoff, falha do host ou falta de
energia. Mantenha PC energizado/ventilado. Veja
[SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).

Nao ha reinicio automatico do supervisor/WSL/campanha. Encerramento forcado
do processo pode impedir o registro final; ausencias de artefatos devem ser
investigadas, nunca interpretadas como sucesso. Esta protecao operacional
nao identifica retrospectivamente a causa de qualquer desligamento do WSL.

Teste de engenharia reproduzivel (aproximadamente 100 s, Python padrao do WSL,
fixture temporaria com caminho contendo espacos; nao executa MCMC):

```powershell
powershell.exe -NoProfile -File tests/manual/validate_windows_background.ps1 -EvidencePath publication/engineering/windows_background_validation_NEW.json
```

O teste fecha somente seu proprio monitor, espera mais de 60 s, verifica
supervisor/cliente WSL vivos e exige saida normal com liberacao de KeepAwake.
O nome de evidencia deve ser novo; arquivos existentes nao sao sobrescritos.
