# 10. Como Usar Esta Documentação na Metodologia do TCC

## Objetivo deste documento

Este arquivo reorganiza a documentação técnica em uma linguagem mais próxima de metodologia acadêmica.

Ele não é o texto final do TCC. É uma base para escrever a seção metodológica depois.

## Formulação geral da etapa RAW

Uma formulação possível:

> Foi construída uma camada RAW em um datalake local para preservar dados públicos brutos e metadados de coleta relacionados a sistemas planetários em trânsito. A coleta foi implementada em Python, com scripts reexecutáveis, registro de logs, manifestos globais, checksums SHA256 e controle de não sobrescrita. Nesta etapa não foram realizadas limpeza, normalização, faseamento, remoção de outliers, geração de gráficos ou inferência estatística.

## Formulação sobre seleção dos planetas

Uma formulação possível:

> A coleta inicial considerou oito planetas candidatos, escolhidos por sua relevância para estudos de trânsitos e pela disponibilidade esperada de dados públicos: HAT-P-7 b, TrES-2 b, HD 189733 b, HD 209458 b, WASP-12 b, WASP-10 b, WASP-4 b e HAT-P-32 b. Para cada planeta foi definida a respectiva estrela hospedeira, utilizada nas consultas aos arquivos de curvas de luz espaciais.

## Formulação sobre NASA Exoplanet Archive

Uma formulação possível:

> Os parâmetros catalográficos planetários e estelares foram coletados do NASA Exoplanet Archive por meio do endpoint TAP síncrono. Foram consultadas as tabelas `pscomppars` e `ps`, com seleção dinâmica de colunas baseada no esquema disponível no momento da coleta. Para cada planeta, as respostas CSV retornadas pela API foram salvas sem transformação na camada RAW, acompanhadas das queries ADQL, metadados da requisição e checksums SHA256.

Complemento possível:

> Além das consultas individuais por planeta, foi salvo um snapshot da tabela `pscomppars` contendo planetas descobertos por trânsito, com período orbital não nulo e raio planetário ou profundidade de trânsito disponível. Esse snapshot foi preservado como referência bruta para eventual seleção futura de alvos, sem constituir ainda uma camada analítica.

## Formulação sobre MAST/Lightkurve

Uma formulação possível:

> As curvas de luz espaciais foram buscadas no MAST por meio da biblioteca Lightkurve, utilizando a estrela hospedeira como alvo de busca. Para cada planeta foram realizadas buscas independentes nas missões Kepler, K2 e TESS. As tabelas completas de resultados foram preservadas em CSV para rastreabilidade. Para evitar volume excessivo, foi baixado um subconjunto controlado de até três produtos FITS por planeta e missão, priorizando produtos de pipelines oficiais e exposições mais longas. Os arquivos FITS foram preservados em formato original, sem leitura ou transformação analítica na camada RAW.

Complemento possível:

> O fallback com Astroquery foi implementado para cenários de falha do Lightkurve, mas não foi necessário na execução validada, pois as buscas e downloads via Lightkurve foram concluídos.

## Formulação sobre Exo.MAST

Uma formulação possível:

> O Exo.MAST foi utilizado como fonte auxiliar de metadados e identificação. Para cada planeta foram coletados JSONs públicos contendo identificadores, propriedades e listas de TCEs quando disponíveis. Esses arquivos foram preservados sem alteração, servindo como apoio à rastreabilidade entre catálogos, identificadores de missão e produtos observacionais.

## Formulação sobre ETD/VarAstro

Uma formulação possível:

> Para dados terrestres de trânsito, foi consultado o portal ETD/VarAstro. A coleta utilizou páginas públicas e endpoints anônimos consumidos pelo próprio front-end do site, sem login, sem automação de navegador e com delay entre requisições. Para cada planeta foram salvos snapshots HTML, respostas JSON de busca, páginas públicas de detalhe, respostas JSON de observações e até cinco respostas JSON de curvas públicas. Os registros retornados foram verificados quanto ao campo `isPrivate`, e nenhum registro privado foi retornado na coleta validada.

Complemento importante:

> As curvas do ETD/VarAstro salvas nesta etapa são respostas JSON da API pública de visualização do portal, contendo séries fotométricas e metadados associados. Elas não devem ser descritas como os arquivos originais enviados pelos observadores sem validação adicional.

## Formulação sobre manifestos e checksums

Uma formulação possível:

> A rastreabilidade foi garantida por um manifesto global em CSV e JSON, contendo data/hora UTC da coleta, fonte, URL de origem, planeta, estrela hospedeira, missão, tipo de produto, caminho local, status, mensagem de erro, tamanho do arquivo e checksum SHA256. Ao final da validação, todos os arquivos locais registrados no manifesto possuíam checksum preenchido e consistente com o conteúdo em disco.

## Formulação sobre reexecução

Uma formulação possível:

> O pipeline foi desenvolvido para ser reexecutável. Arquivos previamente baixados não são sobrescritos; nesses casos, o evento é registrado como `skipped_existing`. Quando sidecars de queries ou metadados diferem entre execuções, novas versões identificadas por hash são criadas. Falhas pontuais são registradas em log e manifesto, sem interromper a coleta das demais fontes ou planetas.

## Formulação sobre limitações da etapa RAW

Uma formulação possível:

> Por se tratar da camada RAW, os dados foram preservados com mínima intervenção. Assim, inconsistências de esquema, diferenças de unidades, múltiplas referências catalográficas, flags de qualidade, duplicidades e variações entre missões não foram resolvidas nesta etapa. Essas questões serão tratadas em uma futura camada Silver, antes de qualquer modelagem ou inferência bayesiana.

## Formulação sobre ausência de processamento analítico

Uma formulação possível:

> Nenhuma curva de luz foi normalizada, faseada, filtrada, agregada ou modelada nesta etapa. A coleta teve caráter exclusivamente documental e operacional, com foco em preservação, rastreabilidade e reprodutibilidade dos dados públicos brutos.

## Números que podem ser citados

Números da coleta validada:

| Item | Quantidade |
|---|---:|
| Planetas candidatos | 8 |
| Arquivos em `data/raw` | 402 |
| Tamanho aproximado de `data/raw` | 82 MB |
| Registros no manifesto global | 749 |
| FITS MAST/Lightkurve | 30 |
| Curvas JSON ETD/VarAstro | 40 |
| Tabelas de busca MAST | 24 |
| Snapshots HTML ETD | 16 |
| JSONs Exo.MAST | 26 |
| Observações públicas ETD consolidadas | 1.650 |
| Registros privados ETD retornados | 0 |
| Divergências de checksum | 0 |

## Cuidados ao escrever a metodologia

Evite dizer:

- que os dados foram limpos;
- que as curvas foram normalizadas;
- que houve inferência;
- que os JSONs do ETD são necessariamente arquivos originais dos observadores;
- que a seleção Gold já foi feita;
- que HAT-P-7 b já foi definitivamente escolhido como único alvo final.

Prefira dizer:

- que HAT-P-7 b é candidato principal inicial;
- que a camada RAW foi construída para múltiplos planetas;
- que a etapa preserva dados públicos brutos;
- que a seleção analítica será feita depois;
- que a Silver ainda será responsável por padronização e validação.

## Próximos passos metodológicos naturais

Para a camada Silver:

1. Ler FITS e inspecionar HDUs/colunas.
2. Padronizar identificadores de planeta e estrela.
3. Harmonizar escalas de tempo.
4. Selecionar flags de qualidade.
5. Separar curvas por missão, setor, quarter ou campanha.
6. Definir critérios de exclusão.
7. Preparar curvas para análise exploratória.

Para a camada Gold:

1. Escolher planeta-alvo.
2. Definir fonte ou combinação de fontes.
3. Selecionar curvas específicas.
4. Construir dataset analítico final.
5. Preparar entrada para modelagem bayesiana.
