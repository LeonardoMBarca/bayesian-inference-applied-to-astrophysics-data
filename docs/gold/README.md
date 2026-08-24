# Documentação Gold

> Snapshot histórico da Gold inicial de HAT-P-7 b. A Gold atual constrói os dois
> alvos, preserva segmentos/exposição e normaliza por segmento. Consulte
> `data/gold/<target>/docs/README_gold.md` e `dataset_metadata.json`.

Esta pasta documenta a camada **Gold inicial** do datalake local do TCC.

A Gold foi construída a partir da Silver, sem modificar a RAW e sem modificar a
Silver. O objetivo foi selecionar um candidato principal e preparar um dataset
analítico inicial para uma futura modelagem bayesiana de trânsito.

No estado atual do projeto, a Gold não contém inferência bayesiana. Ela contém
apenas seleção, organização, filtros técnicos explícitos, faseamento e uma
janela de trânsito pronta para inspeção e modelagem posterior.

## Como Ler

Os arquivos estão numerados em ordem sugerida:

1. [21_contexto_escopo_e_regras_gold.md](21_contexto_escopo_e_regras_gold.md)  
   Explica o papel da Gold, a relação com RAW/Silver e o que foi ou não feito.

2. [22_selecao_candidato_gold.md](22_selecao_candidato_gold.md)  
   Documenta o scorecard, os critérios de pontuação, a escolha de HAT-P-7 b e a missão Kepler.

3. [23_pipeline_gold_e_codigo.md](23_pipeline_gold_e_codigo.md)  
   Mapeia scripts, módulos, configuração, comandos e fluxo de execução da Gold.

4. [24_catalogo_parametros_referencia.md](24_catalogo_parametros_referencia.md)  
   Descreve o catálogo Gold de parâmetros de referência do planeta selecionado.

5. [25_curvas_gold_e_preparacao_modelagem.md](25_curvas_gold_e_preparacao_modelagem.md)  
   Explica a curva primária, filtro por qualidade, fase orbital e janela de trânsito.

6. [26_manifestos_logs_validacoes_gold.md](26_manifestos_logs_validacoes_gold.md)  
   Documenta manifesto, logs, checksums, validações e evidências de reprodutibilidade.

7. [27_dicionario_de_arquivos_e_campos_gold.md](27_dicionario_de_arquivos_e_campos_gold.md)  
   Mapeia onde está cada informação da Gold e o significado dos campos principais.

8. [28_como_usar_gold_na_metodologia.md](28_como_usar_gold_na_metodologia.md)  
   Organiza a Gold em linguagem útil para a futura seção de metodologia do TCC.

## Saída Principal

```text
data/gold/
```

## Comandos

Pipeline Gold completo:

```bash
python scripts/build_gold_data.py
```

Somente seleção:

```bash
python scripts/build_gold_selection_report.py
```

## Resultado Principal

- Planeta selecionado: `HAT-P-7 b`
- Estrela hospedeira: `HAT-P-7`
- Slug: `hat_p_7_b`
- Missão selecionada: `Kepler`
- Fluxo usado: `pdcsap_flux`
- Erro usado: `pdcsap_flux_err`
- Curva primária: `6.163` linhas
- Curva filtrada por qualidade: `3.909` linhas
- Curva faseada: `3.909` linhas
- Janela de trânsito Gold inicial: `1.664` linhas
- Meia largura da janela inicial: aproximadamente `0,48527` dias

## Arquivo Principal Para Modelagem Futura

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Esse arquivo é a entrada Gold inicial para a próxima etapa, mas a EDA posterior
recomendou usar, dentro dele, uma janela preliminar mais estreita:

```python
abs(phase) <= 0.15
```

Essa recomendação pertence à etapa EDA, documentada separadamente em:

```text
docs/eda/gold_hat_p_7_b/
```

## O Que a Gold Não Faz

A Gold não executa:

- inferência bayesiana;
- posterior sampling;
- PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- ajuste físico de trânsito;
- comparação com literatura;
- gráficos finais do TCC.

Ela apenas prepara uma base analítica mínima, rastreável e reproduzível.
