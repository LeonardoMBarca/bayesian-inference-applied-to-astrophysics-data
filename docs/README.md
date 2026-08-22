# Documentação do Datalake Local, Análises e Modelagem

Esta pasta documenta, em detalhe, as etapas RAW, Silver, Gold, EDA e modelagem bayesiana do pequeno datalake local criado para o TCC:

**Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional**

- Aluno: Leonardo Moraes Barca
- Orientadora: Patrícia Belfiore Fávero
- Curso: MBA em Data Science e Analytics
- Foco RAW: coleta e rastreabilidade de dados públicos brutos, sem análise estatística.
- Foco Silver: validação, tabularização e padronização técnica, sem modelagem.
- Foco Gold: seleção de alvo e preparação analítica inicial, sem inferência bayesiana.
- Foco EDA: diagnóstico visual e estatístico da Gold, sem modelagem física.
- Foco Modelagem: modelos bayesianos incrementais M1, M2 e M3, ainda sem caracterização física final.

## Como ler esta documentação

Os arquivos estão organizados por camada:

```text
docs/
├── README.md
├── eda/
│   └── documentação das análises exploratórias e diagnósticas
├── gold/
│   └── documentação da camada analítica inicial Gold
├── modeling/
│   └── documentação dos modelos bayesianos
├── raw/
│   └── documentação da coleta bruta
└── silver/
    └── documentação da camada padronizada
```

Dentro de cada pasta, os arquivos continuam numerados para leitura sequencial, mas cada um também pode ser usado isoladamente como referência.

## Documentação RAW

Diretório:

```text
docs/raw/
```

Índice da subpasta:

[docs/raw/README.md](raw/README.md)

1. [00_contexto_escopo_e_regras_raw.md](raw/00_contexto_escopo_e_regras_raw.md)  
   Define o escopo acadêmico, o que foi feito e, principalmente, o que não foi feito.

2. [01_mapa_do_pipeline_e_codigo.md](raw/01_mapa_do_pipeline_e_codigo.md)  
   Explica a arquitetura simples do pipeline, os scripts, módulos Python e responsabilidades de cada arquivo.

3. [02_configuracao_execucao_ambiente.md](raw/02_configuracao_execucao_ambiente.md)  
   Documenta o ambiente, dependências, comandos de execução e configuração central.

4. [03_manifestos_logs_checksums_reexecucao.md](raw/03_manifestos_logs_checksums_reexecucao.md)  
   Explica os manifestos, logs, checksums SHA256, status de coleta e política de reexecução.

5. [04_nasa_exoplanet_archive.md](raw/04_nasa_exoplanet_archive.md)  
   Documenta a coleta no NASA Exoplanet Archive via TAP, tabelas `pscomppars` e `ps`, queries, CSVs e snapshots.

6. [05_mast_lightkurve_astroquery.md](raw/05_mast_lightkurve_astroquery.md)  
   Documenta a busca e download de curvas de luz no MAST por Lightkurve, incluindo Kepler, K2 e TESS.

7. [06_exomast.md](raw/06_exomast.md)  
   Documenta o uso do Exo.MAST como fonte auxiliar de metadados e identificadores.

8. [07_etd_varastro.md](raw/07_etd_varastro.md)  
   Documenta a coleta no ETD/VarAstro, snapshots HTML, endpoints públicos anônimos, observações e curvas JSON.

9. [08_inventario_por_planeta.md](raw/08_inventario_por_planeta.md)  
   Traz uma visão consolidada por planeta: NASA, MAST, Exo.MAST e ETD.

10. [09_validacao_e_qualidade.md](raw/09_validacao_e_qualidade.md)  
    Registra validações executadas, contagens, checksums e limitações.

11. [10_como_usar_na_metodologia.md](raw/10_como_usar_na_metodologia.md)  
    Reorganiza a documentação em linguagem próxima de metodologia acadêmica.

12. [11_dicionario_de_arquivos_e_campos.md](raw/11_dicionario_de_arquivos_e_campos.md)  
    Mapeia onde está cada informação, qual arquivo contém qual dado e quais campos principais existem.

## Documentação Silver

Diretório:

```text
docs/silver/
```

Índice da subpasta:

[docs/silver/README.md](silver/README.md)

13. [12_contexto_escopo_e_regras_silver.md](silver/12_contexto_escopo_e_regras_silver.md)  
    Define o papel da Silver, sua relação com a RAW, regras de imutabilidade e limites da etapa.

14. [13_mapa_do_pipeline_silver_e_codigo.md](silver/13_mapa_do_pipeline_silver_e_codigo.md)  
    Explica os scripts, módulos Python, fluxo de execução e responsabilidades do código Silver.

15. [14_catalogos_silver_nasa_e_exomast.md](silver/14_catalogos_silver_nasa_e_exomast.md)  
    Documenta a consolidação de catálogos NASA e Exo.MAST, incluindo mapeamento de campos.

16. [15_curvas_mast_silver.md](silver/15_curvas_mast_silver.md)  
    Documenta a leitura dos FITS MAST, extração de curvas tabulares e metadados de qualidade.

17. [16_etd_varastro_silver.md](silver/16_etd_varastro_silver.md)  
    Documenta a consolidação de observações ETD, curvas JSON públicas e pontos fotométricos.

18. [17_manifestos_logs_validacoes_silver.md](silver/17_manifestos_logs_validacoes_silver.md)  
    Explica manifesto Silver, logs, checksums, validação RAW e relatórios Silver.

19. [18_inventario_silver_por_planeta.md](silver/18_inventario_silver_por_planeta.md)  
    Resume a disponibilidade Silver por planeta, missão, fonte e quantidade de registros.

20. [19_dicionario_de_arquivos_e_campos_silver.md](silver/19_dicionario_de_arquivos_e_campos_silver.md)  
    Mapeia arquivos e campos da Silver, incluindo catálogos, curvas MAST, ETD e validações.

21. [20_como_usar_silver_na_metodologia.md](silver/20_como_usar_silver_na_metodologia.md)  
    Organiza a Silver em linguagem útil para a futura seção de metodologia do TCC.

## Documentação Gold

Diretório:

```text
docs/gold/
```

Índice da subpasta:

[docs/gold/README.md](gold/README.md)

22. [21_contexto_escopo_e_regras_gold.md](gold/21_contexto_escopo_e_regras_gold.md)  
    Define o papel da Gold, sua relação com RAW/Silver e seus limites.

23. [22_selecao_candidato_gold.md](gold/22_selecao_candidato_gold.md)  
    Documenta scorecard, critérios de pontuação e escolha de HAT-P-7 b.

24. [23_pipeline_gold_e_codigo.md](gold/23_pipeline_gold_e_codigo.md)  
    Explica scripts, módulos, configuração e fluxo de execução Gold.

25. [24_catalogo_parametros_referencia.md](gold/24_catalogo_parametros_referencia.md)  
    Documenta o catálogo de parâmetros de referência do planeta selecionado.

26. [25_curvas_gold_e_preparacao_modelagem.md](gold/25_curvas_gold_e_preparacao_modelagem.md)  
    Explica curva primária, filtro por qualidade, faseamento e janela de trânsito.

27. [26_manifestos_logs_validacoes_gold.md](gold/26_manifestos_logs_validacoes_gold.md)  
    Documenta manifesto, logs, checksums e validações Gold.

28. [27_dicionario_de_arquivos_e_campos_gold.md](gold/27_dicionario_de_arquivos_e_campos_gold.md)  
    Mapeia arquivos e campos da Gold.

29. [28_como_usar_gold_na_metodologia.md](gold/28_como_usar_gold_na_metodologia.md)  
    Organiza a Gold em linguagem útil para metodologia.

## Documentação EDA

Diretório:

```text
docs/eda/
```

Índice da subpasta:

[docs/eda/README.md](eda/README.md)

EDA Gold HAT-P-7 b:

[docs/eda/gold_hat_p_7_b/README.md](eda/gold_hat_p_7_b/README.md)

30. [29_contexto_escopo_e_regras_eda.md](eda/gold_hat_p_7_b/29_contexto_escopo_e_regras_eda.md)  
    Explica objetivo, entradas, saídas e limites da EDA.

31. [30_pipeline_eda_e_codigo.md](eda/gold_hat_p_7_b/30_pipeline_eda_e_codigo.md)  
    Documenta script, notebook, execução e reprodutibilidade.

32. [31_diagnosticos_estatisticos_e_tabelas.md](eda/gold_hat_p_7_b/31_diagnosticos_estatisticos_e_tabelas.md)  
    Explica métricas e tabelas derivadas.

33. [32_figuras_e_leitura_visual.md](eda/gold_hat_p_7_b/32_figuras_e_leitura_visual.md)  
    Documenta as figuras e incorpora imagens-chave no Markdown.

34. [33_resultados_recomendacoes_e_limitacoes.md](eda/gold_hat_p_7_b/33_resultados_recomendacoes_e_limitacoes.md)  
    Resume conclusões, recomendação de janela e limitações.

35. [34_dicionario_de_arquivos_e_campos_eda.md](eda/gold_hat_p_7_b/34_dicionario_de_arquivos_e_campos_eda.md)  
    Mapeia arquivos e campos produzidos pela EDA.

36. [35_como_usar_eda_na_metodologia.md](eda/gold_hat_p_7_b/35_como_usar_eda_na_metodologia.md)  
    Organiza a EDA em linguagem útil para metodologia.

## Documentação de Modelagem

Diretório:

```text
docs/modeling/
```

Índice da subpasta:

[docs/modeling/README.md](modeling/README.md)

M1 - Bayesian baseline HAT-P-7 b:

[docs/modeling/bayesian_baseline_hat_p_7_b/README.md](modeling/bayesian_baseline_hat_p_7_b/README.md)

37. [36_contexto_escopo_e_regras_m1.md](modeling/bayesian_baseline_hat_p_7_b/36_contexto_escopo_e_regras_m1.md)  
    Explica objetivo, escopo e limites do M1.

38. [37_pipeline_codigo_execucao_m1.md](modeling/bayesian_baseline_hat_p_7_b/37_pipeline_codigo_execucao_m1.md)  
    Documenta script, notebook, dependências e execução.

39. [38_dataset_preprocessamento_normalizacao_m1.md](modeling/bayesian_baseline_hat_p_7_b/38_dataset_preprocessamento_normalizacao_m1.md)  
    Explica filtros, janela de fase e normalização local.

40. [39_modelo_probabilistico_priors_likelihood_m1.md](modeling/bayesian_baseline_hat_p_7_b/39_modelo_probabilistico_priors_likelihood_m1.md)  
    Detalha especificação probabilística, priors e likelihood.

41. [40_resultados_diagnosticos_m1.md](modeling/bayesian_baseline_hat_p_7_b/40_resultados_diagnosticos_m1.md)  
    Resume posterior, R-hat, ESS e posterior predictive.

42. [41_figuras_tabelas_artefatos_m1.md](modeling/bayesian_baseline_hat_p_7_b/41_figuras_tabelas_artefatos_m1.md)  
    Mapeia figuras, tabelas, trace e artefatos do modelo.

43. [42_limitacoes_proximos_modelos_m1.md](modeling/bayesian_baseline_hat_p_7_b/42_limitacoes_proximos_modelos_m1.md)  
    Explica limitações e próximos modelos.

44. [43_como_usar_m1_na_metodologia.md](modeling/bayesian_baseline_hat_p_7_b/43_como_usar_m1_na_metodologia.md)  
    Organiza o M1 em linguagem útil para metodologia.

45. [44_reexecucao_robusta_nuts_m1.md](modeling/bayesian_baseline_hat_p_7_b/44_reexecucao_robusta_nuts_m1.md)  
    Documenta a reexecução robusta do M1 com NUTS, versionamento das runs,
    comparação com Metropolis e diagnóstico de convergência.

M2 - Bayesian predictive phase regression HAT-P-7 b:

[docs/modeling/bayesian_predictive_phase_regression_hat_p_7_b/README.md](modeling/bayesian_predictive_phase_regression_hat_p_7_b/README.md)

46. [01_contexto_e_objetivo.md](modeling/bayesian_predictive_phase_regression_hat_p_7_b/01_contexto_e_objetivo.md)  
    Explica o objetivo do M2 e sua diferença conceitual em relação ao M1.

47. [02_especificacao_do_modelo.md](modeling/bayesian_predictive_phase_regression_hat_p_7_b/02_especificacao_do_modelo.md)  
    Documenta entrada, pré-processamento, funções de base radial, priors,
    likelihood e amostragem.

48. [03_resultados_e_diagnosticos.md](modeling/bayesian_predictive_phase_regression_hat_p_7_b/03_resultados_e_diagnosticos.md)  
    Resume posterior, curva preditiva, resíduos, posterior predictive,
    diagnósticos MCMC e comparação com M1.

49. [04_limitacoes_e_proximos_passos.md](modeling/bayesian_predictive_phase_regression_hat_p_7_b/04_limitacoes_e_proximos_passos.md)  
    Explica limitações científicas do M2 e recomenda M3.

M3 - Bayesian trapezoid transit HAT-P-7 b:

[docs/modeling/bayesian_trapezoid_transit_hat_p_7_b/README.md](modeling/bayesian_trapezoid_transit_hat_p_7_b/README.md)

50. [01_contexto_e_objetivo.md](modeling/bayesian_trapezoid_transit_hat_p_7_b/01_contexto_e_objetivo.md)  
    Explica o objetivo do M3, sua pergunta científica e sua relação com M1 e M2.

51. [02_especificacao_do_modelo.md](modeling/bayesian_trapezoid_transit_hat_p_7_b/02_especificacao_do_modelo.md)  
    Documenta entrada, pré-processamento, normalização, priors, likelihood,
    parametrização trapezoidal, parâmetros derivados e amostragem.

52. [03_resultados_e_diagnosticos.md](modeling/bayesian_trapezoid_transit_hat_p_7_b/03_resultados_e_diagnosticos.md)  
    Resume posterior, diagnósticos MCMC, posterior predictive, resíduos,
    figuras e comparação qualitativa com M1 e M2.

53. [04_limitacoes_e_proximos_passos.md](modeling/bayesian_trapezoid_transit_hat_p_7_b/04_limitacoes_e_proximos_passos.md)  
    Explica limitações científicas do M3 e documenta a recomendação original
    de avançar para comparação M4.

M4 - Comparação de modelos HAT-P-7 b:

[docs/modeling/model_comparison_hat_p_7_b/README.md](modeling/model_comparison_hat_p_7_b/README.md)

54. [01_contexto_e_objetivo.md](modeling/model_comparison_hat_p_7_b/01_contexto_e_objetivo.md)  
    Explica o papel do M4, suas entradas e seu escopo como etapa comparativa.

55. [02_criterios_de_comparacao.md](modeling/model_comparison_hat_p_7_b/02_criterios_de_comparacao.md)  
    Documenta critérios de parâmetros, diagnósticos, métricas preditivas,
    resíduos, LOO/WAIC opcional e recomendação.

56. [03_resultados_comparativos.md](modeling/model_comparison_hat_p_7_b/03_resultados_comparativos.md)  
    Resume profundidade, `Rp/Rs`, diagnósticos, métricas preditivas, resíduos
    e figuras comparativas.

57. [04_recomendacao_e_limitacoes.md](modeling/model_comparison_hat_p_7_b/04_recomendacao_e_limitacoes.md)  
    Explica por que M3 foi recomendado como resultado principal preliminar e
    quais limitações permanecem.

## Visão rápida dos resultados

### RAW

- Diretório RAW principal: `data/raw`
- Tamanho aproximado após a limpeza dos arquivos manuais soltos: `82 MB`
- Total de arquivos em `data/raw`: `402`
- Linhas no manifesto global CSV: `749`
- Checksums auditados: `0` ausentes e `0` divergentes
- Arquivos FITS baixados do MAST/Lightkurve: `30`
- Curvas JSON públicas baixadas do ETD/VarAstro: `40`
- Tabelas de busca MAST/Lightkurve salvas: `24`
- Snapshots HTML ETD/VarAstro salvos: `16`
- JSONs Exo.MAST salvos: `26`
- Snapshot geral NASA `pscomppars`: `4.653` registros de dados, mais cabeçalho

### Silver

- Diretório Silver principal: `data/silver`
- Tamanho aproximado após a construção: `512 MB`
- Total de arquivos em `data/silver`: `29`
- Registros no manifesto Silver: `26`
- Checksums Silver divergentes: `0`
- Catálogo NASA `pscomppars` selecionado: `8` linhas
- Catálogo NASA `ps` consolidado: `167` linhas
- Metadados FITS MAST: `30` arquivos processados
- Curvas MAST tabularizadas: `10` tabelas
- Observações ETD consolidadas: `1.650`
- Pontos fotométricos ETD extraídos: `8.752`
- HAT-P-7 b e TrES-2 b possuem Kepler e TESS
- Todos os planetas possuem TESS
- Nenhum planeta possui K2 na Silver

### Gold

- Diretório Gold principal: `data/gold`
- Planeta selecionado: `HAT-P-7 b`
- Missão selecionada: `Kepler`
- Fluxo selecionado: `pdcsap_flux`
- Artefato principal futuro: `data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv`
- A Gold inicial não contém inferência bayesiana

### EDA Gold HAT-P-7 b

- Notebook: `notebooks/02_gold_eda_hat_p_7_b.ipynb`
- Script: `scripts/analyze_gold_lightcurve.py`
- Relatório: `reports/gold_eda_hat_p_7_b_report.md`
- Figuras: `figures/gold_eda/hat_p_7_b/`
- Tabelas: `tables/gold_eda/hat_p_7_b/`
- Pontos na janela Gold atual: `1.664`
- Valores ausentes em `flux`: `0`
- Valores ausentes em `flux_err`: `0`
- Trânsito visualmente identificável: sim
- Janela Gold inicial: aproximadamente `±0,48527` dias
- Janela recomendada para modelagem preliminar: `±0,15` dias
- A EDA não contém inferência bayesiana

### Modelagem M1

- Modelo: `box-shaped transit baseline`
- Planeta: `HAT-P-7 b`
- Missão: `Kepler`
- Pontos usados: `516`
- Janela de fase: `abs(phase) <= 0,15`
- Normalização: baseline local por mediana
- Execução recomendada: `002_nuts_robust`
- Amostrador recomendado: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- Profundidade posterior média: `0,00525258`
- HDI 94% da profundidade: `[0,00464576, 0,00587726]`
- `Rp/Rs` posterior médio: `0,07243869`
- HDI 94% de `Rp/Rs`: `[0,06815983, 0,07666328]`
- Posterior predictive: criado
- Diagnóstico robusto: `R-hat máximo = 1,00088086`, `ESS mínimo = 4553,60020940`, `divergências = 0`
- Uso correto: baseline comparativo, não caracterização física final

### Modelagem M2

- Modelo: regressão bayesiana preditiva por fase com bases radiais gaussianas
- Planeta: `HAT-P-7 b`
- Missão: `Kepler`
- Pontos usados: `516`
- `n_basis`: `12`
- `basis_width`: `0,035`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- `target_accept` final: `0,99`
- Diagnóstico: `R-hat máximo = 1,00292448`, `ESS mínimo = 2269,80467052`, `divergências = 0`
- `predicted_depth` exploratório médio: `0,00721029`
- Comparação qualitativa: `depth` robusto M1 = `0,00525258`
- Uso correto: modelo preditivo intermediário, não modelo físico final

### Modelagem M3

- Modelo: trânsito trapezoidal bayesiano aproximado
- Planeta: `HAT-P-7 b`
- Missão: `Kepler`
- Pontos usados: `516`
- Amostrador: `NUTS`
- Draws/tune/chains: `2000 / 2000 / 4`
- `target_accept` final: `0,90`
- Diagnóstico: `R-hat máximo = 1,00107423`, `ESS mínimo = 4212,34208408`, `divergências = 0`
- Profundidade posterior média: `0,00656620`
- HDI 94% da profundidade: `[0,00594692, 0,00716767]`
- `Rp/Rs` posterior médio: `0,08100761`
- HDI 94% de `Rp/Rs`: `[0,07711627, 0,08466210]`
- Duração total posterior média: `0,17664741` dias, ou `4,23954` horas
- Duração média de ingresso: `0,03697592` dias, ou `0,88742` horas
- Uso correto: modelo paramétrico aproximado, não caracterização física final

### Modelagem M4

- Etapa: comparação de M1, M2 e M3
- Planeta: `HAT-P-7 b`
- Script: `scripts/run_model_comparison.py`
- Notebook: `notebooks/06_model_comparison_hat_p_7_b.ipynb`
- Relatório: `reports/model_comparison_hat_p_7_b_report.md`
- Tabelas: `tables/model_comparison/hat_p_7_b/`
- Figuras: `figures/model_comparison/hat_p_7_b/`
- M1 RMSE: `0,00358754`
- M2 RMSE: `0,00317888`
- M3 RMSE: `0,00317499`
- M1 profundidade média: `0,00525258`
- M2 `predicted_depth` exploratório médio: `0,00721029`
- M3 profundidade média: `0,00656620`
- LOO/WAIC: indisponíveis porque os traces atuais não possuem `log_likelihood`
- Recomendação: M3 como `primary_preliminary_result`

## Observação importante sobre tentativas anteriores

Durante a validação, algumas tentativas iniciais ocorreram em ambiente com rede bloqueada pela sandbox e algumas hipóteses iniciais sobre o ETD/VarAstro foram registradas como falhas. Essas tentativas permanecem no manifesto e nos logs por rastreabilidade.

A execução final completa do comando principal terminou sem falhas de fonte:

```bash
python scripts/download_raw_data.py
```

No ambiente desta coleta, o comando foi executado com o interpretador do ambiente local:

```bash
.venv/bin/python scripts/download_raw_data.py
```

## O que esta documentação não cobre

Esta documentação já cobre as modelagens bayesianas M1, M2, M3 e a comparação M4. Ela ainda não
cobre:

- caracterização física final de HAT-P-7 b;
- comparação com literatura;
- modelos físicos completos de trânsito;
- comparação formal LOO/WAIC com `log_likelihood` salvo nos traces;
- texto final do TCC.

Essas etapas continuam planejadas para ciclos posteriores.
