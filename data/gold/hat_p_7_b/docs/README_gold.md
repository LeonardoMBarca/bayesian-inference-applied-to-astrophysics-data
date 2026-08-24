# Gold segmentada: HAT-P-7 b

## 1. Objetivo

Esta pasta contém a camada Gold reproduzível do alvo. Ela seleciona a cadência
configurada, preserva identidade de segmento/FITS e tempo de exposição, normaliza
cada segmento pela mediana fora do trânsito e prepara a janela usada pelo M5.

Ela não executa inferência bayesiana.

Data de geração:

```text
2026-08-24T09:44:26+00:00
```

## 2. Planeta Escolhido

```text
HAT-P-7 b
```

Estrela hospedeira:

```text
HAT-P-7
```

Slug:

```text
hat_p_7_b
```

## 3. Critério de Seleção

Motivo registrado:

```text
Supported target included in the reproducible Gold build; scorecard remains the evidence for primary/backup ranking.
```

Missão escolhida:

```text
Kepler
```

Fonte de fluxo:

```text
pdcsap_flux
```

## 4. Fontes Usadas

Principais entradas Silver:

- `data/silver/catalogs/nasa/pscomppars_selected_planets.csv`;
- `data/silver/lightcurves/mast/hat_p_7_b/kepler_lightcurve.csv`;
- `data/silver/validation/silver_summary_by_planet.csv`;
- `data/silver/validation/silver_mast_quality_summary.csv`;
- `data/silver/etd/etd_observations.csv`;
- `data/silver/etd/etd_lightcurve_metadata.csv`.

## 5. Arquivos Criados

Seleção:

- `data/gold/selection/gold_candidate_scorecard.csv`;
- `data/gold/selection/gold_candidate_report.md`;
- `data/gold/selection/selected_gold_target.json`.

Catálogos:

- `data/gold/hat_p_7_b/catalogs/reference_parameters.csv`;
- `data/gold/hat_p_7_b/catalogs/reference_parameters.json`.

Curvas:

- `data/gold/hat_p_7_b/lightcurves/primary_lightcurve.csv`;
- `data/gold/hat_p_7_b/lightcurves/primary_lightcurve_quality_filtered.csv`.

Modelagem futura:

- `data/gold/hat_p_7_b/modeling/phase_folded_lightcurve.csv`;
- `data/gold/hat_p_7_b/modeling/segment_normalized_lightcurve.csv`;
- `data/gold/hat_p_7_b/modeling/segment_normalization_diagnostics.csv`;
- `data/gold/hat_p_7_b/modeling/dataset_metadata.json`;
- `data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv`.

Validação:

- `data/gold/hat_p_7_b/validation/gold_lightcurve_summary.csv`;
- `data/gold/hat_p_7_b/validation/gold_data_quality_report.md`.

Manifesto e log:

- `data/gold/manifests/gold_data_manifest.csv`;
- `data/gold/manifests/gold_data_manifest.json`;
- `data/gold/logs/build_gold_data.log`.

## 6. Transformações Realizadas

Transformações permitidas e realizadas:

- seleção do planeta Gold inicial;
- seleção da missão principal;
- seleção de `PDCSAP_FLUX` como fluxo preferencial;
- remoção de linhas sem `time`;
- remoção de linhas sem fluxo;
- filtro por `quality == 0`;
- seleção explícita da cadência `long`;
- conversão do `transit_midpoint` NASA para a escala temporal do FITS usando `BJDREFI+BJDREFF`;
- criação de fase orbital;
- normalização por segmento com o método `out_of_transit_median`;
- preservação de `segment_id`, FITS de origem, quarter/sector/campaign e exposição;
- criação de janela em torno do trânsito.

Resumo:

| Produto | Linhas |
|---|---:|
| Curva primária | 6163 |
| Curva filtrada por qualidade | 3909 |
| Curva faseada | 3909 |
| Curva normalizada por segmento | 3909 |
| Janela de trânsito | 1027 |

## 7. O Que Não Foi Feito

Não foram feitos:

- inferência bayesiana;
- posterior sampling;
- PyMC;
- ArviZ;
- batman;
- exoplanet;
- Gaussian Process;
- ajuste físico de trânsito;
- comparação com literatura;
- gráficos finais do TCC.

## 8. Limitações

- A janela de trânsito é uma seleção inicial para modelagem futura.
- Não foi aplicado detrending polinomial adicional; a hipótese é o uso de
  `PDCSAP_FLUX` seguido somente da normalização explícita por segmento.
- O filtro de qualidade usa apenas `quality == 0`.
- A seleção de candidato é transparente, mas não é uma métrica astrofísica definitiva.
- A interpretação posterior depende dos gates computacionais, preditivos e científicos do M5.

Warnings:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.

```

## 9. Próximo Passo

Usar como entrada principal para a modelagem bayesiana preliminar:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```
