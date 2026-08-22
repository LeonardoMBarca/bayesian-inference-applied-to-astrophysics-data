# 32 - Figuras e Leitura Visual da EDA

## 1. Objetivo

Este documento descreve as figuras geradas pela EDA e orienta como interpretá-las.

As figuras foram salvas em PNG com `dpi=300` em:

```text
figures/gold_eda/hat_p_7_b/
```

As imagens abaixo são incorporadas no Markdown apenas onde ajudam a leitura.

## 2. Curva Primária no Tempo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/01_primary_lightcurve_time.png
```

Conteúdo:

- eixo x: tempo Kepler/BKJD;
- eixo y: fluxo;
- fonte: `primary_lightcurve.csv`;
- inclui pontos antes do filtro por qualidade.

Uso:

Essa figura mostra a série temporal primária ainda com pontos marcados por
flags instrumentais. Ela ajuda a entender o volume inicial e a escala de fluxo.

## 3. Curva Filtrada Por Qualidade no Tempo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/02_quality_filtered_lightcurve_time.png
```

Conteúdo:

- eixo x: tempo Kepler/BKJD;
- eixo y: fluxo;
- fonte: `primary_lightcurve_quality_filtered.csv`;
- mantém apenas `quality == 0`.

Uso:

Essa figura é a melhor visão temporal antes do faseamento, pois mostra apenas
os pontos técnicos considerados bons pela flag da missão.

## 4. Curva Faseada Completa

Arquivo:

```text
figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png
```

Conteúdo:

- eixo x: fase orbital em dias, centrada no trânsito;
- eixo y: fluxo;
- fonte: `phase_folded_lightcurve.csv`.

Leitura:

A queda de fluxo aparece próxima de `phase = 0`, o que confirma visualmente que
o faseamento Gold está coerente com o tempo central de trânsito usado.

![Curva faseada completa](../../../figures/gold_eda/hat_p_7_b/03_phase_folded_lightcurve_full.png)

## 5. Janela de Trânsito Gold Atual

Arquivo:

```text
figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png
```

Conteúdo:

- eixo x: fase orbital em dias;
- eixo y: fluxo;
- fonte: `transit_window_lightcurve.csv`;
- janela aproximada: `±0,48527` dias.

Leitura:

A janela contém o trânsito, mas também bastante baseline fora do evento. Ela é
útil para diagnóstico amplo, porém parece larga para uma primeira modelagem
paramétrica simples.

![Janela de trânsito Gold atual](../../../figures/gold_eda/hat_p_7_b/04_transit_window_lightcurve.png)

## 6. Janela de Trânsito Com Binning Visual

Arquivo:

```text
figures/gold_eda/hat_p_7_b/05_transit_window_binned.png
```

Conteúdo:

- pontos individuais em baixa opacidade;
- mediana por bin de fase;
- intervalo interquartil por bin;
- linha vertical em fase zero.

Leitura:

O binning visual torna a queda de fluxo mais evidente sem ajustar um modelo.
Ele não altera a Gold e não substitui inferência. Serve apenas para inspeção.

![Janela com binning visual](../../../figures/gold_eda/hat_p_7_b/05_transit_window_binned.png)

## 7. Distribuição do Fluxo

Arquivo:

```text
figures/gold_eda/hat_p_7_b/06_flux_distribution.png
```

Conteúdo:

- histograma do fluxo na janela de trânsito;
- linha vertical na mediana.

Uso:

Ajuda a verificar a escala do fluxo e a assimetria esperada por mistura de
pontos em trânsito e fora do trânsito.

## 8. Distribuição de `flux_err`

Arquivo:

```text
figures/gold_eda/hat_p_7_b/07_flux_err_distribution.png
```

Conteúdo:

- histograma de `flux_err`;
- linha vertical na mediana.

Uso:

Ajuda a verificar se há incerteza observacional disponível para uma likelihood
gaussiana preliminar. A EDA encontrou `0` ausências em `flux_err`.

## 9. Comparação de Larguras de Janela

Arquivo:

```text
figures/gold_eda/hat_p_7_b/08_window_width_comparison.png
```

Conteúdo:

- painéis para `±0,50`, `±0,25`, `±0,15`, `±0,10` e `±0,05` dias;
- pontos de fluxo por fase;
- contagem de pontos por janela;
- profundidade visual aproximada quando calculável.

Leitura:

A figura mostra que:

- a janela `±0,50` dias é larga;
- a janela `±0,25` dias ainda tem bastante baseline;
- a janela `±0,15` dias preserva o trânsito e baseline local;
- a janela `±0,10` dias começa a ficar limitada no baseline fora do núcleo;
- a janela `±0,05` dias não tem baseline fora do núcleo para calcular contraste.

![Comparação de larguras de janela](../../../figures/gold_eda/hat_p_7_b/08_window_width_comparison.png)

## 10. Conclusão Visual

As figuras sustentam três conclusões diagnósticas:

1. O trânsito é visualmente identificável.
2. O faseamento está coerente com o centro de trânsito.
3. A janela Gold inicial é útil para inspeção, mas larga para modelagem inicial.

A recomendação visual e tabular combinada é iniciar a modelagem com:

```python
abs(phase) <= 0.15
```
