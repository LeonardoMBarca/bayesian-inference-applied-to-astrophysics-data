# 26 - Manifestos, Logs e Validações Gold

## 1. Objetivo

A Gold mantém manifestos, logs e validações para garantir rastreabilidade.

Cada arquivo derivado da Gold deve poder ser associado a:

- fonte Silver;
- fonte RAW, quando aplicável;
- planeta;
- missão;
- transformação;
- quantidade de linhas;
- quantidade de colunas;
- status;
- tamanho;
- SHA256.

## 2. Manifesto Gold

Arquivos:

```text
data/gold/manifests/gold_data_manifest.csv
data/gold/manifests/gold_data_manifest.json
```

O manifesto possui `12` registros, todos com status:

```text
created
```

## 3. Colunas do Manifesto

Colunas:

```text
created_at_utc
gold_layer
planet_name
host_star
planet_slug
source_silver_path
source_raw_path
gold_file_path
gold_file_name
transformation_type
row_count
column_count
status
error_message
sha256
file_size_bytes
notes
```

## 4. Transformações Registradas

Transformações presentes:

```text
gold_candidate_scorecard
selected_gold_target
gold_candidate_report
gold_reference_parameters_csv
gold_reference_parameters_json
gold_primary_lightcurve
gold_primary_lightcurve_quality_filtered
gold_phase_folded_lightcurve
gold_transit_window_lightcurve
gold_lightcurve_summary
gold_data_quality_report
gold_readme
```

## 5. Checksums

Cada arquivo Gold criado tem SHA256 registrado no manifesto.

O checksum permite verificar se um arquivo derivado foi alterado após a
execução. Isso é importante porque a Gold é derivada, mas ainda precisa ser
auditável.

## 6. Log Gold

Arquivo:

```text
data/gold/logs/build_gold_data.log
```

O log registra:

- início da execução;
- etapas chamadas;
- arquivos criados;
- decisões de seleção;
- contagens de linhas;
- warnings de tempo;
- fim da execução.

## 7. Validação Numérica

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv
```

Principais campos:

| Campo | Valor |
|---|---:|
| `rows_primary` | `6.163` |
| `rows_quality_filtered` | `3.909` |
| `rows_phase_folded` | `3.909` |
| `rows_transit_window` | `1.664` |
| `time_min` | `120,53881583872862` |
| `time_max` | `258,46743138637976` |
| `flux_min` | `1027023,6` |
| `flux_max` | `1041324,94` |
| `flux_median` | `1040914,9` |
| `flux_std` | `3530,9448155449695` |
| `flux_err_median` | `25,875484` |
| `quality_zero_count` | `3.909` |
| `quality_nonzero_count` | `2.254` |
| `period_used` | `2,20474` |
| `transit_midpoint_used` | `121,35857200017199` |
| `transit_duration_used` | `3,88216` |

## 8. Relatório de Qualidade

Arquivo:

```text
data/gold/hat_p_7_b/validation/gold_data_quality_report.md
```

Esse relatório resume:

- planeta escolhido;
- missão;
- fonte de fluxo;
- linhas antes/depois do filtro;
- faseamento;
- janela de trânsito;
- warnings;
- recomendação para modelagem futura.

## 9. Warning Principal

Warning registrado:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.
```

Esse warning é esperado e importante. Ele documenta que o tempo central da NASA
foi convertido para a escala temporal da curva Kepler.

## 10. Reexecução

A Gold é derivada. Em caso de necessidade, ela pode ser reconstruída com:

```bash
python scripts/build_gold_data.py
```

Como ela é derivada, sobrescrever saídas Gold em uma reexecução é aceitável,
desde que:

- a RAW não seja alterada;
- a Silver não seja alterada;
- o manifesto seja atualizado;
- os logs registrem a execução.

## 11. Limitações das Validações

As validações Gold não avaliam:

- convergência de modelo;
- qualidade de ajuste físico;
- ruído correlacionado;
- evidência bayesiana;
- comparação com literatura;
- estabilidade de posterior.

Elas apenas conferem a coerência técnica dos artefatos preparados.
