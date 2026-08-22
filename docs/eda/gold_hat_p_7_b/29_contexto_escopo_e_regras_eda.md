# 29 - Contexto, Escopo e Regras da EDA

## 1. Contexto

Após a criação da Gold, foi necessário verificar se o dataset preparado para
HAT-P-7 b realmente parecia adequado para uma primeira modelagem bayesiana.

A Gold já havia definido:

- planeta: `HAT-P-7 b`;
- missão: `Kepler`;
- fluxo: `pdcsap_flux`;
- erro: `pdcsap_flux_err`;
- curva primária: `6.163` linhas;
- curva filtrada por qualidade: `3.909` linhas;
- curva faseada: `3.909` linhas;
- janela inicial de trânsito: `1.664` linhas;
- meia largura da janela inicial: aproximadamente `0,48527` dias.

A EDA foi criada para diagnosticar esses artefatos antes de qualquer modelo.

## 2. Objetivo

O objetivo da EDA é responder:

1. A curva mostra um trânsito visualmente identificável?
2. A janela Gold atual parece adequada ou larga demais?
3. Há dados suficientes em uma janela mais estreita?
4. `flux_err` está disponível para uma likelihood gaussiana preliminar?
5. A Gold parece pronta para uma primeira modelagem bayesiana?
6. Qual arquivo deve ser usado na próxima etapa?

## 3. Entradas

A EDA lê:

```text
data/gold/hat_p_7_b/catalogs/reference_parameters.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv
data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv
data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

## 4. Saídas

A EDA escreve apenas em:

```text
notebooks/
reports/
figures/
tables/
```

Arquivos criados:

```text
notebooks/02_gold_eda_hat_p_7_b.ipynb
scripts/analyze_gold_lightcurve.py
reports/gold_eda_hat_p_7_b_report.md
figures/gold_eda/hat_p_7_b/
tables/gold_eda/hat_p_7_b/
```

## 5. O Que a EDA Faz

A EDA calcula:

- número de linhas;
- intervalo de tempo;
- intervalo de fase;
- valores ausentes em `flux`;
- valores ausentes em `flux_err`;
- estatísticas de `flux`;
- estatísticas de `flux_err`;
- contagem de `quality`;
- mediana e desvio padrão do fluxo;
- dispersão fora do núcleo de trânsito;
- profundidade visual aproximada por contraste de medianas;
- comparação de janelas em torno da fase zero.

## 6. O Que a EDA Não Faz

A EDA não faz:

- inferência bayesiana;
- ajuste físico de trânsito;
- posterior sampling;
- PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- comparação com literatura;
- estimativa final de profundidade;
- normalização final;
- remoção estatística de outliers;
- alteração de RAW/Silver/Gold.

## 7. Interpretação da Profundidade Visual

A EDA calcula uma profundidade visual aproximada.

Ela é obtida por contraste entre:

- mediana do fluxo dentro de um núcleo de trânsito;
- mediana do fluxo fora desse núcleo, dentro da janela analisada.

Essa métrica é apenas exploratória.

Ela não deve ser chamada de:

- estimativa bayesiana;
- ajuste de trânsito;
- resultado físico final;
- parâmetro posterior.

Ela serve apenas para confirmar se a queda de fluxo é visível e coerente com a
expectativa de um trânsito.

## 8. Regra de Imutabilidade

A EDA não modifica os arquivos em:

```text
data/raw/
data/silver/
data/gold/
```

Essa regra foi validada por comparação de checksums, tamanhos e timestamps dos
arquivos dessas camadas antes e depois da execução da EDA.

## 9. Resultado Geral

A EDA concluiu que:

- há trânsito visualmente identificável;
- `flux_err` está disponível;
- a janela Gold inicial é ampla para modelagem;
- uma janela de `±0,15` dias é uma recomendação preliminar mais focada;
- o arquivo Gold principal deve continuar sendo lido, com filtro adicional por fase na etapa de modelagem.
