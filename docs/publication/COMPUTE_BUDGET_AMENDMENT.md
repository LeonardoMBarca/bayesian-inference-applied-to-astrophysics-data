# Amendment pré-batch: orçamento do TCC

Data: 2026-09-26. Nenhum batch científico final havia começado.

O usuário estabeleceu prazo aproximado de dez dias, prioridade ao TCC e teto de
36 horas de processamento pesado. A campanha será iniciada pelo usuário, fora
da sessão do agente. M6 fica explicitamente adiado; não existe validação de GP.

O draft de P2 previa 100 realizações em seis cenários. O protocolo TCC fixa
20 em cada um dos quatro regimes principais de ruído branco: 80 realizações.
Os dois regimes OU são preservados como cenários adiados, não tentativas finais.
P4 fixa três pares em cada desenho,
30 tentativas, incluindo seis controles de identidade rejeitáveis antes do
sampling. P3 contém dois fits comparáveis; P5 mantém todos os cinco sistemas
pré-selecionados. Total: 117 unidades de trabalho, sem substituir falhas.

A primeira proposta compute-aware com oito OU em cada regime estimava 40,75h.
Antes de congelar qualquer protocolo final, esses 16 trabalhos foram adiados
para preservar P3–P5 no teto de 36h. A estimativa resultante é 31,86h, com margem
aproximada de 4,14h, não uma garantia. Não haverá afirmação de calibração sob
ruído correlacionado a partir desta campanha. P4 mantém o controle de seno
determinístico, explicitamente diferente de ruído estocástico correlacionado.

Essa redução é exclusivamente computacional e anterior aos resultados finais.
Não foi motivada por coverage, convergência ou concordância observada.
Os pilotos `pilot_001` permanecem excluídos: ambos fizeram sampling e falharam
depois por incompatibilidade da API ArviZ, corrigida com teste de regressão.
Tempos totais observados: aproximadamente 187 s (deep_short) e 1078 s
(shallow_short), com 500 tune + 500 draws, quatro chains e contenção de CPU.
Extrapolações não são garantias: compilação e geometria do posterior variam.
O teste de compilador mostrou equivalência numérica local entre os linkers;
`auto` foi mais rápido que `cvm` nesse teste e é usado no protocolo final.

Com n=20, os erros-padrão binomiais em p=.50/.80/.94 são aproximadamente
.112/.089/.053. Os intervalos Wilson95 serão
mostrados; esses tamanhos não demonstram calibração precisa nem equivalência.
Três pares P4 sustentam descrição de efeitos, não estimativas precisas de
sensibilidade/especificidade dos gates. Resultados inconclusivos são possíveis.

O runner preserva a ordem P2→P3→P4→P5, termina o trabalho ativo ao atingir o
orçamento e deixa o restante PLANNED. Um orçamento insuficiente será registrado
como incompletude, nunca como evidência de aprovação. Não há garantia de que
117 unidades terminem em 36h. Aumentar o teto permite retomar; mudar cenários,
replicações ou hipóteses exige novo campaign_id, protocolo e ledger congelado.

Uma campanha futura de paper poderá ampliar n antes de seus resultados, sem
escolher seeds favoráveis nem promover os pilotos atuais a evidência final.
