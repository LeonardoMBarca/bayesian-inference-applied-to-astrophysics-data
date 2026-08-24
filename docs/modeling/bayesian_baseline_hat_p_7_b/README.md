# Documentação M1 - Bayesian Baseline - HAT-P-7 b

> Snapshot histórico específico de HAT-P-7 b. Não descreve o M5 atual.

Esta pasta documenta o primeiro modelo bayesiano preliminar do projeto:

```text
M1 - box transit baseline
```

O modelo estima uma distribuição posterior para a profundidade média do
trânsito e deriva:

```text
Rp/Rs = sqrt(depth)
```

## Como Ler

1. [36_contexto_escopo_e_regras_m1.md](36_contexto_escopo_e_regras_m1.md)  
   Explica o objetivo do M1, seu papel na sequência de modelos e seus limites.

2. [37_pipeline_codigo_execucao_m1.md](37_pipeline_codigo_execucao_m1.md)  
   Documenta script, notebook, dependências, execução e ambiente.

3. [38_dataset_preprocessamento_normalizacao_m1.md](38_dataset_preprocessamento_normalizacao_m1.md)  
   Explica filtros, janela de fase e normalização local.

4. [39_modelo_probabilistico_priors_likelihood_m1.md](39_modelo_probabilistico_priors_likelihood_m1.md)  
   Detalha modelo probabilístico, priors, likelihood e parâmetro derivado.

5. [40_resultados_diagnosticos_m1.md](40_resultados_diagnosticos_m1.md)  
   Resume posterior, R-hat, ESS, posterior predictive e interpretação cautelosa.

6. [41_figuras_tabelas_artefatos_m1.md](41_figuras_tabelas_artefatos_m1.md)  
   Mapeia tabelas, figuras, `trace.nc` e arquivos de configuração.

7. [42_limitacoes_proximos_modelos_m1.md](42_limitacoes_proximos_modelos_m1.md)  
   Explica limitações científicas e computacionais e próximos modelos.

8. [43_como_usar_m1_na_metodologia.md](43_como_usar_m1_na_metodologia.md)  
   Organiza a etapa M1 em linguagem útil para a metodologia do TCC.

9. [44_reexecucao_robusta_nuts_m1.md](44_reexecucao_robusta_nuts_m1.md)  
   Documenta a reexecução robusta com NUTS, o versionamento das runs e a
   comparação com a execução curta Metropolis.

## Artefatos Principais

Script:

```text
scripts/run_bayesian_baseline.py
scripts/run_bayesian_baseline_nuts_robust.py
```

Notebook:

```text
notebooks/03_bayesian_baseline_hat_p_7_b.ipynb
```

Trace:

```text
models/bayesian_baseline/hat_p_7_b/trace.nc
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/trace.nc
```

Relatório:

```text
reports/bayesian_baseline_hat_p_7_b_report.md
reports/bayesian_baseline_hat_p_7_b_nuts_robust_report.md
```

Tabelas:

```text
tables/bayesian_baseline/hat_p_7_b/
```

Figuras:

```text
figures/bayesian_baseline/hat_p_7_b/
```

## Resultado Resumido Atual

Execução recomendada para interpretação do M1:

```text
002_nuts_robust
```

- Pontos usados: `516`
- Janela de fase: `abs(phase) <= 0,15`
- Normalização: `flux / baseline_median`
- `baseline_median`: `1040715,45`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- Profundidade posterior média: `0,00525258`
- HDI 94% da profundidade: `[0,00464576, 0,00587726]`
- `Rp/Rs` posterior médio: `0,07243869`
- HDI 94% de `Rp/Rs`: `[0,06815983, 0,07666328]`
- Posterior predictive: criado
- Maior R-hat: `1,00088086`
- Menor ESS: `4553,60020940`
- Divergências: `0`

## Atenção

Os artefatos planos originais continuam representando a execução operacional
curta com Metropolis. Eles foram preservados por rastreabilidade em:

```text
models/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
tables/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
figures/bayesian_baseline/hat_p_7_b/runs/001_operational_metropolis/
```

Para interpretação científica preliminar do M1, usar a execução:

```text
models/bayesian_baseline/hat_p_7_b/runs/002_nuts_robust/
```

Mesmo com bons diagnósticos, M1 continua sendo baseline simplificado, não
caracterização física final do sistema.
