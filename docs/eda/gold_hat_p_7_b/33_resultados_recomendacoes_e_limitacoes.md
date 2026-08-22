# 33 - Resultados, Recomendações e Limitações da EDA

## 1. Pergunta: A Curva Mostra Um Trânsito Visualmente Identificável?

Resposta:

```text
Sim.
```

A queda de fluxo aparece próxima de `phase = 0` na curva faseada e na janela de
trânsito. O binning visual reforça essa leitura.

A profundidade visual aproximada na janela Gold atual foi:

```text
0,006501
```

Essa profundidade é apenas exploratória.

## 2. Pergunta: A Janela Atual Parece Excessivamente Larga?

Resposta:

```text
Sim, para a primeira modelagem.
```

A janela Gold atual usa aproximadamente:

```text
±0,48527 dias
```

Ela é útil como janela inicial conservadora, pois garante que o trânsito e
baseline amplo estejam presentes. Porém, para um modelo bayesiano preliminar,
ela inclui baseline demais em relação à duração do trânsito.

## 3. Pergunta: Há Dados Suficientes em Uma Janela Mais Estreita?

Resposta:

```text
Sim.
```

Comparação:

| Janela | Pontos | Pontos fora do núcleo |
|---:|---:|---:|
| `±0,50` | `1.711` | `1.424` |
| `±0,25` | `854` | `567` |
| `±0,15` | `516` | `229` |
| `±0,10` | `335` | `48` |
| `±0,05` | `179` | `0` |

A janela `±0,15` dias preserva pontos suficientes dentro e fora do núcleo do
trânsito.

## 4. Recomendação de Janela

Recomendação preliminar:

```python
abs(phase) <= 0.15
```

Justificativa:

- mantém `516` pontos;
- mantém `287` pontos dentro do núcleo do trânsito;
- mantém `229` pontos fora do núcleo;
- preserva baseline local;
- reduz a largura em relação à janela Gold inicial;
- evita a janela `±0,10`, que já fica com baseline externo limitado;
- evita `±0,05`, que não tem baseline externo suficiente.

## 5. Pergunta: Há `flux_err` Utilizável Para Likelihood Gaussiana?

Resposta:

```text
Sim.
```

Na janela Gold atual:

| Métrica | Valor |
|---|---:|
| Ausências em `flux_err` | `0` |
| Mediana de `flux_err` | `25,8860865` |
| Média de `flux_err` | `26,102194072115385` |
| Desvio padrão de `flux_err` | `0,25819710596197804` |

Isso permite usar `flux_err` em uma likelihood gaussiana preliminar.

A modelagem futura ainda deve avaliar se será necessário incluir um termo de
ruído adicional.

## 6. Pergunta: A Gold Está Pronta Para Um Modelo Bayesiano Preliminar?

Resposta:

```text
Sim, com cautela.
```

A Gold está pronta para um primeiro modelo simples porque:

- tem curva faseada;
- tem janela de trânsito;
- tem fluxo;
- tem incerteza de fluxo;
- não possui ausências em `flux` ou `flux_err` na janela;
- mantém proveniência;
- preserva parâmetros orbitais usados.

Mas a modelagem ainda precisa definir:

- normalização local;
- priors;
- modelo físico;
- likelihood;
- estratégia de amostragem;
- diagnóstico de resíduos;
- diagnóstico de convergência.

## 7. Arquivo de Entrada Para a Próxima Etapa

Usar:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```

Aplicar na etapa de modelagem o filtro preliminar:

```python
abs(phase) <= 0.15
```

Esse filtro não foi aplicado na Gold para preservar a janela inicial ampla e
permitir comparação de janelas.

## 8. Limitações

Limitações da EDA:

- a profundidade visual não é parâmetro físico estimado;
- o binning é apenas visual;
- não há ajuste de trânsito;
- não há inferência;
- não há posterior;
- não há avaliação de ruído correlacionado;
- não há normalização final;
- não há comparação com literatura;
- não há validação residual.

## 9. Decisão Recomendada

Para a próxima etapa, a recomendação objetiva é:

1. carregar `transit_window_lightcurve.csv`;
2. filtrar `abs(phase) <= 0.15`;
3. aplicar uma normalização local simples e documentada;
4. ajustar um modelo bayesiano preliminar;
5. avaliar resíduos, posterior e sensibilidade da janela.

## 10. Frase-Síntese

Uma frase-síntese possível:

```text
A EDA da Gold de HAT-P-7 b confirmou visualmente o trânsito, verificou a
presença de incertezas observacionais em flux_err, identificou que a janela
Gold inicial é ampla para modelagem e recomendou uma janela preliminar de
±0,15 dias em torno da fase zero.
```
