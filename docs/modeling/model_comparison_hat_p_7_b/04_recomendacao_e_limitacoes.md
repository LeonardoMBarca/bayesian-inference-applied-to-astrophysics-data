# 04 - Recomendação e Limitações do M4

## 1. Recomendação Principal

Arquivo:

```text
tables/model_comparison/hat_p_7_b/model_recommendation_summary.csv
```

Recomendação:

```text
M3 - primary_preliminary_result
```

Justificativa:

- possui profundidade direta;
- deriva `Rp/Rs`;
- estima duração total aproximada;
- estima ingresso/egresso;
- apresenta diagnósticos MCMC bons;
- tem desempenho preditivo simples competitivo;
- é mais interpretável fisicamente que M2;
- é mais flexível que M1.

## 2. Papel de Cada Modelo

M1:

```text
baseline_reference
```

Uso recomendado:

- demonstrar uma primeira inferência bayesiana transparente;
- servir como comparação mínima;
- mostrar como uma hipótese rígida afeta a profundidade.

M2:

```text
predictive_description
```

Uso recomendado:

- descrever a curva suave de fluxo por fase;
- avaliar incerteza preditiva;
- ilustrar flexibilidade maior que M1;
- não reportar `predicted_depth` como profundidade física final.

M3:

```text
primary_preliminary_result
```

Uso recomendado:

- reportar resultado preliminar principal;
- discutir profundidade, `Rp/Rs`, duração total e ingresso/egresso;
- reforçar que o modelo ainda é aproximado.

## 3. Por que M3, e não M1

M1 é extremamente útil como baseline, mas sua forma box-shaped ignora ingresso
e egresso. Isso torna o modelo simples demais para ser a principal síntese
preliminar do formato observado.

M3 preserva a profundidade direta, mas adiciona estrutura temporal ao trânsito.

## 4. Por que M3, e não M2

M2 descreve bem a curva suave, mas não estima diretamente `Rp/Rs`.

Seu `predicted_depth` é:

```text
baseline_level - min(f_grid)
```

Esse valor é diagnóstico e exploratório. Ele não deve ser tratado como o mesmo
tipo de parâmetro que `depth` em M1 ou M3.

M3, por outro lado, possui `depth` como parâmetro do modelo.

## 5. Limitações do M4

O M4 ainda não faz comparação formal completa porque:

- os traces atuais não possuem grupo `log_likelihood`;
- LOO/WAIC ficaram indisponíveis;
- os modelos têm objetivos diferentes;
- M2 não possui profundidade física direta;
- todos os modelos usam apenas Kepler;
- nenhum modelo incorpora limb darkening;
- nenhum modelo incorpora geometria orbital completa;
- nenhum modelo usa Mandel & Agol.

## 6. Limitação da Recomendação

A recomendação de M3 é:

```text
principal resultado preliminar
```

Não é:

```text
caracterização física final de HAT-P-7 b
```

Essa distinção é importante para o artigo/TCC.

## 7. Próximo Passo

O próximo passo recomendado é avançar para um modelo físico ou semi-físico:

- incorporar limb darkening;
- usar `batman` ou uma formulação Mandel & Agol;
- gerar `log_likelihood` no `InferenceData`;
- comparar modelos com LOO/WAIC quando adequado;
- avaliar integração por tempo de exposição;
- preservar M1, M2 e M3 como referências comparativas.

## 8. Como Usar na Metodologia

Na metodologia, o M4 pode ser descrito como:

```text
uma etapa de comparação posterior aos ajustes bayesianos, destinada a avaliar
como diferentes pressupostos de forma do trânsito alteram a profundidade,
o comportamento preditivo e a interpretabilidade dos parâmetros.
```

Esse texto ajuda a defender que a escolha do resultado preliminar não foi
arbitrária: ela considerou diagnóstico, predição e interpretação física.
