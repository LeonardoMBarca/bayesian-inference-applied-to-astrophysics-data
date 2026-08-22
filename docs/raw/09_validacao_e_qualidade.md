# 09. Validação e Qualidade da Coleta

## Objetivo da validação

A validação final teve como objetivo confirmar que:

- o comando principal funciona;
- as fontes foram processadas;
- os manifestos existem;
- os arquivos locais existem;
- os checksums batem;
- os dados principais foram coletados;
- a documentação e o README descrevem a reprodução.

## Comando principal validado

Comando:

```bash
.venv/bin/python scripts/download_raw_data.py
```

Resultado lógico da execução final:

```text
source_level_failures=0
```

## Validação do manifesto

Arquivos:

```text
data/raw/_manifests/raw_data_manifest.csv
data/raw/_manifests/raw_data_manifest.json
```

Resultado:

```text
manifest_rows: 749
json_rows: 749
missing_local_files: 0
blank_checksums: 0
checksum_mismatches: 0
```

Interpretação:

- todo `local_path` registrado aponta para arquivo existente;
- todo arquivo local registrado tem SHA256;
- nenhum SHA256 divergiu do conteúdo atual.

## Validação de dependências

Foi executado:

```bash
.venv/bin/python -m pip check
```

Resultado:

```text
No broken requirements found.
```

Também foram importadas as bibliotecas principais:

```text
pandas
requests
astropy
astroquery
lightkurve
bs4
lxml
tqdm
```

Resultado:

```text
dependency imports: OK
```

Observações:

- o Lightkurve emitiu warning opcional sobre `oktopus`, relacionado a submódulo não usado nesta etapa;
- o Matplotlib informou cache temporário em `/tmp`, o que não afetou a coleta.

## Validação de estrutura

Diretórios principais presentes:

```text
data/raw/_logs
data/raw/_manifests
data/raw/nasa_exoplanet_archive
data/raw/mast
data/raw/exomast
data/raw/etd_varastro
```

Subestruturas presentes:

```text
data/raw/nasa_exoplanet_archive/pscomppars
data/raw/nasa_exoplanet_archive/ps
data/raw/nasa_exoplanet_archive/manifests
data/raw/mast/lightkurve
data/raw/mast/astroquery
data/raw/mast/manifests
data/raw/exomast/manifests
data/raw/etd_varastro/html_snapshots
data/raw/etd_varastro/extracted_metadata
data/raw/etd_varastro/downloaded_lightcurves
data/raw/etd_varastro/manifests
```

## Contagens finais

| Métrica | Valor |
|---|---:|
| Tamanho aproximado de `data/raw` | 82 MB |
| Arquivos em `data/raw` | 402 |
| Respostas NASA por planeta | 16 |
| Snapshot geral NASA | 1 |
| Tabelas de busca MAST | 24 |
| FITS MAST/Lightkurve | 30 |
| Snapshots HTML ETD | 16 |
| Curvas JSON ETD | 40 |
| JSONs Exo.MAST | 26 |
| Registros no snapshot NASA de planetas em trânsito | 4.653 |

## Validação NASA

Critérios:

- `raw_data_manifest.csv` existe;
- `pscomppars` existe para todos os planetas;
- `ps` existe para todos os planetas;
- snapshot geral existe;
- queries e metadados existem;
- checksums registrados.

Resultado:

- todos os oito planetas têm `pscomppars/response.csv`;
- todos os oito planetas têm `ps/response.csv`;
- snapshot geral existe em `all_transiting_planets_snapshot.csv`;
- schema TAP salvo para `pscomppars` e `ps`;
- checksums válidos.

## Validação MAST

Critérios:

- cada planeta tem busca por Kepler, K2 e TESS;
- cada busca gerou `search_results.csv`;
- downloads respeitaram limite;
- FITS estão registrados no manifesto;
- checksums válidos.

Resultado:

- 24 tabelas de busca;
- 30 FITS;
- K2 sem resultados para todos;
- Kepler com resultados para HAT-P-7 b e TrES-2 b;
- TESS com resultados para todos os planetas.

## Validação Exo.MAST

Critérios:

- cada planeta tem diretório em `data/raw/exomast`;
- cada planeta tem `identifiers.json`;
- cada planeta tem `properties.json`;
- TCEs salvos quando disponíveis;
- notas salvas.

Resultado:

- 26 JSONs;
- todos os planetas têm identificadores e propriedades;
- HAT-P-7 b e TrES-2 b têm Kepler TCEs;
- todos têm TESS TCEs.

## Validação ETD/VarAstro

Critérios:

- HTML salvo;
- JSON de busca salvo;
- página de detalhe salva;
- observações públicas salvas;
- verificação de registros privados;
- curvas JSON limitadas;
- notas e manifestos por planeta.

Resultado:

- 16 HTMLs;
- 8 JSONs de busca;
- 8 JSONs de observações públicas;
- 1.650 observações públicas consolidadas;
- zero registros privados retornados;
- 40 curvas JSON públicas;
- checksums válidos.

## Execução final sem falhas

Na execução final completa:

```text
NASA: finalizada
MAST: finalizada
Exo.MAST: finalizada
ETD/VarAstro: finalizada
source_level_failures: 0
```

## Sobre falhas históricas registradas

O manifesto contém 33 registros `failed`.

Eles são históricos e ocorreram durante:

- tentativa inicial com rede bloqueada;
- exploração inicial do ETD antes da identificação do endpoint público correto;
- tentativa de link HTML que retornou página em vez de arquivo.

Esses registros não invalidam a coleta final. Eles documentam o processo de descoberta e reexecução.

## O que ainda precisa ser validado na Silver

A camada RAW garante presença e rastreabilidade, mas não garante adequação analítica.

Na Silver será necessário:

- ler FITS e validar colunas;
- verificar unidades de tempo;
- padronizar escalas temporais;
- validar flags de qualidade;
- verificar duplicidades;
- separar observações por missão/setor/quarter;
- harmonizar IDs de planeta e estrela;
- avaliar quais curvas são adequadas para modelagem;
- documentar critérios de exclusão.
