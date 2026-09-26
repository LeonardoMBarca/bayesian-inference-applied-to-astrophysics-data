# Campanha autônoma do TCC

Execute somente na branch `publication-grade-validation`. O comando não usa
Codex, LLM, confirmação interativa ou rede para iniciar o próximo experimento.
As entradas observacionais foram pré-selecionadas e estão disponíveis localmente.
O batch final **não foi executado durante a preparação do runner**.

## 1. Configuração

Arquivo: `configs/publication/tcc_final_campaign.json`.

O plano final contém 117 trabalhos: P2 = 80, P3 = 2, P4 = 30 e P5 = 5.
P2 tem quatro cenários principais com 20 realizações cada. OU exploratório e
M6 estão adiados por orçamento, conforme `COMPUTE_BUDGET_AMENDMENT.md`.
A estimativa de planejamento é cerca de 31,86h; não é garantia de conclusão.

Com o controlador parado, pode ajustar `resources.max_campaign_hours`, `resources.max_runtime_hours`
(teto por sessão), `max_workers`, `cores_per_run` e caminhos de intérpretes.
O padrão é uma inferência por vez, até quatro cores; o controlador impede
oversubscription por CPU. `memory_limit_gb` é uma estimativa consultiva, não um
limite de memória imposto pelo sistema operacional. Não altere priors, gates,
seeds, dados ou contagens de uma campanha iniciada.

Para ampliar posteriormente para 50–100 realizações, use outro `campaign_id`,
por exemplo `paper_campaign_v1`, com protocolo/contagens compatíveis e ledger
pré-batch próprio. Não basta editar o número sob a identidade do TCC. Depois de
revisar o desenho e os testes, gere o ledger com `PYTHONPATH=src python -m
publication.campaign_plan --config NOVO_CONFIG --freeze-plan` e faça commit
dos protocolos/config/ledger antes de executar. O runner recusa drift.

## 2. Um comando

Na raiz do repositório:

```sh
python scripts/run_publication_campaign.py --dry-run
python scripts/run_publication_campaign.py --config configs/publication/tcc_final_campaign.json --resume
```

No Windows, o launcher encaminha os argumentos ao WSL `Ubuntu-24.04` e ao
Python científico configurado. No Linux/WSL, encaminha ao mesmo ambiente
quando necessário. O ambiente independente juliet é separado e não substitui
o ambiente PyMC. Ausência de ambiente, versão divergente, branch incorreta,
protocolo não commitado ou fonte alterada bloqueiam a execução antes do P2.

## 3. VSCode / Play

`Terminal → Run Task` oferece:

- `Publication: Dry Run`
- `Publication: Run / Resume`
- `Publication: Status`
- `Publication: Stop gracefully`
- `Publication: Aggregate Results`

Em `Run and Debug`, selecione `Publication: Run / Resume` e clique Play
(requer extensão Python/debugpy). Rodar pelo terminal integrado não é a opção
de background recomendada: use tmux para poder fechar o VSCode.

## 4. Background independente da sessão

O `tmux` foi localizado em `/usr/bin/tmux` nesta instalação. Em um terminal WSL:

```sh
cd '/mnt/c/Users/Leonardo Barca/Desktop/workspace/personal/bayesian-inference-applied-to-astrophysics-data'
tmux new -s tcc-publication
/home/leonardo_barca/mc3/bin/python3.14 scripts/run_publication_campaign.py --resume
```

Desconecte com `Ctrl+B`, solte as teclas e pressione `D`. Pode fechar o VSCode e
o Codex. Para reconectar: `tmux attach -t tcc-publication`.
Isso preserva o processo ao desconectar o terminal, não após reboot/encerramento
do WSL. Não use `wsl --shutdown` durante a campanha; evite suspensão do
computador. Após reboot, abra WSL/tmux novamente e use `--resume`.

Fontes operacionais: [manual introdutório oficial do tmux](https://github.com/tmux/tmux/wiki/Getting-Started)
e [comandos oficiais WSL](https://learn.microsoft.com/en-us/windows/wsl/basic-commands).

## 5. Progresso

```sh
python scripts/run_publication_campaign.py --status
```

Mostra contagens por família, execução/rejeição/falha, pendências e orçamento
consumido. Logs gerais: `logs/publication_campaign/tcc_campaign_v1/campaign.log`.
Cada tentativa tem stdout e stderr separados, sem descartar warnings.
O tempo contabiliza sessões ativas e conservadoramente intervalos sem controle
em que havia workers registrados; não é tempo de CPU medido pelo kernel.

## 6. Parada segura

Em outro terminal:

```sh
python scripts/run_publication_campaign.py --stop
```

O trabalho atual termina, é selado por checksums, relatórios parciais são gerados
e os seguintes permanecem PLANNED. `Ctrl+C` no controlador também solicita parada
graciosa; prefira `--stop`. O limite de horas é suave: não mata MCMC no meio.
Uma estimativa conservadora pode impedir o início do próximo trabalho antes do
teto. Não altere o estado manualmente para “destravar” um run.

## 7. Retomada

```sh
python scripts/run_publication_campaign.py --resume
```

Completed e rejected são verificados por hash e não repetidos. Um worker órfão
ainda vivo é reconhecido por PID + identidade de início/boot; nunca se inicia
uma cópia concorrente. Interrupções sem conclusão preservam o diretório antigo;
uma nova tentativa usa a mesma seed em outro diretório. Uma falha técnica não
classificada não recebe retry automático. Por padrão, finais têm zero retries
automáticos; rejeição científica nunca gera retry. Corrupção é BLOCKED, não
autorização para sobrescrever. Para estender o orçamento, aumente apenas o teto
em `resources` e retome.

Não há checkpoint dentro da adaptação NUTS: um replicate interrompido
abruptamente pode precisar começar novamente. Isso é diferente de repetir um
replicate concluído, que é proibido. Todas as tentativas ficam auditáveis.

## 8. Resultados e auditoria

- Estado: `artifacts/publication_campaign/tcc_campaign_v1/campaign_state.json`.
- Tentativas: `artifacts/publication_campaign/tcc_campaign_v1/runs/<PUB>/<scenario>/<replicate>/attempt_NNN/`.
- Preparação P5 isolada: `publication/observational/PUB-05/<target>/<run_id>/`.
- Consolidação: `reports/publication_campaign/tcc_campaign_v1/`.
- Logs: `logs/publication_campaign/tcc_campaign_v1/`.

Cada tentativa contém config, input/hash, resultado/gates, identidade do código,
diagnósticos disponíveis, trace quando produzido e completion manifest.
Ground truth sintético fica fora do subprocesso de inferência.
`campaign_summary.json`, `campaign_summary.md`, inventário, tabela de tentativas,
falhas, rejeições, coverage/bias e figuras são gerados automaticamente.
Subpastas PUB-02–PUB-05 contêm as análises de cada família. Não copie manualmente
números de um run favorável para o TCC.

```sh
# Regenerar somente derivados, sem MCMC (com controlador parado):
python scripts/run_publication_campaign.py --aggregate
# Verificar hashes e freshness dos relatórios:
python scripts/verify_publication_campaign.py --config configs/publication/tcc_final_campaign.json
```

Uma campanha completa pode conter rejeições e falhas; isso não significa
“todos os modelos válidos”. A aprovação da infraestrutura tampouco é aprovação
do paper. O verificador de release completa permanece reprovado enquanto
faltarem evidência final e revisão científica. Traces `.nc` não são adicionados
automaticamente ao Git: arquive-os com os hashes e política de armazenamento
antes de alegar reprodução pública integral.
