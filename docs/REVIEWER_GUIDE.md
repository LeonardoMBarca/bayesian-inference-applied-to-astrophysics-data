# Guia do avaliador

[Voltar ao projeto](../README.md) · [Reprodução e disponibilidade](REPRODUCIBILITY.md)

Este roteiro apresenta o trabalho sem exigir instalação, download de todos os
artefatos ou execução de uma campanha. A fonte canônica é a
[síntese v3](../reports/publication_synthesis/tcc_evidence_v3/REPORT.md), identificada
pelo [índice de evidências](../publication/TCC_EVIDENCE_INDEX.json).

## 1. Entender a pergunta e a contribuição

O objetivo é avaliar a confiabilidade de um fluxo de inferência de parâmetros de
trânsito, combinando observações reais, simulação e verificações computacionais.
A contribuição é a implementação integrada e sua avaliação, não uma nova equação
de trânsito, um novo sampler ou a descoberta de um planeta.

Leia a [metodologia](../reports/publication_synthesis/tcc_evidence_v3/METHODOLOGY.md)
e o [rascunho científico](../reports/publication_synthesis/tcc_evidence_v3/MANUSCRIPT_DRAFT.md).
O rascunho é uma fonte de redação: **não é um artigo aceito nem o Word definitivo
entregue à instituição**.

HAT-P-7 b é a âncora de desenvolvimento exploratório; Kepler-10 b é a âncora
observacional do M5 histórico. A progressão não é treino/teste supervisionado.
Os outros sistemas ampliam os regimes examinados, sem formar uma amostra
probabilística da população de exoplanetas.

## 2. Ler os resultados nas populações corretas

| Evidência | Onde consultar | Pergunta que responde |
|---|---|---|
| Simulações iniciais e confirmatórias | [calibration_metrics.csv](../reports/publication_synthesis/tcc_evidence_v3/calibration_metrics.csv) | Como variam recuperação, largura e cobertura nos regimes testados? |
| Critérios por componente | [gate_counts.csv](../reports/publication_synthesis/tcc_evidence_v3/gate_counts.csv) | O que foi avaliado, aprovado, rejeitado ou invalidado? |
| Comparação externa | [benchmark_comparisons.csv](../reports/publication_synthesis/tcc_evidence_v3/benchmark_comparisons.csv) | As marginais são próximas sob hipóteses comparáveis? |
| Afirmações e suas restrições | [claims.json](../reports/publication_synthesis/tcc_evidence_v3/claims.json) | Qual conclusão os artefatos sustentam? |
| Fontes de tabelas e figuras | [SOURCE_INVENTORY.json](../reports/publication_synthesis/tcc_evidence_v3/SOURCE_INVENTORY.json) | De quais arquivos cada resultado deriva? |

As coortes de **80** e **400** simulações permanecem separadas. Os **24** ajustes
complementares incluem dados pareados e um único conjunto observacional. As
**541** unidades das campanhas concluídas não são um denominador de cobertura.

Um controle bloqueado antes de amostrar não é falha de convergência observada.
Um diagnóstico invalidado por defeito não é evidência de inadequação física.
Os intervalos das campanhas são de caudas iguais; o HDI do baseline histórico
conserva sua denominação. A avaliação com verdades fixas não é SBC.

## 3. Confrontar as conclusões com seus limites

Três resultados ajudam a ler o conjunto:

- **Recuperação condicional:** pequeno viés médio de raio nos regimes de curta
  exposição coexistiu com intervalos conservadores. No regime fraco, houve
  recuperação geométrica inadequada mesmo em muitas execuções aprovadas.
- **Computação versus modelo:** os três novos ajustes locais do benchmark passaram
  na amostragem, mas falharam na avaliação residual temporal. Proximidade com
  `juliet` não resolve uma hipótese de ruído inadequada compartilhada.
- **Controles e portabilidade:** cinco sistemas foram mantidos na avaliação,
  inclusive os desfavoráveis. As ablações preservam contrastes reprovados, mas não
  os transformam em estimativas físicas definitivas.

Consulte [limitações](../reports/publication_synthesis/tcc_evidence_v3/LIMITATIONS.md),
[revisão de calibração](publication/CALIBRATION_REVIEW.md) e
[revisão do complemento](publication/NUMERICAL_COMPLEMENT_V4_REVIEW.md).
M6/GP e validação populacional não são resultados concluídos.

## 4. Inspecionar a implementação e a rastreabilidade

O [modelo físico compartilhado](../src/bayesian_modeling/physical_transit.py)
explicita geometria, priors, exposição e likelihood. A
[inferência de publicação](../src/publication/inference.py) aplica o contrato da
campanha e retém as variáveis necessárias ao condicionamento preditivo.
Os [contadores](../src/publication/gate_accounting.py) separam componentes e
populações; não inferem aprovação do sampler pelo status conjunto.

Os [protocolos](../publication/protocols/) definem os experimentos. As
[tentativas](../artifacts/publication_campaign/) conservam configurações, inputs,
resumos e decisões. O [manifesto do baseline](../publication/baseline/manifest.json)
protege `scientific_003`. Os [testes](../tests/) e o
[workflow de CI](../.github/workflows/ci.yml) permitem examinar as propriedades
verificadas, sem confundir teste aprovado com acurácia física universal.

O exemplo histórico de Kepler-10 b tem [relatório próprio](../reports/bayesian_physical_transit_kepler_10_b_scientific_003_report.md).
Sua aprovação pertence ao contrato daquela execução. A interpretação atual deve
ser lida junto à avaliação ampliada, não somente à tabela histórica favorável.

## 5. Verificar o que está realmente disponível

O código, os relatórios e os artefatos compactos versionados estão públicos.
Os traces completos e certos intermediários grandes não foram disponibilizados
como um arquivo público durável. Há recibos de **restauração local**, que não
atestam uma reexecução independente de toda a pesquisa.

Siga [Reprodução e disponibilidade](REPRODUCIBILITY.md) para distinguir leitura,
verificação de bytes, restauração e nova inferência. Relatórios históricos que
mencionam acesso privado registram o momento do congelamento; não são uma
instrução para procurar outra branch. O acesso público atual não altera seus números.

Materiais acadêmicos administrativos não são evidência do modelo e não devem
ser usados para avaliar a contribuição científica. O manuscrito de submissão
precisa ser obtido do autor na versão aprovada para distribuição, sem dados
pessoais desnecessários.

## Citar e comunicar uma questão

Use [CITATION.cff](../CITATION.cff) e o commit consultado. O snapshot científico
consolidado é `127089538dbf2e233bce0d5e92c3977e115bb86b`; a `main` pode receber
correções documentais sem alterar esse conjunto de resultados.

Para uma questão técnica, indique arquivo, campanha, parâmetro, população e
resultado observado. Siga [CONTRIBUTING.md](../CONTRIBUTING.md). Relatos de
privacidade ou credenciais devem seguir [SECURITY.md](../SECURITY.md), não uma
issue pública com os dados expostos.
