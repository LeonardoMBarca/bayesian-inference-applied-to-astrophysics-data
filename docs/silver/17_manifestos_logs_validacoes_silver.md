# 17. Manifestos, Logs e Validações da Camada Silver

## Objetivo deste documento

Este documento descreve os mecanismos de controle da camada Silver:

- manifesto Silver;
- logs de execução;
- validação do manifesto RAW;
- validações das tabelas Silver;
- checksums;
- reprodutibilidade.

## Manifesto Silver

Arquivos:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/manifests/silver_data_manifest.json
```

Resultado final:

| Métrica | Valor |
|---|---:|
| Registros no manifesto Silver | 26 |
| Registros com status `created` | 26 |
| Registros com status `failed` | 0 |
| Checksums Silver verificados | 26 |
| Divergências de checksum Silver | 0 |
| Arquivos Silver ausentes no manifesto | 0 |

## Colunas do manifesto Silver

| Coluna | Significado |
|---|---|
| `created_at_utc` | Data/hora UTC do registro |
| `silver_layer` | Camada registrada, sempre `silver` |
| `source_raw_manifest_path` | Caminho do manifesto RAW usado |
| `source_raw_path` | Caminho RAW associado, quando aplicável |
| `source_name` | Fonte lógica |
| `planet_name` | Planeta associado, quando aplicável |
| `host_star` | Estrela hospedeira, quando aplicável |
| `mission` | Missão, quando aplicável |
| `raw_file_type` | Tipo do arquivo RAW |
| `silver_file_path` | Caminho do artefato Silver |
| `silver_file_name` | Nome do arquivo Silver |
| `silver_file_type` | Tipo/extensão do arquivo Silver |
| `transformation_type` | Tipo lógico de transformação |
| `row_count` | Número de linhas criadas |
| `column_count` | Número de colunas criadas |
| `status` | Resultado da criação |
| `error_message` | Erro, se houver |
| `sha256` | Checksum SHA256 do arquivo Silver |
| `file_size_bytes` | Tamanho do arquivo Silver |
| `notes` | Observações |

## Tipos de transformação registrados

| Transformação | Quantidade |
|---|---:|
| `mast_fits_to_silver_lightcurve` | 10 |
| `raw_manifest_validation_summary` | 1 |
| `raw_manifest_validation_detail` | 1 |
| `nasa_pscomppars_selected_planets` | 1 |
| `nasa_ps_all_solutions` | 1 |
| `nasa_all_transiting_planets_snapshot` | 1 |
| `exomast_identifiers` | 1 |
| `exomast_properties` | 1 |
| `exomast_tces` | 1 |
| `mast_fits_metadata` | 1 |
| `etd_observations` | 1 |
| `etd_lightcurve_points` | 1 |
| `etd_lightcurve_metadata` | 1 |
| `silver_summary_by_planet` | 1 |
| `silver_mast_quality_summary` | 1 |
| `silver_etd_summary` | 1 |
| `silver_column_presence_report` | 1 |

## Log Silver

Arquivo:

```text
data/silver/logs/build_silver_data.log
```

O log registra:

- início do pipeline;
- etapas executadas;
- validação da RAW;
- processamento NASA;
- processamento Exo.MAST;
- processamento de cada FITS MAST;
- processamento ETD;
- criação de validações;
- escrita da documentação;
- fim do pipeline.

## Validação do manifesto RAW

Arquivos:

```text
data/silver/validation/raw_manifest_summary.csv
data/silver/validation/raw_manifest_validation.json
```

### Resultado validado

| Métrica | Valor |
|---|---:|
| Registros no manifesto RAW | 749 |
| Arquivos RAW locais únicos validados | 399 |
| Arquivos RAW ausentes | 0 |
| Arquivos com checksum verificado | 399 |
| Divergências de checksum RAW | 0 |

### Registros `failed` da RAW

A RAW preserva falhas históricas por rastreabilidade.

A Silver não trata essas falhas como erro fatal.

Regra:

- registros RAW com `status = failed` são aceitos;
- arquivos locais existentes são validados;
- ausência de arquivo em registro histórico de falha não derruba a execução.

## Validações Silver criadas

### `silver_summary_by_planet.csv`

Caminho:

```text
data/silver/validation/silver_summary_by_planet.csv
```

Linhas:

```text
8
```

Resumo por planeta:

- linhas NASA `pscomppars`;
- linhas NASA `ps`;
- quantidade de FITS MAST;
- quantidade de linhas de curvas MAST;
- missões disponíveis;
- quantidade de JSONs Exo.MAST;
- observações ETD;
- curvas JSON ETD;
- pontos ETD.

### `silver_mast_quality_summary.csv`

Caminho:

```text
data/silver/validation/silver_mast_quality_summary.csv
```

Linhas:

```text
10
```

Resumo por planeta e missão:

- FITS processados;
- linhas extraídas;
- linhas com `quality == 0`;
- linhas com `quality != 0`;
- linhas com qualidade ausente;
- contagens não nulas de `PDCSAP_FLUX`;
- contagens não nulas de `SAP_FLUX`;
- intervalo de tempo.

### `silver_etd_summary.csv`

Caminho:

```text
data/silver/validation/silver_etd_summary.csv
```

Linhas:

```text
8
```

Resumo por planeta:

- observações públicas;
- registros privados;
- curvas JSON;
- pontos fotométricos;
- filtros observados;
- DQI mínimo;
- DQI máximo.

### `silver_column_presence_report.csv`

Caminho:

```text
data/silver/validation/silver_column_presence_report.csv
```

Relatório de presença de colunas esperadas em:

- NASA;
- Exo.MAST;
- MAST metadata;
- ETD observações;
- ETD pontos;
- ETD metadata;
- colunas preferidas dos FITS.

## Reprodutibilidade

A Silver é reprodutível porque:

1. Tem configuração versionável em `scripts/silver_data_config.py`.
2. Lê a RAW por manifesto.
3. Usa caminhos locais.
4. Não depende de rede.
5. Usa escrita atômica.
6. Calcula checksums.
7. Registra logs.
8. Gera manifesto próprio.
9. Preserva proveniência linha a linha.

## Como verificar manualmente

Executar:

```bash
python scripts/build_silver_data.py
```

Verificar existência:

```text
data/silver/manifests/silver_data_manifest.csv
data/silver/logs/build_silver_data.log
data/silver/validation/raw_manifest_validation.json
data/silver/validation/silver_summary_by_planet.csv
```

Verificar que a RAW não foi alterada:

```text
Comparar checksums de data/raw antes e depois da execução.
```

Na execução validada, a comparação não apresentou diferenças.

## Interpretação metodológica

Essa etapa demonstra controle de qualidade inicial.

Ela documenta:

- quais arquivos entraram no processamento;
- como a integridade foi conferida;
- quais tabelas foram geradas;
- quais limitações permanecem;
- por que a análise estatística ainda não começou.

Isso ajuda a separar claramente coleta, preparação e modelagem no TCC.
