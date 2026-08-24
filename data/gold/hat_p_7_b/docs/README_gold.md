# Gold Inicial: HAT-P-7 b

## 1. Objetivo

Esta pasta contém a primeira camada Gold do projeto.

A Gold inicial prepara um dataset analítico mínimo para modelagem bayesiana futura, usando exclusivamente tabelas já consolidadas na Silver.

Ela não executa inferência bayesiana.

Data de geração:

```text
2026-08-24T01:15:24+00:00
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
HAT-P-7 b selected because it satisfies the default rule: Kepler available, PDCSAP flux available, orbital period available, and more than 1000 quality==0 rows.
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
- conversão do `transit_midpoint` NASA para a escala temporal do FITS usando `BJDREFI+BJDREFF`;
- criação de fase orbital;
- criação de janela em torno do trânsito.

Resumo:

| Produto | Linhas |
|---|---:|
| Curva primária | 6163 |
| Curva filtrada por qualidade | 3909 |
| Curva faseada | 3909 |
| Janela de trânsito | 1664 |

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
- O fluxo não foi normalizado nesta etapa.
- O filtro de qualidade usa apenas `quality == 0`.
- A seleção de candidato é transparente, mas não é uma métrica astrofísica definitiva.
- A modelagem ainda precisa definir priors, likelihood, modelo físico e diagnóstico posterior.

Warnings:

```text
NASA transit_midpoint converted to FITS time scale using BJD reference 2454833.0 from TIMESYS=TDB;BJDREFI=2454833;BJDREFF=0.0.

```

## 9. Próximo Passo

Usar como entrada principal para a modelagem bayesiana preliminar:

```text
data/gold/hat_p_7_b/modeling/transit_window_lightcurve.csv
```
