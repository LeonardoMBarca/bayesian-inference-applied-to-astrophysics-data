# Metodologia — fonte da revisão v2

Esta fonte descreve contratos históricos e auditorias posteriores separadamente.
Os priors e configurações específicos por família são extraídos para
`priors_by_family.json`; cada protocolo original é imutável e prevalece sobre
qualquer resumo textual. Nenhum prior foi ajustado à verdade simulada ou à
concordância com catálogo depois dos resultados.

## Modelo e unidades

Para tempo relativo em dias, fluxo relativo y e incerteza conhecida sigma:

\[
y_i \mid \theta,s \sim N(\mu_i(\theta),\sigma_i^2+s^2),
\qquad
\mu_i=B+\frac{1}{\Delta t_i}\int_{t_i-\Delta t_i/2}^{t_i+\Delta t_i/2}
\Delta F(u;r,b,a,q_1,q_2,t_0,P)\,du.
\]

O segundo argumento da Normal na equação é a **variância**. No código, o
argumento sigma é sua raiz quadrada. s é jitter branco independente, não GP.
P e eccentricidade circular são fixos. r=Rp/Rs, a=a/Rs; b entre0 e1 não cobre
todo trânsito grazing possível. Limb darkening quadrático usa a transformação
u1=2sqrt(q1)q2 e u2=sqrt(q1)(1−2q2), com q1,q2 uniformes independentes.
Exposição é convertida de segundos para dias e integrada pelo modelo.

Profundidade geométrica d=r² não é necessariamente a profundidade observada
sob limb darkening. Duração de contato circular:

\[
T_{14}=\frac{P}{\pi}\arcsin\sqrt{\frac{(1+r)^2-b^2}{a^2-b^2}}.
\]

No PUB-02 o raio tem LogNormal(log(0.04),0.9), sem usar o raio verdadeiro de
cada regime; no benchmark há Uniform(0.001,0.2), diferente de scientific_003.
Baseline N(1,0.02), t0 N(0,0.025dia), a Uniform(2,50) e b Uniform(0,1)
fazem parte dos contratos de publicação. Jitter é HalfNormal com escala
max(5×mediana do erro medido,0.0005). PUB-04 altera somente os itens
declarados por intervenção; o prior patológico é um controle, não recomendado.
Não substituir a lista exata por uma descrição genérica do M5 histórico.

## Estimandos de recuperação

Para replicate j, verdade fixa theta*, média posterior m_j, SD s_j e ETI
[l_j(alpha),u_j(alpha)], o viés é média(m_j−theta*), RMSE é
sqrt(média((m_j−theta*)²)), e cobertura é média(1[l_j≤theta*≤u_j]).
Viés absoluto |viés| não é MAE=média(|m_j−theta*|); ambos são registrados.
Viés relativo é indefinido quando a verdade é zero. Largura é u_j−l_j.

As frequências usam intervalos Wilson95 pontuais e níveis ETI50/80/94.
Os experimentos têm verdades fixas e realizam novamente o ruído: isto não é
SBC com parâmetros sorteados do prior. Não há garantia frequentista nominal
para cada verdade fixa. Pouca informação, seleção pelo gate e erro numérico
podem alterar as frequências por mecanismos distintos.

São três populações explícitas: todas as saídas numéricas, somente aquelas
que passam o sampler e somente aquelas que passam o gate conjunto. Falhas
sem posterior ficam indisponíveis, não como não cobertura medida. Rejeitados
numéricos permanecem na primeira população com ressalva de inexatidão.
Coberto-e-aprovado/todos os declarados é rendimento operacional, não cobertura.
As coortes inicial e confirmatória não são combinadas; a decisão de estender
veio após conhecer a inicial e está declarada no protocolo prospectivo.

## Avaliação por escopo, não certificado universal

A revisão v2 conserva a decisão histórica e avalia dimensões separadas:
integridade dos bytes/proveniência, computação, predição, escala física,
informação por parâmetro e afirmações autorizadas. Razão SD posterior/prior
é exploratória; não demonstra identificabilidade nem gera cutoff de aprovação.
Informação futura exigirá protocolo prospectivo, avaliação em controles
conhecidos e diagnóstico que não dependa da verdade para dados observacionais.

R-hat, ESS, divergências e BFMI investigam computação, não adequação física.
PPC global de observações não é cobertura dos parâmetros. O screen temporal
usa pares ordenados dentro de segmentos com gaps filtrados; após thinning,
lag1 não significa necessariamente a cadência instrumental e a referência
normal é aproximada para resíduos ajustados.

## Parametrização alternativa de t0

A alternativa opt-in usa z~N(0,1), t0=sigma_t z. Logo
log p_z(z,y)=log p_t(t0,y)+log(sigma_t), com dt0/dz=sigma_t.
A likelihood nos mesmos parâmetros físicos é idêntica; o gradiente em z
é sigma_t vezes o gradiente em t0. Testes numéricos verificam essas relações
em pontos centrais e aliases. O default direto e a saída t0 em dias permanecem.

O inicializador jitter+adapt_diag aplica jitter uniforme em coordenadas não
restritas. Para Normal direto, isso ocorre em dias; para z, em unidades de
SD a priori. A fonte PyMC instalada é registrada no diagnóstico. A equivalência
da densidade não prova melhoria de desempenho: o estudo complementar deve
executar sob novo protocolo, preservar todos os seeds e manter os gates.

## Auditoria e reprodução

Dados RAW não podem ser convertidos pelo Git se têm identidade por bytes.
A correção restaura blobs a cópias históricas com SHA e tamanho já fixados;
não recalcula checksums de origem para aceitar uma corrupção.
O arquivo externo local completa dependências explicitamente tipadas:
RAW, preparação, Silver/Gold, input efetivo, configuração, resultados/traces,
protocolos, tabelas e figuras. Código histórico é resolvido pelo commit/blob,
não confundido com o gerador atual. Restauração exata não é nova execução
MCMC nem comprovação de reprodução numérica em outro ambiente.
