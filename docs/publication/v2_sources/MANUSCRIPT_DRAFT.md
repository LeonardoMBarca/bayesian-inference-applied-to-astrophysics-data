# Confiabilidade sob teste: workflow Bayesiano rastreável de trânsitos

Fonte para reconstrução do TCC/manuscrito, não texto aprovado para submissão.
Resultados quantitativos autoritativos: `REPORT.md`, `calibration_metrics.csv`,
`claims.json` e seus hashes. Tabelas não devem ser digitadas novamente no TCC.

## Resumo

Investigamos sob quais condições um workflow de inferência de trânsitos recupera
parâmetros conhecidos e quantifica a incerteza. Duas coortes de verdades fixas
são analisadas separadamente por auditoria direta dos traces. Implementação
externa publicada, ablations, controles de falha e alvos reais pré-selecionados
testam questões distintas. Há regiões de recuperação útil de raio, intervalos
conservadores, baixa informação geométrica e falha acentuada no regime fraco.
A convergência não basta para adequação preditiva; tampouco o gate garante
recuperação por parâmetro. A contribuição é delimitar esses resultados e
torná-los auditáveis, sem reivindicar calibração universal.

## Introdução e trabalhos relacionados

Um posterior computado não garante computação correta, modelo adequado ou
informação suficiente para os parâmetros de interesse. Métodos anteriores
de Bayesian Workflow, SBC, posterior predictive checking e diagnósticos MCMC
fundamentam essa separação. exoplanet, juliet e allesfitter já oferecem
inferência de trânsitos. Maneage, DataLad e padrões de proveniência astronômica
fundamentam rastreabilidade e reprodução. A matriz de novidade e bibliografia
do repositório delimitam a contribuição de integração/avaliação deste trabalho;
não se afirma prioridade histórica sem evidência.

## Métodos

`METHODOLOGY.md` traz equações, parametrização, unidades e estimandos;
`priors_by_family.json` reproduz as configurações congeladas. Camadas de dados
mantêm segmentos, exposição e origem. IDs distinguem datasets, cenários,
replicates e tentativas; rejeições não geram reseeding seletivo.

As coortes sintéticas medem frequências em verdades fixas, não SBC. As
populações all-numeric e condicionadas são separadas. O benchmark usa um
contrato de comparabilidade, não ajuste para concordar. Controles inválidos
testam detecção de falhas; multi-alvo delimita regimes, não uma população.
Auditoria de bytes e cálculos por implementação independente do agregador
protege a cadeia que liga resultados a claims.

## Resultados

O relatório gerado apresenta todos os jobs/tentativas, todas as frequências,
viés, RMSE, larguras e métricas de informação exploratórias. Figuras e captions
mostram curvas de cobertura e retenção de uma cadeia em alias temporal.
Não se omitem posterior rejeitado, controle que falha ou alvo desfavorável.

O resultado positivo é **delimitado**: desempenho de raio útil em regimes
short específicos e demonstrações auditáveis de classes reais de falha.
O resultado negativo é igualmente central: a geometria no regime pouco
informativo não é recuperada adequadamente apesar de muitos gates históricos
aprovados. O benchmark histórico local não estabelece posterior convergido;
resíduos temporais restringem a interpretação observacional em todos os alvos.

## Discussão

O prior pode governar intervalos quando os dados pouco informam, produzindo
cobertura frequentista condicional inadequada sem bug de código. Intervalos
largos podem incluir a verdade e ainda ser pouco úteis. Trapping em aliases
é uma dificuldade numérica distinta: há penalidade a priori forte, mas o
modelo periódico permite predições semelhantes em modos afastados.

A parametrização padronizada preserva a distribuição física e torna a escala
do inicializador coerente com a do prior. Os testes matemáticos não são prova
de eficácia; novas comparações requerem protocolo e execução próprios. Não
se removem cadeias históricas para produzir concordância com juliet.

A análise temporal usa observações efetivamente selecionadas, separadas por
segmentos e gaps. Correlação fora do trânsito e após remoção linear descritiva
motiva investigação de causas; não autoriza escolher GP como solução provada.
Os critérios de promoção autorizam claims específicos, não um selo universal.

## Reprodutibilidade, limitações e conclusão

`SOURCE_INVENTORY.json` é a lista de fontes para a reconstrução posterior.
`LIMITATIONS.md` explicita dependências, seleção e escopo computacional.
O relatório de fechamento distingue bytes restaurados, métricas recalculadas,
CI remoto e pendências de release pública. Um DOI só pode ser declarado depois
de existir; bundle local não constitui depósito público.

Concluímos que a confiabilidade é uma propriedade testável e limitada pelo
regime, parâmetro e objetivo. O workflow produz evidência sobre essas condições,
incluindo falhas dos próprios gates. Melhoria futura deve ser testada com novos
IDs, sem reescrever os resultados que motivaram a investigação.
