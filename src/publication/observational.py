"""Isolated, target-safe observational preparation for a frozen publication study.

This adapter reuses the existing FITS-to-Silver, phase, segment normalization,
Gold identity and M5 deterministic thinning primitives. It never invokes the
repository-global pipelines and never writes to historical RAW/Silver/Gold.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from astropy.io import fits

from gold_processing.lightcurve_preparation import (
    build_gold_dataset_signature,
    construct_centered_phase,
    dataset_id_from_signature,
    normalize_segments_dataframe,
)
from project_config import TargetConfig
from silver_processing import config as silver_config
from silver_processing.lightcurves_mast import _extract_one_fits


def _hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _safe_identifier(value: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[a-z][a-z0-9_]{0,79}", value) is None:
        raise ValueError(f"Unsafe publication target/run identifier: {value!r}")
    return value


def target_registry(protocol: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Resolve the declared target universe; never select on posterior status."""
    if protocol.get("experiment_id") != "PUB-05":
        raise ValueError("Expected PUB-05 observational protocol")
    entries = protocol.get("targets", [])
    registry: dict[str, dict[str, Any]] = {}
    for entry in entries:
        target = TargetConfig(**entry["config"])
        slug = _safe_identifier(target.planet_slug)
        if slug in registry:
            raise ValueError(f"Duplicate selected target: {slug}")
        if target.orbital_period_days <= 0 or not np.isfinite(target.transit_midpoint_bjd):
            raise ValueError("Invalid target ephemeris")
        if not (0 < target.transit_duration_days < 2 * target.phase_window_days < target.orbital_period_days):
            raise ValueError("Duration/window/period ordering is inconsistent")
        if not entry.get("selection_role") or not entry.get("source_references"):
            raise ValueError("Every target needs selection rationale and authoritative sources")
        registry[slug] = dict(entry)
    expected = protocol.get("declared_target_ids", [])
    if len(expected) != len(set(expected)) or set(expected) != set(registry):
        raise ValueError("Target-selection registry must account for every declared system exactly once")
    if not {"hat_p_7_b", "kepler_10_b"}.issubset(registry):
        raise ValueError("The two protected anchor targets must remain in the selection")
    if len(registry) < 5 and not protocol.get("pre_result_smaller_set_justification"):
        raise ValueError("Fewer than five targets requires an explicit pre-result justification")
    return registry


def target_outcome_table(protocol: Mapping[str, Any], outcomes: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Include all selected systems, including failed/missing observations."""
    registry = target_registry(protocol)
    indexed = {}
    for outcome in outcomes:
        slug = outcome.get("target_id")
        if slug not in registry or slug in indexed:
            raise ValueError("Unknown or duplicate target outcome")
        indexed[slug] = dict(outcome)
    return [
        {"target_id": slug, "selection_role": registry[slug]["selection_role"],
         **indexed.get(slug, {"status": "missing", "scientifically_interpretable": False})}
        for slug in protocol["declared_target_ids"]
    ]


def _verify_source(root: Path, entry: Mapping[str, Any], target_entry: Mapping[str, Any]) -> tuple[Path, dict[str, Any]]:
    relative = entry.get("path", "")
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise ValueError("Source paths must be repository-relative POSIX paths")
    source = (root / relative).resolve()
    if not source.is_relative_to(root) or Path(relative).is_absolute():
        raise ValueError("Source path escapes repository")
    checksum = entry.get("sha256")
    if not isinstance(checksum, str) or re.fullmatch(r"[0-9a-f]{64}", checksum) is None:
        raise ValueError("Every source requires a frozen valid SHA-256 before preparation")
    if _hash(source) != checksum:
        raise ValueError(f"Source checksum mismatch: {relative}")
    with fits.open(source, memmap=True) as hdul:
        primary, table = hdul[0].header, hdul[1].header
        archive = target_entry["archive_identity"]
        if str(primary.get(archive["header_key"], table.get(archive["header_key"], ""))) != str(archive["value"]):
            raise ValueError(f"FITS target identity mismatch: {relative}")
        mission = target_entry["config"]["mission"]
        if str(primary.get("TELESCOP", "")).lower() != mission.lower():
            raise ValueError("FITS mission identity mismatch")
        system = table.get("TIMESYS", primary.get("TIMESYS"))
        unit = table.get("TIMEUNIT", primary.get("TIMEUNIT"))
        bjd_reference = table.get("BJDREFI", primary.get("BJDREFI"))
        bjd_fraction = table.get("BJDREFF", primary.get("BJDREFF", 0.0))
        if system != "TDB" or unit not in {"d", "day", "days"} or bjd_reference is None:
            raise ValueError("Require an explicit BJD/TDB day time convention")
        bjd_reference = float(bjd_reference) + float(bjd_fraction)
        if bjd_reference != float(target_entry["time_reference_bjd"]):
            raise ValueError("Unexpected BJD reference for selected target")
        info = {"timesys": system, "time_unit": unit, "bjd_reference": bjd_reference}
    return source, info


def prepare_target(
    root: Path, protocol: Mapping[str, Any], target_slug: str, run_id: str,
    *, allow_draft: bool = False,
) -> dict[str, Any]:
    """Prepare one immutable publication dataset; preserve failure artifacts.

    Final use requires a FROZEN protocol. ``allow_draft`` exists for fixture/pilot
    engineering only and labels the output PILOT. No network request is made.
    A fresh output directory is atomically reserved; existing runs always fail.
    """
    root = root.resolve()
    registry = target_registry(protocol)
    if target_slug not in registry:
        raise ValueError(f"Undeclared target {target_slug!r}")
    _safe_identifier(run_id)
    if protocol.get("protocol_status") != "FROZEN" and not allow_draft:
        raise ValueError("Final data preparation requires a FROZEN protocol")
    target_entry = registry[target_slug]
    target = TargetConfig(**target_entry["config"])
    output = root / "publication" / "observational" / "PUB-05" / target_slug / run_id
    if not output.resolve().is_relative_to(root / "publication"):
        raise ValueError("Publication output escaped its isolated namespace")
    output.mkdir(parents=True, exist_ok=False)
    manifest: dict[str, Any] = {
        "schema_version": "publication-observational-v1", "experiment_id": "PUB-05",
        "target_id": target_slug, "preparation_id": run_id,
        "purpose": "PILOT" if allow_draft else "FINAL", "status": "running",
        "protocol_sha256": _digest(protocol), "target_config": asdict(target),
        "target_config_sha256": _digest(target_entry), "source_artifacts": [],
        "declared_source_artifacts": target_entry.get("sources", []),
        "output_directory": output.relative_to(root).as_posix(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    try:
        sources = target_entry.get("sources", [])
        if not sources or len({entry.get("path") for entry in sources}) != len(sources):
            raise ValueError("Nonempty unique preselected FITS source list required")
        if len(sources) != target_entry["expected_source_count"]:
            raise ValueError("Missing selected FITS products; do not silently omit segments")
        frames, metadata = [], []
        for source_entry in sources:
            source, time_info = _verify_source(root, source_entry, target_entry)
            raw_info = {
                "source_name": "MAST", "source_raw_path": source_entry["path"],
                "source_raw_sha256": source_entry["sha256"], "source_raw_file_name": source.name,
            }
            frame, fits_metadata = _extract_one_fits(
                config=silver_config, path=source, planet=target.pipeline_dict(),
                mission=target.mission, mission_slug=target.mission.lower(), raw_info=raw_info,
                created_at=manifest["created_at_utc"],
            )
            # FITS numerical arrays are big-endian. The normal Silver pipeline
            # serializes/reloads CSV before Gold; this in-memory adapter must
            # explicitly convert byte order before pandas row selection.
            frame = pd.DataFrame({
                column: np.asarray(series).astype(np.asarray(series).dtype.newbyteorder("="), copy=False)
                for column, series in frame.items()
            })
            frame["source_row_index"] = np.arange(len(frame))
            frame["source_fits_sha256"] = source_entry["sha256"]
            frame["segment_id"] = f"{target_slug}:{source.name}"
            frame["phase"] = construct_centered_phase(
                pd.to_numeric(frame.time, errors="coerce"),
                orbital_period_days=target.orbital_period_days,
                transit_midpoint_in_time_scale=target.transit_midpoint_bjd - time_info["bjd_reference"],
            )
            frames.append(frame)
            metadata.append(fits_metadata)
            manifest["source_artifacts"].append({**source_entry, **time_info, "rows": len(frame)})
        silver = pd.concat(frames, ignore_index=True)
        silver.to_csv(output / "silver_lightcurve.csv", index=False, float_format="%.17g", lineterminator="\n")
        pd.DataFrame(metadata).to_csv(output / "silver_fits_metadata.csv", index=False, lineterminator="\n")
        values = silver[["time", "phase", "pdcsap_flux", "pdcsap_flux_err", "exposure_time_seconds", "quality"]].apply(pd.to_numeric, errors="coerce")
        keep = np.isfinite(values).all(axis=1) & (values.quality == 0) & (values.pdcsap_flux_err > 0) & (values.exposure_time_seconds > 0)
        selected = silver.loc[keep].copy()
        for key in values:
            selected[key] = values.loc[keep, key]
        if selected.empty or selected.time.duplicated().any():
            raise ValueError("No valid observations or overlapping duplicate times")
        # TIMEDEL can encode a nominal 120 s exposure as 120.00000000000097.
        # Keep the original Silver label; classify Gold with numerical tolerance
        # far smaller than any scientifically meaningful exposure difference.
        tolerance_seconds = 1e-6
        short_cadence = selected.exposure_time_seconds <= 120 + tolerance_seconds
        long_cadence = selected.exposure_time_seconds >= 600 - tolerance_seconds
        selected["cadence_type"] = np.where(short_cadence, "short", np.where(long_cadence, "long", "intermediate"))
        if target.cadence_preference != "any" and not selected.cadence_type.eq(target.cadence_preference).all():
            raise ValueError("Selected product cadence violates the target protocol")
        selected["flux"], selected["flux_err"] = selected.pdcsap_flux, selected.pdcsap_flux_err
        selected["flux_source"] = "PDCSAP_FLUX"
        # Silver timestamps are provenance, not content identity. Keep them in
        # Silver only; the Gold content signature must reproduce on another day.
        selected = selected.drop(columns=["silver_created_at_utc"])
        exclusion = target.transit_duration_days * protocol["preprocessing"]["transit_exclusion_duration_multiplier"] / 2
        normalized, diagnostics = normalize_segments_dataframe(
            selected, transit_exclusion_half_width_days=exclusion,
            min_baseline_points=protocol["preprocessing"]["minimum_baseline_points_per_segment"],
        )
        signature = build_gold_dataset_signature(
            normalized=normalized, diagnostics=diagnostics,
            schema_version="publication-gold-v1", planet_slug=target_slug,
            orbital_period_days=target.orbital_period_days,
            normalization_method="out_of_transit_median",
            transit_exclusion_half_width_days=exclusion,
        )
        signature["target_config_sha256"] = manifest["target_config_sha256"]
        dataset_id = dataset_id_from_signature(target_slug, signature)
        normalized["dataset_id"] = dataset_id
        window = normalized[normalized.phase.abs() <= target.phase_window_days].copy()
        from bayesian_modeling.physical_transit import stratified_phase_thin

        model_input = stratified_phase_thin(window, max_points_per_segment=protocol["preprocessing"]["max_points_per_segment"])
        if model_input.segment_id.nunique() != len(sources) or len(model_input) < 12:
            raise ValueError("Missing selected segments or insufficient modeling observations")
        model_input["normalized_flux"], model_input["normalized_flux_err"] = model_input.flux, model_input.flux_err
        normalized.to_csv(output / "gold_lightcurve.csv", index=False, float_format="%.17g", lineterminator="\n")
        diagnostics.to_csv(output / "segment_diagnostics.csv", index=False, float_format="%.17g", lineterminator="\n")
        model_input.to_csv(output / "model_input.csv", index=False, float_format="%.17g", lineterminator="\n")
        manifest.update({
            "status": "completed", "dataset_id": dataset_id, "dataset_signature": signature,
            "preprocessing_status": "segment_normalized", "preprocessing": protocol["preprocessing"],
            "silver_row_count": len(silver), "quality_row_count": len(normalized),
            "quality_removed_count": len(silver) - len(normalized), "transit_window_row_count": len(window),
            "modeling_row_count": len(model_input), "segment_count": len(sources),
            "median_exposure_seconds": float(model_input.exposure_time_seconds.median()),
            "cadence_classification_roundoff_tolerance_seconds": tolerance_seconds,
            "input_sha256": _hash(output / "model_input.csv"),
            "artifacts": {path.name: _hash(path) for path in sorted(output.glob("*.csv"))},
            "scientific_caveats": [
                "Catalog ephemeris and duration condition phase folding and normalization; catalog comparison is contextual, not independent validation.",
                "PDCSAP includes mission pipeline processing and may not remove astrophysical variability.",
                "Median segment calibration is estimated, but its uncertainty is not propagated in M5.",
                "Phase-uniform thinning can remove time-adjacent residual pairs; chronological diagnostics must account for gaps.",
                "No final interpretability claim follows from successful data preparation.",
            ],
        })
        for entry in manifest["source_artifacts"]:
            if _hash(root / entry["path"]) != entry["sha256"]:
                raise ValueError("RAW source changed during extraction")
    except Exception as exc:
        manifest.update(status="failed", error=repr(exc))
        (output / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
        raise
    (output / "preparation_manifest.json").write_text(json.dumps(manifest, indent=2, allow_nan=False), encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("protocol", type=Path)
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--pilot", action="store_true", help="Permit draft fixture/pilot preparation; never final evidence")
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text(encoding="utf-8"))
    result = prepare_target(args.root, protocol, args.target, args.run_id, allow_draft=args.pilot)
    print(json.dumps({key: result[key] for key in ("status", "target_id", "dataset_id", "input_sha256", "output_directory")}, indent=2))


if __name__ == "__main__":
    main()
