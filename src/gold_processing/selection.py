"""GOLD candidate selection from SILVER summaries."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

from .manifests import GoldManifest
from .utils import (
    atomic_write_dataframe,
    atomic_write_json,
    atomic_write_text,
    markdown_table,
    path_list,
    read_csv,
    relative_path,
    scalar_to_float,
    to_number,
    utc_now,
)


SCORECARD_COLUMNS = (
    "planet_name",
    "host_star",
    "planet_slug",
    "has_kepler",
    "has_tess",
    "has_k2",
    "kepler_fits_count",
    "tess_fits_count",
    "total_mast_rows",
    "total_quality_zero_rows",
    "total_quality_nonzero_rows",
    "pdcsap_flux_available",
    "sap_flux_available",
    "orbital_period_available",
    "transit_midpoint_available",
    "transit_duration_available",
    "transit_depth_available",
    "etd_observation_count",
    "etd_curve_count",
    "etd_photometry_points",
    "score_availability",
    "score_quality",
    "score_catalog_completeness",
    "score_total",
    "recommended_role",
    "notes",
)


def build_gold_selection(
    *,
    config: Any,
    manifest: GoldManifest,
    logger: logging.Logger,
) -> dict[str, Any]:
    """Build candidate scorecard, markdown report, and selected target JSON."""

    logger.info("Building GOLD candidate selection outputs")
    selection_dir = config.GOLD_DATA_DIR / "selection"
    source_paths = list(config.SILVER_PATHS.values())
    scorecard = _score_candidates(config)
    selected = _select_target(config, scorecard)
    scorecard["recommended_role"] = scorecard.apply(
        lambda row: _recommended_role(config, row, selected),
        axis=1,
    )

    scorecard_path = selection_dir / "gold_candidate_scorecard.csv"
    atomic_write_dataframe(scorecard_path, scorecard.loc[:, SCORECARD_COLUMNS])
    manifest.add_artifact(
        path=scorecard_path,
        transformation_type="gold_candidate_scorecard",
        source_silver_path=path_list(config, source_paths),
        row_count=len(scorecard),
        column_count=len(SCORECARD_COLUMNS),
        notes="Transparent candidate scoring from SILVER summaries.",
    )

    selected_payload = _selected_payload(config, scorecard, selected)
    selected_path = selection_dir / "selected_gold_target.json"
    atomic_write_json(selected_path, selected_payload)
    manifest.add_artifact(
        path=selected_path,
        transformation_type="selected_gold_target",
        planet_name=selected_payload["selected_planet_name"],
        host_star=selected_payload["selected_host_star"],
        planet_slug=selected_payload["selected_planet_slug"],
        source_silver_path=path_list(config, source_paths),
        row_count=1,
        column_count=len(selected_payload),
        notes="Machine-readable GOLD target selection decision.",
    )

    report = _selection_report(config, scorecard, selected_payload)
    report_path = selection_dir / "gold_candidate_report.md"
    atomic_write_text(report_path, report)
    manifest.add_artifact(
        path=report_path,
        transformation_type="gold_candidate_report",
        planet_name=selected_payload["selected_planet_name"],
        host_star=selected_payload["selected_host_star"],
        planet_slug=selected_payload["selected_planet_slug"],
        source_silver_path=path_list(config, source_paths),
        row_count=1,
        column_count=1,
        notes="Human-readable candidate selection report.",
    )

    logger.info(
        "GOLD target selected: %s / %s",
        selected_payload["selected_planet_name"],
        selected_payload["selected_primary_mission"],
    )
    return {
        "scorecard": scorecard,
        "selected": selected_payload,
        "scorecard_path": scorecard_path,
        "selected_path": selected_path,
        "report_path": report_path,
    }


def _score_candidates(config: Any) -> pd.DataFrame:
    summary = read_csv(config.SILVER_PATHS["summary_by_planet"])
    quality = read_csv(config.SILVER_PATHS["mast_quality_summary"])
    metadata = read_csv(config.SILVER_PATHS["mast_fits_metadata"])
    nasa = read_csv(config.SILVER_PATHS["nasa_pscomppars"])
    tces = read_csv(config.SILVER_PATHS["exomast_tces"])
    etd_observations = read_csv(config.SILVER_PATHS["etd_observations"])
    etd_metadata = read_csv(config.SILVER_PATHS["etd_lightcurve_metadata"])

    rows: list[dict[str, Any]] = []
    for _, planet in summary.iterrows():
        planet_name = planet["planet_name"]
        slug = planet["planet_slug"]
        missions = {
            value.strip().lower()
            for value in str(planet.get("mast_missions_available", "")).split("|")
            if value.strip()
        }
        planet_quality = quality[quality["planet_name"] == planet_name].copy()
        planet_metadata = metadata[metadata["planet_slug"] == slug].copy()
        catalog = nasa[nasa["planet_slug"] == slug].head(1)
        planet_tces = tces[tces["planet_slug"] == slug] if "planet_slug" in tces.columns else pd.DataFrame()
        etd_obs = etd_observations[etd_observations["planet_slug"] == slug]
        etd_curves = etd_metadata[etd_metadata["planet_slug"] == slug]

        kepler_fits = _fits_count(planet_metadata, "Kepler")
        tess_fits = _fits_count(planet_metadata, "TESS")
        quality_zero = int(to_number(planet_quality.get("rows_with_quality_zero", pd.Series(dtype=str))).fillna(0).sum())
        quality_nonzero = int(to_number(planet_quality.get("rows_with_quality_nonzero", pd.Series(dtype=str))).fillna(0).sum())
        pdcsap_count = int(to_number(planet_quality.get("pdcsap_flux_non_null_count", pd.Series(dtype=str))).fillna(0).sum())
        sap_count = int(to_number(planet_quality.get("sap_flux_non_null_count", pd.Series(dtype=str))).fillna(0).sum())
        total_rows = int(scalar_to_float(planet.get("mast_lightcurve_rows", 0)) or 0)

        orbital_period_available = _catalog_available(catalog, "orbital_period_days")
        transit_midpoint_available = _catalog_available(catalog, "transit_midpoint")
        transit_duration_available = _catalog_available(catalog, "transit_duration_hours")
        transit_depth_available = _catalog_available(catalog, "transit_depth")

        availability = _availability_score(
            has_kepler="kepler" in missions,
            has_tess="tess" in missions,
            has_k2="k2" in missions,
            total_mast_rows=total_rows,
            etd_observation_count=len(etd_obs),
        )
        quality_score = _quality_score(
            pdcsap_available=pdcsap_count > 0,
            sap_available=sap_count > 0,
            quality_zero=quality_zero,
            quality_nonzero=quality_nonzero,
        )
        catalog_score = (
            (2 if orbital_period_available else 0)
            + (2 if transit_midpoint_available else 0)
            + (1 if transit_duration_available else 0)
            + (1 if transit_depth_available else 0)
        )

        rows.append(
            {
                "planet_name": planet_name,
                "host_star": planet["host_star"],
                "planet_slug": slug,
                "has_kepler": "kepler" in missions,
                "has_tess": "tess" in missions,
                "has_k2": "k2" in missions,
                "kepler_fits_count": kepler_fits,
                "tess_fits_count": tess_fits,
                "total_mast_rows": total_rows,
                "total_quality_zero_rows": quality_zero,
                "total_quality_nonzero_rows": quality_nonzero,
                "pdcsap_flux_available": pdcsap_count > 0,
                "sap_flux_available": sap_count > 0,
                "orbital_period_available": orbital_period_available,
                "transit_midpoint_available": transit_midpoint_available,
                "transit_duration_available": transit_duration_available,
                "transit_depth_available": transit_depth_available,
                "etd_observation_count": len(etd_obs),
                "etd_curve_count": len(etd_curves),
                "etd_photometry_points": int(scalar_to_float(planet.get("etd_lightcurve_point_count", 0)) or 0),
                "score_availability": availability,
                "score_quality": quality_score,
                "score_catalog_completeness": catalog_score,
                "score_total": availability + quality_score + catalog_score,
                "recommended_role": "",
                "notes": _score_notes(
                    "kepler" in missions,
                    "tess" in missions,
                    quality_zero,
                    quality_nonzero,
                    len(planet_tces),
                ),
            }
        )
    return pd.DataFrame(rows).sort_values(
        ["score_total", "has_kepler", "total_quality_zero_rows"],
        ascending=[False, False, False],
    )


def _fits_count(metadata: pd.DataFrame, mission: str) -> int:
    if metadata.empty:
        return 0
    return int((metadata["mission"].astype(str).str.lower() == mission.lower()).sum())


def _catalog_available(catalog: pd.DataFrame, column: str) -> bool:
    if catalog.empty or column not in catalog.columns:
        return False
    return catalog[column].replace("", pd.NA).notna().any()


def _availability_score(
    *,
    has_kepler: bool,
    has_tess: bool,
    has_k2: bool,
    total_mast_rows: int,
    etd_observation_count: int,
) -> int:
    score = 0
    score += 3 if has_kepler else 0
    score += 2 if has_tess else 0
    score += 1 if has_k2 else 0
    score += 1 if total_mast_rows >= 50_000 else 0
    score += 1 if etd_observation_count > 0 else 0
    return score


def _quality_score(
    *,
    pdcsap_available: bool,
    sap_available: bool,
    quality_zero: int,
    quality_nonzero: int,
) -> int:
    score = 0
    score += 2 if pdcsap_available else 0
    score += 1 if sap_available else 0
    total_quality = quality_zero + quality_nonzero
    ratio = quality_zero / total_quality if total_quality else 0.0
    if ratio >= 0.80:
        score += 3
    elif ratio >= 0.60:
        score += 2
    elif ratio > 0:
        score += 1
    if total_quality and (quality_nonzero / total_quality) > 0.30:
        score -= 1
    return max(score, 0)


def _score_notes(
    has_kepler: bool,
    has_tess: bool,
    quality_zero: int,
    quality_nonzero: int,
    tce_rows: int,
) -> str:
    notes = []
    if has_kepler:
        notes.append("Kepler available")
    if has_tess:
        notes.append("TESS available")
    total = quality_zero + quality_nonzero
    if total:
        notes.append(f"quality_zero_ratio={quality_zero / total:.3f}")
    notes.append(f"exomast_tce_rows={tce_rows}")
    return "; ".join(notes)


def _select_target(config: Any, scorecard: pd.DataFrame) -> pd.Series:
    primary = scorecard[scorecard["planet_slug"] == config.PRIMARY_CANDIDATE["planet_slug"]]
    if not primary.empty and _meets_default_target_rule(primary.iloc[0]):
        return primary.iloc[0]
    backup = scorecard[scorecard["planet_slug"] == config.BACKUP_CANDIDATE["planet_slug"]]
    if not backup.empty and _meets_default_target_rule(backup.iloc[0]):
        return backup.iloc[0]
    return scorecard.sort_values("score_total", ascending=False).iloc[0]


def _meets_default_target_rule(row: pd.Series) -> bool:
    return bool(
        row["has_kepler"]
        and row["pdcsap_flux_available"]
        and row["orbital_period_available"]
        and int(row["total_quality_zero_rows"]) >= 1_000
    )


def _recommended_role(config: Any, row: pd.Series, selected: pd.Series) -> str:
    if row["planet_slug"] == selected["planet_slug"]:
        return "primary_candidate"
    if row["planet_slug"] == config.BACKUP_CANDIDATE["planet_slug"] and bool(row["has_kepler"]):
        return "backup_candidate"
    return "reference_only"


def _selected_payload(config: Any, scorecard: pd.DataFrame, selected: pd.Series) -> dict[str, Any]:
    selected_mission = _preferred_mission(config, selected)
    selected_flux = (
        config.PREFERRED_FLUX_COLUMN
        if bool(selected["pdcsap_flux_available"])
        else config.FALLBACK_FLUX_COLUMN
    )
    selected_flux_err = (
        config.PREFERRED_FLUX_ERR_COLUMN
        if selected_flux == config.PREFERRED_FLUX_COLUMN
        else config.FALLBACK_FLUX_ERR_COLUMN
    )
    reason = (
        f"{selected['planet_name']} selected because it satisfies the default rule: "
        "Kepler available, PDCSAP flux available, orbital period available, and "
        "more than 1000 quality==0 rows."
        if _meets_default_target_rule(selected)
        else f"{selected['planet_name']} selected by highest score_total."
    )
    return {
        "selected_planet_name": selected["planet_name"],
        "selected_host_star": selected["host_star"],
        "selected_planet_slug": selected["planet_slug"],
        "selected_primary_mission": selected_mission,
        "selected_flux_column": selected_flux,
        "selected_flux_err_column": selected_flux_err,
        "selection_reason": reason,
        "created_at_utc": utc_now(),
    }


def _preferred_mission(config: Any, selected: pd.Series) -> str:
    for mission in config.PREFERRED_MISSIONS:
        if mission.lower() == "kepler" and bool(selected["has_kepler"]):
            return mission
        if mission.lower() == "tess" and bool(selected["has_tess"]):
            return mission
    return "TESS" if bool(selected["has_tess"]) else "Kepler"


def _selection_report(config: Any, scorecard: pd.DataFrame, selected: dict[str, Any]) -> str:
    summary_columns = [
        "planet_name",
        "has_kepler",
        "has_tess",
        "kepler_fits_count",
        "tess_fits_count",
        "total_mast_rows",
        "total_quality_zero_rows",
        "score_total",
        "recommended_role",
    ]
    return f"""# Relatório de Seleção Gold

## 1. Objetivo

Selecionar um planeta e uma missão principal para a primeira camada Gold do projeto, usando apenas artefatos já consolidados na Silver.

## 2. Fontes Silver Usadas

- `data/silver/validation/silver_summary_by_planet.csv`
- `data/silver/validation/silver_mast_quality_summary.csv`
- `data/silver/lightcurves/mast/mast_fits_metadata.csv`
- `data/silver/catalogs/nasa/pscomppars_selected_planets.csv`
- `data/silver/catalogs/exomast/exomast_tces.csv`
- `data/silver/etd/etd_observations.csv`
- `data/silver/etd/etd_lightcurve_metadata.csv`

## 3. Critérios de Pontuação

Pontuação de disponibilidade:

- +3 se possui Kepler;
- +2 se possui TESS;
- +1 se possui K2;
- +1 se possui ao menos 50.000 linhas MAST;
- +1 se possui observações ETD.

Pontuação de qualidade:

- +2 se `PDCSAP_FLUX` está disponível;
- +1 se `SAP_FLUX` está disponível;
- +3 se a razão `quality == 0` é pelo menos 0,80;
- +2 se a razão `quality == 0` é pelo menos 0,60;
- +1 se há qualquer linha `quality == 0`;
- -1 se mais de 30% das linhas têm `quality != 0`.

Pontuação catalográfica:

- +2 se há período orbital;
- +2 se há tempo de meio trânsito;
- +1 se há duração de trânsito;
- +1 se há profundidade de trânsito.

## 4. Tabela Resumida dos Candidatos

{markdown_table(scorecard, summary_columns)}
## 5. Planeta Escolhido

Planeta selecionado:

```text
{selected['selected_planet_name']}
```

Missão principal selecionada:

```text
{selected['selected_primary_mission']}
```

Fonte de fluxo:

```text
{selected['selected_flux_column']}
```

Justificativa:

```text
{selected['selection_reason']}
```

## 6. Justificativa da Missão

A missão Kepler é preferida quando disponível porque fornece uma série temporal extensa e historicamente adequada para estudos de trânsitos. Para o alvo escolhido, Kepler está disponível na Silver e contém fluxo `PDCSAP_FLUX`.

## 7. Limitações

- A pontuação é simples e transparente, não uma métrica astrofísica definitiva.
- A seleção não avalia ruído instrumental em profundidade.
- A seleção não ajusta modelo de trânsito.
- A seleção não compara parâmetros com literatura.
- A seleção não executa inferência bayesiana.

## 8. Próximos Passos

A próxima etapa poderá usar `data/gold/{selected['selected_planet_slug']}/modeling/transit_window_lightcurve.csv` como entrada para uma modelagem bayesiana preliminar, após revisão das escolhas de normalização, janela temporal e modelo físico.
"""
