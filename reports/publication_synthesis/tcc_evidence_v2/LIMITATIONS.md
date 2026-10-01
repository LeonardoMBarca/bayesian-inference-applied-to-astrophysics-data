# Limitações e ameaças à validade

- A calibração é condicional a quatro verdades e decisões fixas; fatores
  variam em conjunto. Não é desenho fatorial nem amostra de uma população.
- Gerador e inferência compartilham primitivas físicas. O benchmark externo
  acrescenta outra implementação, mas não fornece verdade astrofísica.
- Período, órbita circular, erro medido e calibração idealizada são conhecidos
  nos controles PUB-02. Incerteza de normalização empírica não foi propagada
  integralmente; não extrapolar sucesso sintético ao processamento real.
- Cobertura alta pode decorrer de intervalos largos; raio, geometria e duração
  têm desempenho distinto. r e r² não são replicações independentes.
- Saídas com falha no sampler estão retidas para auditar o procedimento, não
  como amostras exatas do posterior. Resultados condicionados sofrem seleção.
- Os baselines longos PUB-04 divergiram; efeitos pareados históricos são
  descritivos. Rejeitar um controle inválido não é recuperar parâmetros físicos.
- A inicialização explica um mecanismo possível de aliases; warmup histórico
  ausente impede reconstruir exatamente as trajetórias antigas. A alternativa
  padronizada ainda requer a execução final prospectiva complementar.
- O benchmark usa priors distintos do baseline scientific_003. A concordância
  marginal sob inadequação do sampler/PPC não é validação externa positiva.
- Catálogo condiciona efemérides, máscaras e priors; acordo com ele não é
  validação independente. PDCSAP já incorpora processamento de missão.
- Cinco alvos por regime não estimam uma taxa populacional. Todos permanecem
  na tabela, inclusive rejeitados; não há substituição por conveniência.
- Correlação residual não identifica sua causa. Tendências, offsets,
  variabilidade, forma de trânsito e ruído estocástico podem se confundir.
  Projeções de deslocamento temporal de um template não são medições de TTV.
- Limites normais dos screens são aproximações, não testes perfeitamente
  calibrados. Falha agregada de recuperação restringe a utilidade de gates,
  sem converter cada não cobertura em erro de classificação individual.
- M5 não contém covariância temporal. M6 e calibração com ruído OU não foram
  executados. Sofisticação de GP não é evidência de benefício.
- Ambiente fixado em Python e dependências diretas não fixa cada biblioteca
  nativa/transitiva. CI exato nessas dimensões não é byte-identidade de WSL.
- Bundle local e checkout restaurado demonstram disponibilidade local auditada;
  distribuição pública, direitos de terceiros, revisão de segurança e DOI
  precisam de recibos próprios. Não há autorização implícita de release pública.

## Contribuição e trabalho futuro

A contribuição defensável é a integração e avaliação empírica auditável de
proveniência, inferência e critérios de interpretação, **com seus limites**.
Modelos de trânsito, SBC, checagem Bayesiana, dados endereçados por conteúdo e
proveniência possuem literatura anterior; não se reivindica invenção desses
elementos. A matriz NOVELTY_MATRIX diferencia capacidade verificada de
desconhecida; ausência de documentação encontrada não prova ausência de método.

Prioridades futuras: estudo numérico de parametrização/amostragem já
protocolado; caracterização informacional por parâmetro com validação
prospectiva; causas determinísticas/efemérides nos resíduos; somente então
likelihood correlacionada validada sinteticamente e riscos de absorção de sinal.
