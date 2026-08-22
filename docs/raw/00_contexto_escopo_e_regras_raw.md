# 00. Contexto, Escopo e Regras da Camada RAW

## Contexto acadêmico

O projeto de pesquisa se chama:

**Inferência Bayesiana na Estimativa de Parâmetros Astrofísicos sob Incerteza Observacional**

O objetivo geral do TCC é investigar como a inferência bayesiana pode ser aplicada à estimação de parâmetros físicos em sistemas astrofísicos sob incerteza observacional, com ênfase em curvas de luz de trânsitos de exoplanetas.

Esta etapa, porém, não implementa a inferência bayesiana. Ela prepara apenas a base bruta, rastreável e reproduzível de dados públicos.

## Objetivo desta etapa

O objetivo desta etapa foi criar uma camada RAW em um datalake local pequeno, salvo em:

```text
data/raw/
```

A camada RAW foi desenhada para registrar:

- dados brutos retornados por APIs públicas;
- arquivos FITS originais baixados do MAST;
- respostas JSON públicas;
- snapshots HTML de páginas consultadas;
- tabelas de busca;
- queries executadas;
- metadados de coleta;
- logs;
- manifestos;
- checksums SHA256.

## O que foi feito

Foi criado um pipeline local em Python para coletar dados de quatro grupos de fontes:

1. NASA Exoplanet Archive
2. MAST / Lightkurve / Astroquery
3. Exo.MAST
4. ETD / VarAstro

Foram considerados oito planetas candidatos:

| Prioridade | Planeta | Estrela hospedeira | Slug usado em pastas |
|---:|---|---|---|
| 1 | HAT-P-7 b | HAT-P-7 | `hat_p_7_b` |
| 2 | TrES-2 b | TrES-2 | `tres_2_b` |
| 3 | HD 189733 b | HD 189733 | `hd_189733_b` |
| 4 | HD 209458 b | HD 209458 | `hd_209458_b` |
| 5 | WASP-12 b | WASP-12 | `wasp_12_b` |
| 6 | WASP-10 b | WASP-10 | `wasp_10_b` |
| 7 | WASP-4 b | WASP-4 | `wasp_4_b` |
| 8 | HAT-P-32 b | HAT-P-32 | `hat_p_32_b` |

## O que não foi feito

Por desenho metodológico, esta etapa não faz:

- criação de `data/silver`;
- criação de `data/gold`;
- criação de `data/processed`;
- limpeza de dados;
- normalização de curvas de luz;
- remoção de outliers;
- faseamento;
- transformação estatística;
- geração de gráficos;
- modelagem física;
- inferência bayesiana;
- preenchimento de valores ausentes;
- criação de dados sintéticos;
- estimativa de parâmetros;
- escrita do texto final do TCC.

## Princípio RAW adotado

O princípio adotado foi:

> salvar o que a fonte pública retornou, registrar como foi obtido, e evitar modificar o conteúdo bruto.

Isso significa que:

- CSVs do NASA TAP foram salvos como retornados pelo endpoint;
- FITS do MAST foram salvos como produtos originais baixados pelo Lightkurve;
- JSONs de Exo.MAST foram salvos sem alteração;
- HTMLs do ETD/VarAstro foram salvos como snapshots públicos;
- JSONs de curva do ETD/VarAstro foram salvos como respostas públicas da API de visualização;
- extrações tabulares auxiliares foram salvas separadamente e marcadas como metadados extraídos.

## Estrutura RAW desejada e criada

A estrutura principal criada foi:

```text
data/
  raw/
    nasa_exoplanet_archive/
      pscomppars/
      ps/
      manifests/
    mast/
      lightkurve/
      astroquery/
      manifests/
    exomast/
      manifests/
    etd_varastro/
      html_snapshots/
      extracted_metadata/
      downloaded_lightcurves/
      manifests/
    _manifests/
    _logs/
```

Durante uma revisão posterior, três CSVs manuais antigos que ficavam soltos na raiz de `data/raw` foram removidos.

Esses arquivos:

- não estavam registrados no manifesto RAW;
- não eram usados pela Silver;
- não eram usados pela Gold;
- não seguiam a estrutura padronizada por fonte;
- haviam sido baixados manualmente antes da definição do pipeline.

A coleta estruturada considerada para metodologia é a que está organizada nas subpastas por fonte e registrada em:

```text
data/raw/_manifests/raw_data_manifest.csv
```

## Política de não sobrescrita

O pipeline evita sobrescrever artefatos existentes.

Quando um arquivo bruto já existe:

- ele é mantido;
- a coleta registra `skipped_existing`;
- o checksum do arquivo existente é registrado novamente no manifesto;
- quando um sidecar de metadados ou query difere de uma tentativa anterior, é criado um arquivo versionado por hash.

Exemplo de arquivos versionados por hash:

```text
query_query_b819ea7b4acd.sql
metadata_query_6a5ddfbed4d8.json
observations_api_a469dcaa60ba.csv
notes_api_ac5e86d3e2c2.md
```

Essa política mantém a rastreabilidade de tentativas anteriores sem apagar o histórico.
