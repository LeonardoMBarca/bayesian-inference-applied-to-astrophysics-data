# Monitor Windows - somente leitura

Execute na raiz do repositorio, sem precisar do Codex:

```powershell
powershell.exe -NoProfile -File .\scripts\watch_publication_campaign.ps1
```

Atualiza a cada 10 segundos. `Ctrl+C` fecha apenas o monitor; ele nao inicia,
reinicia nem encerra controller, worker ou inferencia. Nao escreve no repositorio.
Nao use `Get-Content -Wait` sobre `campaign_state.json` para substitui-lo.

Uma unica leitura, ou estado alternativo:

```powershell
.\scripts\watch_publication_campaign.ps1 -Once
.\scripts\watch_publication_campaign.ps1 -RepoRoot 'C:\caminho\repo' -CampaignId 'tcc_campaign_v1'
.\scripts\watch_publication_campaign.ps1 -RepoRoot 'C:\caminho\fixture' -StatePath 'state.json' -Once
```

O percentual e `(COMPLETED + COMPLETED_REJECTED) / jobs declarados`. Rejeicao
cientifica nao e falha tecnica nem confirmacao de um resultado fisico valido.
As demais categorias sao mostradas separadamente.

Checkpoint com mais de 30 segundos, horario invalido ou leitura indisponivel
gera **STALE**. `RUNNING` e sempre apresentado como o ultimo estado **gravado**,
nunca como prova de processo vivo. Checkpoint recente tambem nao comprova
atividade. O monitor permanece aberto no estado STALE; nao tenta recuperar a
campanha automaticamente.

O monitor nao compara PID Linux com processos Windows. Para verificar
identidade/atividade, use `--status` da campanha no WSL e consulte
`effective_status`; um checkpoint antigo pode corresponder a controller parado.

## Opcao noturna: `-KeepAwake`

Desligada por padrao. Para solicitar explicitamente:

```powershell
powershell.exe -NoProfile -File .\scripts\watch_publication_campaign.ps1 -KeepAwake
```

Usa `SetThreadExecutionState(ES_CONTINUOUS | ES_SYSTEM_REQUIRED)` apenas enquanto
o monitor acompanha um estado nao terminal. Nao mantem a tela ligada, nao
habilita away mode e nao altera o plano de energia. Libera a solicitacao com
`ES_CONTINUOUS` no `finally` (`Ctrl+C`, saida normal e `-Once`) e ao ler estado
terminal sem jobs registrados como `RUNNING`; continua monitorando sem reiniciar
nada. Nao impede suspensao manual, fechamento da tampa, desligamento ou falta
de energia. Mantenha o PC ligado a energia e respeite ventilacao/temperatura.
Essas limitacoes seguem a [documentacao oficial da Microsoft](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).

STALE nao e motivo para fechar o monitor ou reiniciar a campanha. Uma solicitacao
ja ativa permanece durante checkpoint indisponivel/antigo e nao comprova que
controller/worker continuam vivos. Se a API falhar, um aviso informa que a
protecao contra suspensao nao esta garantida. Fechar o processo encerra a
solicitacao; a campanha e um processo separado e permanece intacta.

Estado e logs sao abertos com `.NET FileStream`, acesso somente leitura e
`FileShare.ReadWrite | FileShare.Delete`. Todos os handles sao fechados com
`Dispose`, inclusive em excecoes, antes de exibir conteudo ou aguardar. Isso
permite que o WSL substitua atomicamente o checkpoint enquanto o monitor le.
A leitura do estado repete brevemente erros transitorios de I/O (inclusive
arquivo momentaneamente ausente), sem manter handle aberto entre tentativas.

O monitor acompanha automaticamente stdout/stderr da ultima tentativa dos jobs
registrados como `RUNNING`, incluindo a ultima leitura quando observa sua saida
desse estado. Nao abre/reexibe os logs de todos os jobs historicos ja concluidos;
a primeira tela resume suas contagens. Para um job acompanhado, primeiro mostra
ate 15 linhas recentes; depois apenas linhas novas. Le no
maximo 1 MiB por log/ciclo, mantem apenas posicao e fragmentos em memoria, e
continua no ciclo seguinte. Fragmentos UTF-8/linhas incompletas aguardam o
proximo trecho. Novas tentativas ganham cursores separados. Nao substitui os
logs e manifests preservados como evidencia cientifica.
