# 20. Como Usar a Camada Silver na Metodologia

## Objetivo deste documento

Este documento organiza a implementação da Silver em linguagem útil para a futura seção de metodologia do TCC.

Não é o texto final do TCC.

É uma base técnica para explicar:

- como os dados foram preparados;
- como a rastreabilidade foi preservada;
- como a validação foi feita;
- por que a modelagem ainda não aparece nesta etapa.

## Ideia metodológica central

A camada Silver foi construída como etapa intermediária entre coleta bruta e análise final.

Ela transforma dados públicos heterogêneos em tabelas padronizadas, sem alterar o significado científico dos dados observacionais.

Essa separação ajuda a demonstrar que a futura inferência bayesiana será aplicada sobre uma base rastreável e auditável.

## Como descrever a entrada da Silver

A entrada primária foi:

```text
data/raw/_manifests/raw_data_manifest.csv
```

Esse manifesto registra:

- fonte;
- URL ou origem;
- planeta;
- estrela;
- caminho local;
- tipo de arquivo;
- missão;
- produto;
- status;
- checksum;
- tamanho.

Na metodologia, isso pode ser descrito como um controle de proveniência da camada bruta.

## Como descrever a validação inicial

Antes de transformar dados, a Silver validou a RAW.

Foram conferidos:

- existência do manifesto RAW;
- existência dos arquivos locais registrados;
- checksums SHA256;
- contagens por fonte;
- contagens por status;
- contagens por produto;
- contagens por planeta.

Resultado:

- 749 registros no manifesto RAW;
- 399 arquivos locais únicos validados;
- 0 arquivos ausentes;
- 0 divergências de checksum.

Isso sustenta a afirmação de que a camada Silver foi construída a partir de uma RAW íntegra.

## Como descrever NASA

Os CSVs do NASA Exoplanet Archive foram usados para consolidar parâmetros planetários e estelares.

Tabelas usadas:

- `pscomppars`;
- `ps`;
- snapshot geral de planetas em trânsito.

Na Silver:

- `pscomppars` foi padronizada para uma linha por planeta;
- `ps` foi preservada com múltiplas soluções por planeta;
- o snapshot geral foi mantido como contexto.

Decisão importante:

```text
Nenhuma solução da tabela ps foi escolhida como definitiva na Silver.
```

Essa decisão evita antecipar uma escolha científica que pertence à etapa Gold ou à análise.

## Como descrever Exo.MAST

Os JSONs Exo.MAST foram transformados em tabelas por flattening.

Como os esquemas variam, foi preservado:

```text
raw_metadata_json
```

Esse campo permite rastrear o conteúdo original do JSON mesmo quando a estrutura tabular fica incompleta ou muito heterogênea.

Isso pode ser descrito como estratégia conservadora de tabularização.

## Como descrever MAST

Os FITS do MAST foram abertos com `astropy.io.fits`.

Para cada FITS:

1. a HDU tabular de curva de luz foi identificada;
2. colunas preferidas foram extraídas quando presentes;
3. colunas ausentes foram mantidas como ausentes;
4. metadados do header foram registrados;
5. cada linha manteve o caminho do FITS original.

Ponto metodológico essencial:

```text
As flags de qualidade foram preservadas, mas não filtradas.
```

Isso permite que a futura Gold decida critérios de qualidade explicitamente.

## Como descrever ETD

O ETD foi consolidado em duas dimensões:

1. observações de trânsito;
2. pontos fotométricos de curvas públicas.

Foram preservados:

- IDs de observação;
- IDs de trânsito;
- época;
- meio do trânsito;
- duração;
- profundidade;
- DQI;
- filtro;
- observador;
- JSON original compacto.

Ponto metodológico essencial:

```text
As magnitudes foram mantidas como magnitudes. Não houve conversão para fluxo.
```

Isso evita introduzir transformação física antes da definição da Gold.

## Como descrever proveniência

Toda tabela Silver inclui, quando aplicável:

- `planet_name`;
- `host_star`;
- `planet_slug`;
- `source_name`;
- `source_raw_path`;
- `source_raw_sha256`;
- `source_raw_file_name`;
- `silver_created_at_utc`.

Essa estrutura permite rastrear:

```text
linha Silver -> arquivo RAW -> fonte pública original
```

## Como descrever validações finais

Após gerar as tabelas, a Silver criou relatórios:

- resumo por planeta;
- resumo de qualidade MAST;
- resumo ETD;
- presença de colunas.

Esses relatórios permitem justificar a futura escolha do planeta Gold.

## Como justificar HAT-P-7 b e TrES-2 b

Com base apenas na disponibilidade Silver:

- HAT-P-7 b possui Kepler, TESS, NASA, Exo.MAST e ETD;
- TrES-2 b possui Kepler, TESS, NASA, Exo.MAST e ETD;
- os demais planetas possuem TESS, NASA, Exo.MAST e ETD, mas não Kepler;
- nenhum planeta possui K2.

Assim, HAT-P-7 b e TrES-2 b são candidatos fortes para Gold.

HAT-P-7 b permanece como candidato principal inicial do projeto.

## Frases técnicas úteis para metodologia

As frases abaixo são rascunhos técnicos, não texto final.

### Sobre arquitetura

```text
Os dados foram organizados em uma arquitetura local de datalake, com separação explícita entre camada bruta e camada padronizada.
```

### Sobre RAW

```text
A camada RAW preservou os arquivos públicos conforme coletados, incluindo CSVs, JSONs, HTMLs e FITS, acompanhados de manifesto, logs e checksums.
```

### Sobre Silver

```text
A camada Silver foi construída exclusivamente a partir da RAW, sem novos downloads, com o objetivo de padronizar identificadores, tabularizar curvas de luz e consolidar metadados observacionais.
```

### Sobre integridade

```text
Antes da transformação, o manifesto RAW foi validado por existência de arquivos e comparação de checksums SHA256.
```

### Sobre curvas FITS

```text
Os arquivos FITS do MAST foram lidos com astropy.io.fits, preservando valores de tempo, fluxo e flags de qualidade, sem normalização ou filtragem.
```

### Sobre ETD

```text
As curvas terrestres do ETD foram mantidas em magnitude, sem conversão para fluxo, preservando metadados de observação, filtro e DQI.
```

### Sobre limites

```text
A camada Silver não executou modelagem, inferência bayesiana, faseamento orbital ou remoção de outliers; tais decisões foram reservadas para etapas posteriores.
```

## O que não afirmar

Evitar afirmar que:

- a Silver produziu dataset final de modelagem;
- as curvas já estão limpas;
- os fluxos já estão normalizados;
- os dados ETD são os arquivos originais dos observadores;
- uma solução NASA foi escolhida como definitiva;
- HAT-P-7 b foi definitivamente escolhido como Gold.

## Próximos passos metodológicos

Para a Gold, a metodologia poderá descrever:

1. escolha de planeta;
2. escolha de missão;
3. seleção de curvas;
4. critério de qualidade;
5. normalização;
6. faseamento;
7. tratamento de incertezas;
8. modelo físico de trânsito;
9. especificação bayesiana;
10. diagnóstico posterior.

Esses passos ainda não foram implementados.
