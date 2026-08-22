"""Validation and documentation for GOLD target datasets."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from .manifests import GoldManifest
from .utils import atomic_write_dataframe, atomic_write_text, markdown_table, read_csv, relative_path, scalar_to_float, to_number


SUMMARY_COLUMNS = (
    "planet_name",
    "mission",
    "rows_primary",
    "rows_quality_filtered",
    "rows_phase_folded",
    "rows_transit_window",
    "time_min",
    "time_max",
    "flux_min",
    "flux_max",
    "flux_median",
    "flux_std",
    "flux_err_median",
    "quality_zero_count",
    "quality_nonzero_count",
    "selected_flux_source",
    "period_used",
    "transit_midpoint_used",
    "transit_duration_used",
    "warnings",
)


def build_gold_validation_outputs(
    *,
    config: Any,
    selected: dict[str, Any],
    target_results: dict[str, Any],
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Path]:
    """Write GOLD validation CSV and markdown quality report."""

    slug = selected["selected_planet_slug"]
    validation_dir = config.GOLD_DATA_DIR / slug / "validation"
    primary = read_csv(target_results["primary"]["path"])
    quality = read_csv(target_results["quality_filtered"]["path"])
    phase_result = target_results["phase"]
    window_result = target_results["transit_window"]
    phase = read_csv(phase_result["path"]) if phase_result.get("created") else pd.DataFrame()
    window = read_csv(window_result["path"]) if window_result.get("created") else pd.DataFrame()
    reference = target_results["reference"]

    flux = to_number(primary["flux"])
    flux_err = to_number(primary["flux_err"])
    quality_numeric = to_number(primary["quality"])
    warnings = _warnings(phase_result, window_result)

    summary = pd.DataFrame(
        [
            {
                "planet_name": selected["selected_planet_name"],
                "mission": selected["selected_primary_mission"],
                "rows_primary": len(primary),
                "rows_quality_filtered": len(quality),
                "rows_phase_folded": len(phase),
                "rows_transit_window": len(window),
                "time_min": to_number(primary["time"]).min(),
                "time_max": to_number(primary["time"]).max(),
                "flux_min": flux.min(),
                "flux_max": flux.max(),
                "flux_median": flux.median(),
                "flux_std": flux.std(),
                "flux_err_median": flux_err.median(),
                "quality_zero_count": int((quality_numeric == config.QUALITY_GOOD_VALUE).sum()),
                "quality_nonzero_count": int(((quality_numeric != config.QUALITY_GOOD_VALUE) & quality_numeric.notna()).sum()),
                "selected_flux_source": selected["selected_flux_column"],
                "period_used": scalar_to_float(reference.iloc[0].get("orbital_period_days")),
                "transit_midpoint_used": phase_result.get("transit_midpoint_used", ""),
                "transit_duration_used": scalar_to_float(reference.iloc[0].get("transit_duration_hours")),
                "warnings": warnings,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )
    summary_path = validation_dir / "gold_lightcurve_summary.csv"
    atomic_write_dataframe(summary_path, summary)
    manifest.add_artifact(
        path=summary_path,
        transformation_type="gold_lightcurve_summary",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(target_results["primary"]["path"], config.PROJECT_ROOT),
        row_count=len(summary),
        column_count=len(summary.columns),
        notes="Numerical summary of initial GOLD lightcurve products.",
    )

    report_path = validation_dir / "gold_data_quality_report.md"
    atomic_write_text(
        report_path,
        _quality_report(config, selected, summary, target_results),
    )
    manifest.add_artifact(
        path=report_path,
        transformation_type="gold_data_quality_report",
        planet_name=selected["selected_planet_name"],
        host_star=selected["selected_host_star"],
        planet_slug=slug,
        source_silver_path=relative_path(summary_path, config.PROJECT_ROOT),
        row_count=1,
        column_count=1,
        notes="Human-readable GOLD data quality report.",
    )
    logger.info("GOLD validation outputs written for %s", slug)
    return {"summary": summary_path, "quality_report": report_path}


def _warnings(phase_result: dict[str, Any], window_result: dict[str, Any]) -> str:
    warnings = []
    for result in (phase_result, window_result):
        warning = result.get("warning", "")
        if warning:
            warnings.append(warning)
    return " | ".join(warnings)


def _quality_report(
    config: Any,
    selected: dict[str, Any],
    summary: pd.DataFrame,
    target_results: dict[str, Any],
) -> str:
    row = summary.iloc[0].to_dict()
    return f"""# Relatório de Qualidade da Gold Inicial

## 1. Planeta Escolhido

```text
{selected['selected_planet_name']}
```

## 2. Missão Escolhida

```text
{selected['selected_primary_mission']}
```

Kepler foi escolhido por estar disponível para o planeta selecionado e por ser a primeira missão na ordem de preferência configurada.

## 3. Fonte do Fluxo

Fluxo selecionado:

```text
{selected['selected_flux_column']}
```

Erro de fluxo selecionado:

```text
{selected['selected_flux_err_column']}
```

Política:

```text
{config.NORMALIZATION_POLICY}
```

## 4. Quantidade de Linhas

{markdown_table(summary, list(summary.columns))}
## 5. Filtros Aplicados

Foram aplicadas somente transformações mínimas:

- seleção de colunas relevantes;
- remoção de linhas sem `time`;
- remoção de linhas sem fluxo;
- filtro `quality == {config.QUALITY_GOOD_VALUE}` na curva filtrada;
- criação de fase orbital quando a escala temporal foi reconciliada;
- seleção de janela em torno do trânsito.

Não houve normalização de fluxo.

## 6. Problemas de Tempo e Fase

Warnings registrados:

```text
{row.get('warnings', '')}
```

## 7. Limitações

- A Gold inicial ainda não executa modelagem física.
- A Gold inicial ainda não executa inferência bayesiana.
- A Gold inicial não escolhe modelo de ruído.
- A Gold inicial não compara resultados com literatura.
- A janela de trânsito é uma seleção operacional inicial, não um ajuste.

## 8. Recomendação Para Modelagem

Usar como entrada principal:

```text
data/gold/{selected['selected_planet_slug']}/modeling/transit_window_lightcurve.csv
```

Antes da modelagem bayesiana, revisar:

- normalização;
- tratamento de incertezas;
- escolha do modelo físico;
- priors;
- diagnóstico de qualidade da curva.
"""
