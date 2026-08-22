# 43 - Como Usar o M1 na Metodologia

## 1. Função Metodológica

M1 pode ser descrito como o primeiro modelo bayesiano preliminar, usado para
demonstrar a passagem de uma curva Gold para uma distribuição posterior de um
parâmetro astrofísico simplificado.

## 2. Texto Possível

```text
Como primeiro baseline, foi especificado um modelo bayesiano do tipo box
transit para a curva de luz faseada de HAT-P-7 b. O modelo estima uma
profundidade média de trânsito e deriva a razão aproximada Rp/Rs pela relação
Rp/Rs = sqrt(depth).
```

## 3. Pré-processamento

```text
Foram utilizados pontos da janela Gold com abs(phase) <= 0,15, mantendo apenas
pontos com quality igual a zero e removendo observações sem fluxo, sem erro de
fluxo ou com erro não positivo. O fluxo foi normalizado pela mediana de uma
região local de baseline definida por 0,08 <= abs(phase) <= 0,15.
```

## 4. Modelo

```text
Dentro de uma região central fixa, abs(phase) <= 0,05, o modelo assume fluxo
médio baseline - depth. Fora dessa região, assume fluxo médio baseline. A
likelihood é normal, com incerteza efetiva composta pelo erro observacional e
um termo extra de dispersão.
```

## 5. Priors

```text
Foram usados priors fracos e centrados em uma curva normalizada: baseline ~
Normal(1, 0,01), depth ~ HalfNormal(0,02) e extra_sigma ~ HalfNormal(0,005).
```

## 6. Resultado

```text
A execução robusta com NUTS produziu uma profundidade posterior média de
0,00525258, com HDI 94% entre 0,00464576 e 0,00587726. A razão Rp/Rs derivada
teve média posterior de 0,07243869, com HDI 94% entre 0,06815983 e
0,07666328.
```

## 7. Como Mencionar a Execução Operacional Anterior

```text
Uma execução operacional inicial com Metropolis curto foi usada para validar o
pipeline de artefatos, mas seus diagnósticos MCMC foram inadequados. Por isso,
ela foi preservada apenas para rastreabilidade e substituída, para
interpretação do M1, por uma reexecução robusta com NUTS 2000/2000 e quatro
cadeias.
```

## 8. Como Mencionar os Diagnósticos

```text
A reexecução robusta apresentou R-hat máximo de 1,00088086, ESS mínimo de
4553,60020940 e zero divergências, atendendo aos critérios definidos para uso
do M1 como baseline comparativo.
```

## 9. Ponte Para Próximos Modelos

```text
O M1 estabelece um baseline interpretável para comparação posterior. As
próximas etapas devem considerar modelos com maior flexibilidade preditiva e
maior estrutura física, como modelos suaves em fase ou trapezoidais.
```

## 10. O Que Evitar

Evite escrever que:

- M1 caracterizou fisicamente HAT-P-7 b;
- a razão `Rp/Rs` é resultado final;
- o modelo box representa toda a física do trânsito;
- o box transit representa a física completa do trânsito.

## 11. Frase-Síntese

```text
O M1 robusto demonstrou a construção de uma inferência bayesiana preliminar
para a profundidade de trânsito, produzindo distribuições posteriores para
depth e Rp/Rs com diagnósticos MCMC adequados. Ainda assim, por usar um modelo
box-shaped simplificado, ele deve ser tratado como baseline comparativo, não
como caracterização física final de HAT-P-7 b.
```
