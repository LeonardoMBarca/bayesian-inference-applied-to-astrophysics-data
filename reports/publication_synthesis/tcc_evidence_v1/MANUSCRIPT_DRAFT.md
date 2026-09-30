# Auditando a confiabilidade de um workflow Bayesiano de trânsitos

Status: rascunho de fonte para TCC/manuscrito, posterior aos resultados.
Não é um manuscrito aprovado para submissão. Tabelas completas: [REPORT.md](REPORT.md).
O ledger de afirmações é [claims.json](claims.json).

## Resumo

Investigamos em quais condições um workflow rastreável de inferência de trânsitos
recupera parâmetros e quantifica incerteza. Dois experimentos com verdades fixas
contêm 80 e 400 realizações independentes, analisadas separadamente. O programa
inclui um benchmark publicado independente, intervenções controladas e cinco
sistemas reais pré-selecionados. O inventário contém 517 jobs
e 518 tentativas, inclusive uma tentativa cancelada.
Os resultados mostram recuperação dependente do regime e do parâmetro, com
intervalos conservadores em alguns casos e cobertura 94% de a/Rs de
9/100 no regime menos informativo. As falhas
preservadas demonstram que convergência e gates de adequação não garantem
identificação física. A contribuição é uma avaliação auditável desses limites;
não reivindicamos calibração universal ou superioridade sobre outros fitters.

## 1. Motivação e trabalhos relacionados

A confiabilidade exige identificação de dados, avaliação da computação e
verificação do modelo. SBC (Talts et al.) e Bayesian Workflow (Gelman et al.)
estabelecem parte desse fundamento; não são novidades deste projeto.
`exoplanet`, `juliet` e `allesfitter` já fornecem inferência científica de
trânsitos. A matriz de novidade compara capacidades verificadas e desconhecidas
sem pressupor que ferramentas anteriores careçam de validação ou proveniência.
A contribuição investigada é a integração e avaliação de contratos rastreáveis
de promoção da evidência. Ver `docs/publication/NOVELTY_MATRIX.md` e
`docs/publication/BIBLIOGRAPHY.md` no repositório.

## 2. Modelo e proveniência

O modelo circular usa trânsito com limb darkening quadrático e integração na
exposição. Para observação i:

\[
y_i \sim \mathcal{N}(\mu_i(\theta),\sigma_i^2+s^2),\qquad
\mu_i = c + \Delta t_i^{-1}\int_{t_i-\Delta t_i/2}^{t_i+\Delta t_i/2}
\Delta F(t;\theta)\,dt.
\]

`s` é jitter branco independente. Não há covariância temporal no M5. Os
parâmetros incluem r=Rp/Rs, b, a/Rs, t0 e limb darkening transformado via q1/q2.
A profundidade geométrica é r²; ela difere da profundidade observada sob limb
darkening. A duração T14 segue a geometria circular declarada no protocolo.
Os priors e samplers exatos por família constam nos protocolos congelados, que
são fonte autoritativa e precedem a execução; não se substituem por uma descrição
genérica que esconda diferenças do contrato de benchmark ou dos alvos reais.

Dados públicos percorrem RAW, Silver e Gold com hashes, identidade de segmento,
unidades e exposição. O resultado histórico scientific_003 tem seu próprio
manifest e permanece separado dos novos experimentos.

## 3. Desenho e estimandos

P2 usa quatro regimes com verdades fixas, e não uma amostra do prior: é cobertura
condicional em repetidas realizações do ruído, não SBC. A extensão de 100 novas
realizações por regime foi decidida após observar a coorte de 20; seu protocolo
prospectivo declara N fixo e novos seeds. As coortes não são combinadas.
Vários fatores variam entre regimes; as comparações não isolam efeitos causais
de cadência ou SNR. A geração compartilha primitivas físicas com a inferência,
uma limitação de independência explicitamente reconhecida.

Para cada parâmetro, viés = média das médias posteriores menos a verdade;
RMSE = raiz da média dos erros quadráticos; cobertura = frequência de inclusão
da verdade nos intervalos de caudas iguais. Relatamos 50%, 80% e 94%, larguras,
SD posterior e Wilson95 pontual para as frequências. Falhas, dados ausentes e
rejeições têm denominadores explícitos. Resultados condicionados à aprovação
são selecionados; a taxa coberto-e-aprovado sobre todos os jobs é rendimento
operacional, não calibração de intervalos. Não se infere calibração perfeita
por ausência de discrepância significativa, nem se faz seleção por p-valor.

P3 compara a implementação local e juliet sob contrato de dados/modelo/priors.
P4 inclui exposição, normalização, jitter, prior inadequado, amostragem insuficiente,
identidade inválida e sistemática senoidal. P5 mantém os cinco alvos declarados,
incluindo os rejeitados. Nenhum dos estudos valida desempenho populacional.

## 4. Resultados

Inserir as tabelas e figuras geradas em [REPORT.md](REPORT.md),
[calibration_metrics.csv](calibration_metrics.csv),
[gate_summary.csv](gate_summary.csv),
[ablation_paired_effects.csv](ablation_paired_effects.csv) e
[targets.csv](targets.csv). As captions estão em [captions.json](captions.json);
o inventário exato das fontes e figuras históricas está em
[SOURCE_INVENTORY.json](SOURCE_INVENTORY.json).

A narrativa deve apresentar tanto sobrecobertura quanto subcobertura e viés,
destacar limites de identificação, e manter as falhas do benchmark e de todos
os alvos. Sem convergência local, sem adequação preditiva e com aliases de t0,
a concordância de algumas marginais não constitui validação externa positiva.
A demonstração de sampler aprovado/PPC reprovado é sustentada pelos controles;
efeitos físicos pareados têm interpretação limitada pela divergência dos baselines.

## 5. Discussão e ameaças à validade

O prior Uniform(2,50) de a/Rs tem intervalo central94% [3.44,48.56]; portanto
um posterior sem informação pode excluir uma verdade 3.3 que está no suporte.
Esse exemplo explica por que cobertura condicional ruim não diagnostica sozinha
um bug. Não demonstra quantitativamente que todo o erro observado venha do prior.
Os resultados exigem revisão de claims de recuperação no regime fraco, e futura
avaliação prospectiva de identificação/informação, sem ajustar priors à verdade.

Gates detectam classes de falha, mas não garantem precisão dos parâmetros.
R-hat/ESS não testam adequação da likelihood; PPC global não exclui estrutura
temporal. Diagnósticos de correlação são aproximados e dependem do thinning.
Catálogos usados para condicionar a análise não oferecem validação astrofísica
independente. O conjunto multi-alvo foi escolhido por regimes, não aleatoriamente.

Limitações adicionais: primitivas físicas compartilhadas; verdades fixas;
somente três realizações por ablation; normalização empírica sem propagação
integral de incerteza; período/eccentricidade fixos; modos periódicos de t0;
posteriores rejeitados retidos apenas como diagnóstico; ausência de validação
sob ruído estocástico correlacionado. M6 não foi executado. LOO/WAIC não é usado
para ranquear modelos neste estudo. A extensão GP permanece investigação futura.

## 6. Disponibilidade e reprodução

`python scripts/build_publication_synthesis.py` gera este conjunto sem inferência;
`--check` valida hashes, figuras, textos e dependências das campanhas. Os
protocolos, seeds e fontes seladas permitem auditoria; restaurar os traces e
intermediários externos ainda é requisito de release. Não há DOI ou reprodução
integral limpa declarada. Ver [STORAGE_MANIFEST.json](STORAGE_MANIFEST.json).

## 7. Conclusão sustentada

O estudo produz evidência repetida sobre o desempenho condicional e as limitações
do workflow, preserva resultados negativos e torna auditável a distância entre
convergência, adequação e recuperação física. Os dados não sustentam uma garantia
universal de calibração ou generalização. Qualquer versão futura que modifique
inicialização, priors, likelihood ou critérios deve ser avaliada em novos IDs,
sob protocolo prospectivo, preservando estas coortes como referência.
