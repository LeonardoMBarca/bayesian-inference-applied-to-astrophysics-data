# Documentação das Análises Exploratórias

Esta pasta documenta análises exploratórias e diagnósticas realizadas após a
criação das camadas RAW, Silver e Gold.

As análises nesta pasta não fazem parte da RAW, Silver ou Gold. Elas leem
artefatos já existentes e produzem saídas em:

```text
notebooks/
reports/
figures/
tables/
```

## Análises Disponíveis

1. [gold_hat_p_7_b](gold_hat_p_7_b/README.md)  
   EDA da Gold de HAT-P-7 b antes da modelagem bayesiana.

## Regra Geral

As análises exploratórias:

- não modificam `data/raw/`;
- não modificam `data/silver/`;
- não modificam `data/gold/`;
- não baixam dados externos;
- não fazem inferência bayesiana;
- não ajustam modelo físico de trânsito;
- não criam resultados científicos finais.

Elas servem para diagnosticar se os artefatos preparados estão adequados para a
próxima etapa.
