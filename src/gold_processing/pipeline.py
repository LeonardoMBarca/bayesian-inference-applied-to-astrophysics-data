"""Orchestration for the initial GOLD data preparation pipeline."""

from __future__ import annotations

import json
import logging
from typing import Any, Iterable

from .lightcurve_preparation import build_gold_target_datasets
from .manifests import GoldManifest
from .selection import build_gold_selection
from .utils import atomic_write_text, ensure_gold_directories, read_csv, relative_path, setup_logging, utc_now
from .validation import build_gold_validation_outputs


ALL_STEPS = ("selection", "target", "validation", "docs")


def run_pipeline(config: Any, steps: Iterable[str] = ALL_STEPS) -> dict[str, Any]:
    selected_steps = tuple(steps)
    ensure_gold_directories(config)
    logger = setup_logging(config.GOLD_DATA_DIR / "logs" / "build_gold_data.log")
    logger.info("GOLD pipeline started: steps=%s", ",".join(selected_steps))
    manifest = GoldManifest(config)
    results: dict[str, Any] = {}

    try:
        if "selection" in selected_steps:
            results["selection"] = build_gold_selection(
                config=config,
                manifest=manifest,
                logger=logger,
            )
            manifest.flush()
        else:
            results["selection"] = _load_existing_selection(config)

        supported = results["selection"].get(
            "supported", [results["selection"]["selected"]]
        )
        results["targets"] = {}
        results["validations"] = {}
        results["target_docs"] = {}
        for selected in supported:
            slug = selected["selected_planet_slug"]
            ensure_gold_directories(config, slug)
            if "target" in selected_steps:
                results["targets"][slug] = build_gold_target_datasets(
                    config=config,
                    selected=selected,
                    manifest=manifest,
                    logger=logger,
                )
                manifest.flush()
            if "validation" in selected_steps:
                if slug not in results["targets"]:
                    raise ValueError("Validation requires target datasets from the same run.")
                results["validations"][slug] = build_gold_validation_outputs(
                    config=config,
                    selected=selected,
                    target_results=results["targets"][slug],
                    manifest=manifest,
                    logger=logger,
                )
                manifest.flush()
            if "docs" in selected_steps:
                if slug not in results["targets"] or slug not in results["validations"]:
                    raise ValueError("Docs require target and validation outputs from the same run.")
                results["target_docs"][slug] = write_gold_readme(
                    config=config,
                    selected=selected,
                    target_results=results["targets"][slug],
                    validation_results=results["validations"][slug],
                    manifest=manifest,
                    logger=logger,
                )
                manifest.flush()
        primary_slug = results["selection"]["selected"]["selected_planet_slug"]
        if primary_slug in results["targets"]:
            results["target"] = results["targets"][primary_slug]
        if primary_slug in results["validations"]:
            results["validation"] = results["validations"][primary_slug]
        if primary_slug in results["target_docs"]:
            results["docs"] = results["target_docs"][primary_slug]
    finally:
        manifest.flush()

    logger.info("GOLD pipeline finished: manifest_rows=%s", len(manifest.rows))
    return results


def _load_existing_selection(config: Any) -> dict[str, Any]:
    path = config.GOLD_DATA_DIR / "selection" / "selected_gold_target.json"
    selected = json.loads(path.read_text(encoding="utf-8"))
    supported_path = config.GOLD_DATA_DIR / "selection" / "supported_gold_targets.json"
    supported = (
        json.loads(supported_path.read_text(encoding="utf-8"))
        if supported_path.exists()
        else [selected]
    )
    return {"selected": selected, "supported": supported}


def write_gold_readme(
    *,
    config: Any,
    selected: dict[str, Any],
    target_results: dict[str, Any],
    validation_results: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> str:
    slug = selected["selected_planet_slug"]
    path = config.GOLD_DATA_DIR / slug / "docs" / "README_gold.md"
    primary_rows = target_results["primary"]["rows"]
    quality_rows = target_results["quality_filtered"]["rows_after"]
    phase_created = target_results["phase"].get("created", False)
    window_created = target_results["transit_window"].get("created", False)
    content = f"""# Gold segmentada: {selected['selected_planet_name']}

## 1. Objetivo

Esta pasta contém a camada Gold reproduzível do alvo. Ela seleciona a cadência
configurada, preserva identidade de segmento/FITS e tempo de exposição, normaliza
cada segmento pela mediana fora do trânsito e prepara a janela usada pelo M5.

Ela não executa inferência bayesiana.

Data de geração:

```text
{utc_now()}
```

## 2. Planeta Escolhido

```text
{selected['selected_planet_name']}
```

Estrela hospedeira:

```text
{selected['selected_host_star']}
```

Slug:

```text
{slug}
```

## 3. Critério de Seleção

Motivo registrado:

```text
{selected['selection_reason']}
```

Missão escolhida:

```text
{selected['selected_primary_mission']}
```

Fonte de fluxo:

```text
{selected['selected_flux_column']}
```

## 4. Fontes Usadas

Principais entradas Silver:

- `data/silver/catalogs/nasa/pscomppars_selected_planets.csv`;
- `data/silver/lightcurves/mast/{slug}/{selected['selected_primary_mission'].lower()}_lightcurve.csv`;
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

- `data/gold/{slug}/catalogs/reference_parameters.csv`;
- `data/gold/{slug}/catalogs/reference_parameters.json`.

Curvas:

- `data/gold/{slug}/lightcurves/primary_lightcurve.csv`;
- `data/gold/{slug}/lightcurves/primary_lightcurve_quality_filtered.csv`.

Modelagem futura:

- `data/gold/{slug}/modeling/phase_folded_lightcurve.csv`;
- `data/gold/{slug}/modeling/segment_normalized_lightcurve.csv`;
- `data/gold/{slug}/modeling/segment_normalization_diagnostics.csv`;
- `data/gold/{slug}/modeling/dataset_metadata.json`;
- `data/gold/{slug}/modeling/transit_window_lightcurve.csv`.

Validação:

- `data/gold/{slug}/validation/gold_lightcurve_summary.csv`;
- `data/gold/{slug}/validation/gold_data_quality_report.md`.

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
- seleção explícita da cadência `{target_results['primary'].get('cadence_preference', '')}`;
- conversão do `transit_midpoint` NASA para a escala temporal do FITS usando `BJDREFI+BJDREFF`;
- criação de fase orbital;
- normalização por segmento com o método `{config.SEGMENT_NORMALIZATION_METHOD}`;
- preservação de `segment_id`, FITS de origem, quarter/sector/campaign e exposição;
- criação de janela em torno do trânsito.

Resumo:

| Produto | Linhas |
|---|---:|
| Curva primária | {primary_rows} |
| Curva filtrada por qualidade | {quality_rows} |
| Curva faseada | {target_results['phase'].get('rows', 0)} |
| Curva normalizada por segmento | {target_results['segment_normalization'].get('rows', 0)} |
| Janela de trânsito | {target_results['transit_window'].get('rows', 0)} |

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
{target_results['phase'].get('warning', '')}
{target_results['transit_window'].get('warning', '')}
```

## 9. Próximo Passo

Usar como entrada principal para a modelagem bayesiana preliminar:

```text
data/gold/{slug}/modeling/transit_window_lightcurve.csv
```
"""
    atomic_write_text(path, content)
    manifest.add_artifact(
        path=path,
        transformation_type="gold_readme",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(validation_results["summary"], config.PROJECT_ROOT),
        row_count=1,
        column_count=1,
        notes="Target-level GOLD documentation.",
    )
    logger.info("GOLD documentation written: %s", path)
    return relative_path(path, config.PROJECT_ROOT)
