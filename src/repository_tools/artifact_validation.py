"""Validate critical machine-readable invariants of the hardened data layers."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from gold_processing.lightcurve_preparation import (  # noqa: E402
    build_gold_dataset_signature,
    dataset_id_from_signature,
    read_normalized_signature_frame,
)
from project_config import TARGETS, get_target  # noqa: E402


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_gold_content_signature(
    *,
    normalized_path: Path,
    diagnostics: pd.DataFrame,
    metadata: dict[str, object],
    planet_slug: str,
) -> tuple[dict[str, object], str]:
    recorded_signature = {
        key: metadata[key]
        for key in (
            "schema_version",
            "planet_slug",
            "orbital_period_days",
            "method",
            "transit_exclusion_half_width_days",
            "normalized_content_sha256",
            "segments",
        )
    }
    diagnostic_segments = [
        {
            "segment_id": str(row["segment_id"]),
            "source_fits_file": str(row["source_fits_file"]),
            "source_fits_sha256": str(row["source_fits_sha256"]),
            "rows": int(row["row_count"]),
            "exposure_time_seconds": float(row["exposure_time_seconds"]),
        }
        for row in diagnostics.sort_values("segment_id").to_dict(orient="records")
    ]
    require(
        diagnostic_segments == recorded_signature["segments"],
        "Gold diagnostic segment signature differs from metadata",
    )
    content_hash = str(recorded_signature["normalized_content_sha256"])
    require(
        len(content_hash) == 64
        and all(character in "0123456789abcdef" for character in content_hash),
        "Gold normalized-content checksum is invalid",
    )
    if normalized_path.is_file():
        normalized = read_normalized_signature_frame(normalized_path)
        computed_signature = build_gold_dataset_signature(
            normalized=normalized,
            diagnostics=diagnostics,
            schema_version=str(metadata["schema_version"]),
            planet_slug=planet_slug,
            orbital_period_days=float(metadata["orbital_period_days"]),
            normalization_method=str(metadata["method"]),
            transit_exclusion_half_width_days=float(
                metadata["transit_exclusion_half_width_days"]
            ),
        )
        require(
            computed_signature == recorded_signature,
            f"Gold content signature mismatch for {planet_slug}: "
            f"computed={computed_signature!r}; recorded={recorded_signature!r}",
        )
        content_validation = "recomputed_from_local_normalized_artifact"
    else:
        computed_signature = recorded_signature
        content_validation = (
            "recorded_hash_only_full_artifact_excluded_by_storage_policy; "
            "verified by manual clean rebuild"
        )
    require(
        dataset_id_from_signature(planet_slug, computed_signature)
        == metadata["dataset_id"],
        "Gold dataset ID is not derived from its recorded content signature",
    )
    return computed_signature, content_validation


def main() -> None:
    evidence: dict[str, object] = {}
    current = pd.read_csv(
        PROJECT_ROOT / "data/raw/_manifests/raw_data_current_state.csv",
        dtype=str,
    ).fillna("")
    require(current["local_path"].is_unique, "RAW current-state paths are not unique")
    require(not current["local_path"].str.contains(r"\\", regex=True).any(), "RAW has Windows paths")
    require(current["sha256"].str.len().eq(64).all(), "RAW current state has missing checksums")
    missing_paths: list[str] = []
    checksum_mismatches: list[str] = []
    for row in current.to_dict(orient="records"):
        relative = Path(str(row["local_path"]))
        require(not relative.is_absolute() and ".." not in relative.parts, "unsafe RAW path")
        path = PROJECT_ROOT / relative
        if not path.is_file():
            missing_paths.append(relative.as_posix())
        elif sha256_file(path) != row["sha256"]:
            checksum_mismatches.append(relative.as_posix())
    require(not missing_paths, f"RAW current-state files are missing: {missing_paths[:5]}")
    require(
        not checksum_mismatches,
        f"RAW current-state checksum mismatches: {checksum_mismatches[:5]}",
    )
    evidence["raw_current_state"] = {
        "rows": len(current),
        "unique_paths": int(current["local_path"].nunique()),
        "missing_checksums": int(current["sha256"].str.len().ne(64).sum()),
        "missing_files": len(missing_paths),
        "checksum_mismatches": len(checksum_mismatches),
    }

    catalog = pd.read_csv(
        PROJECT_ROOT / "data/silver/catalogs/nasa/pscomppars_selected_planets.csv"
    )
    unit_columns = {
        "orbital_period_days",
        "transit_midpoint_bjd",
        "transit_duration_hours",
        "transit_depth_percent",
        "transit_depth_fraction",
    }
    require(unit_columns.issubset(catalog.columns), "Silver catalog unit columns are incomplete")
    require(
        (catalog["transit_depth_fraction"] - catalog["transit_depth_percent"] / 100).abs().max()
        < 1e-12,
        "Silver transit-depth conversion is inconsistent",
    )
    evidence["silver_catalog"] = {"rows": len(catalog), "unit_columns": sorted(unit_columns)}

    target_evidence: dict[str, object] = {}
    gold_manifest = pd.read_csv(PROJECT_ROOT / "data/gold/manifests/gold_data_manifest.csv")
    raw_checksums = set(current["sha256"].astype(str))
    for target in TARGETS:
        model_dir = PROJECT_ROOT / "data" / "gold" / target.planet_slug / "modeling"
        normalized_path = model_dir / "segment_normalized_lightcurve.csv"
        window = pd.read_csv(model_dir / "transit_window_lightcurve.csv", low_memory=False)
        diagnostics = pd.read_csv(model_dir / "segment_normalization_diagnostics.csv")
        metadata = json.loads((model_dir / "dataset_metadata.json").read_text(encoding="utf-8"))
        require(set(window["planet_name"].astype(str)) == {target.planet_name}, "target mismatch")
        require(set(window["preprocessing_status"].astype(str)) == {"segment_normalized"}, "status mismatch")
        require(window["dataset_id"].nunique() == 1, "Gold window has multiple dataset IDs")
        require(window["dataset_id"].iloc[0] == metadata["dataset_id"], "dataset ID mismatch")
        require(window["segment_id"].nunique() == metadata["segment_count"], "segment count mismatch")
        require(window["source_fits_file"].astype(str).str.len().gt(0).all(), "FITS provenance missing")
        require(
            diagnostics["source_fits_sha256"].astype(str).str.fullmatch(r"[0-9a-f]{64}").all(),
            "Gold segment FITS checksums are invalid",
        )
        require(
            set(diagnostics["source_fits_sha256"].astype(str)).issubset(raw_checksums),
            "Gold segment FITS checksums are absent from RAW current state",
        )
        require((pd.to_numeric(window["exposure_time_seconds"]) > 0).all(), "exposure missing")
        require(
            (pd.to_numeric(diagnostics["normalized_baseline_median"]) - 1.0).abs().max()
            < 1e-12,
            "segment baseline was not normalized to one",
        )
        cadence_values = set(window["cadence_type"].astype(str))
        if target.cadence_preference != "any":
            require(cadence_values == {target.cadence_preference}, "cadence preference mismatch")
        _, content_validation = validate_gold_content_signature(
            normalized_path=normalized_path,
            diagnostics=diagnostics,
            metadata=metadata,
            planet_slug=target.planet_slug,
        )
        metadata_relative = f"data/gold/{target.planet_slug}/modeling/dataset_metadata.json"
        metadata_manifest_rows = gold_manifest.loc[
            gold_manifest["gold_file_path"] == metadata_relative
        ]
        require(len(metadata_manifest_rows) == 1, "Gold metadata manifest row missing")
        metadata_manifest_row = metadata_manifest_rows.iloc[0]
        require(
            int(metadata_manifest_row["column_count"]) == len(metadata),
            "Gold metadata manifest column count is incorrect",
        )
        require(
            metadata_manifest_row["sha256"] == sha256_file(model_dir / "dataset_metadata.json"),
            "Gold metadata manifest checksum mismatch",
        )
        target_evidence[target.planet_slug] = {
            "dataset_id": metadata["dataset_id"],
            "normalized_content_sha256": metadata["normalized_content_sha256"],
            "normalized_content_validation": content_validation,
            "source_fits_sha256": diagnostics["source_fits_sha256"].tolist(),
            "metadata_manifest_column_count": int(metadata_manifest_row["column_count"]),
            "window_rows": len(window),
            "segment_count": int(window["segment_id"].nunique()),
            "cadence": sorted(cadence_values),
            "median_exposure_seconds": float(pd.to_numeric(window["exposure_time_seconds"]).median()),
            "raw_segment_medians": diagnostics["raw_flux_median"].tolist(),
            "normalized_baseline_medians": diagnostics["normalized_baseline_median"].tolist(),
        }
    evidence["gold_targets"] = target_evidence

    run_id = "scientific_003"
    target = get_target("kepler_10_b")
    model_dir = (
        PROJECT_ROOT
        / "models"
        / "bayesian_physical_transit"
        / target.planet_slug
        / "runs"
        / run_id
    )
    table_dir = (
        PROJECT_ROOT
        / "tables"
        / "bayesian_physical_transit"
        / target.planet_slug
        / "runs"
        / run_id
    )
    config = json.loads((model_dir / "model_config.json").read_text(encoding="utf-8"))
    status = json.loads((model_dir / "run_status.json").read_text(encoding="utf-8"))
    modeling_input = table_dir / "modeling_input_physical.csv"
    derived = pd.read_csv(table_dir / "derived_parameters_summary.csv")
    posterior = pd.read_csv(table_dir / "posterior_summary.csv")
    require(status["status"] == "completed", "M5 run is not completed")
    require(
        config["interpretation_gate"]["scientifically_interpretable"] is True,
        "M5 run did not pass the scientific gate",
    )
    require(config["target"]["planet_name"] == target.planet_name, "M5 target mismatch")
    require(
        float(config["model"]["orbit"]["period_days"]) == target.orbital_period_days,
        "M5 model period mismatch",
    )
    require(
        float(derived.loc[0, "orbital_period_days_used"]) == target.orbital_period_days,
        "M5 derived period mismatch",
    )
    input_digest = sha256_file(modeling_input)
    require(
        input_digest == config["input_summary"]["modeling_input_sha256"],
        "M5 modeling-input checksum mismatch",
    )
    require(
        not posterior[["hdi_3%", "hdi_97%"]].isna().any().any(),
        "M5 posterior HDI columns contain missing values",
    )
    require(
        not derived.filter(regex="hdi_").isna().any().any(),
        "M5 derived HDI values contain missing values",
    )
    rp = posterior.loc[posterior["parameter"] == "rp_rs"].iloc[0]
    catalog_rp = target.reference_radius_ratio_from_depth
    trace_path = PROJECT_ROOT / config["artifacts"]["trace"]
    evidence["m5_scientific_run"] = {
        "run_id": run_id,
        "target": target.planet_name,
        "dataset_id": config["input_summary"]["dataset_id"],
        "modeling_input_sha256": input_digest,
        "trace_present_locally": trace_path.exists(),
        "trace_sha256_recorded": config["artifact_checksums_sha256"]["trace"],
        "sampling": config["sampling"],
        "diagnostics": config["diagnostics"],
        "posterior_predictive_status": config["posterior_predictive_status"],
        "residual_metrics": config["residual_metrics"],
        "interpretation_gate": config["interpretation_gate"],
        "rp_rs_posterior_mean": float(rp["mean"]),
        "rp_rs_posterior_hdi_94": [float(rp["hdi_3%"]), float(rp["hdi_97%"] )],
        "catalog_scale_reference_rp_rs": catalog_rp,
        "catalog_scale_inside_posterior_hdi_94": bool(
            float(rp["hdi_3%"] ) <= catalog_rp <= float(rp["hdi_97%"] )
        ),
        "catalog_validation_caveat": (
            "The catalog depth also centers the radius prior; this is a scale check, "
            "not independent validation or a tuning target."
        ),
    }

    noise_evidence: dict[str, object] = {}
    expected_kinds = {
        "white_002": "white_gaussian",
        "sinusoid_002": "deterministic_sinusoid",
        "ar1_002": "correlated_ar1",
    }
    for experiment_id, expected_kind in expected_kinds.items():
        path = (
            PROJECT_ROOT
            / "data"
            / "experiments"
            / "noise_injection"
            / target.planet_slug
            / experiment_id
            / "experiment_config.json"
        )
        experiment = json.loads(path.read_text(encoding="utf-8"))
        injection = experiment["injection"]
        require(injection["kind"] == expected_kind, "noise experiment kind mismatch")
        require(injection["inference_status"] == "not_run", "noise inference claim mismatch")
        require(
            injection["correlated_likelihood_implemented_by_this_generator"] is False,
            "noise generator incorrectly claims a correlated likelihood",
        )
        require(
            experiment["source_dataset_id"] == config["input_summary"]["dataset_id"],
            "noise experiment source dataset mismatch",
        )
        noise_evidence[experiment_id] = {
            "kind": expected_kind,
            "claim": injection["claim"],
            "lag1": injection["median_segment_lag1_autocorrelation"],
            "inference_status": injection["inference_status"],
        }
    require(
        abs(float(noise_evidence["white_002"]["lag1"])) < 0.05,
        "white-noise artifact has unexpectedly strong lag-1 correlation",
    )
    require(
        float(noise_evidence["ar1_002"]["lag1"]) > 0.7,
        "AR(1) artifact does not show the configured correlation",
    )
    evidence["noise_experiments"] = noise_evidence

    rejected_comparison = json.loads(
        (
            PROJECT_ROOT
            / "reports"
            / "model_comparison"
            / "historical_guard_rejection"
            / "comparison_summary.json"
        ).read_text(encoding="utf-8")
    )
    require(
        rejected_comparison["comparison_contract"]["formal_comparison_valid"] is False,
        "historical comparison should have been rejected",
    )
    require(
        rejected_comparison["formal_bayesian_metrics"] is None,
        "rejected comparison must not contain formal Bayesian metrics",
    )
    evidence["historical_comparison_negative_control"] = rejected_comparison[
        "comparison_contract"
    ]

    clean_rebuild = json.loads(
        (PROJECT_ROOT / "reports" / "clean_rebuild_validation.json").read_text(
            encoding="utf-8"
        )
    )
    require(clean_rebuild["status"] == "passed", "clean-room rebuild did not pass")
    require(clean_rebuild["network_used"] is False, "clean-room rebuild used network")
    network_isolation = clean_rebuild.get("network_isolation", {})
    require(
        network_isolation.get("enforcement") == "verified Python socket guard",
        "clean-room rebuild lacks technical network enforcement evidence",
    )
    require(
        network_isolation.get("verification", {}).get("verified") is True,
        "clean-room network guard probe did not pass",
    )
    require(
        network_isolation.get("pipeline_attempted_network_calls") == [],
        "clean-room pipeline attempted Python socket networking",
    )
    require(
        clean_rebuild["targets"][target.planet_slug]["dataset_id"]
        == config["input_summary"]["dataset_id"],
        "clean-room dataset ID differs from the scientific run",
    )
    require(
        clean_rebuild["targets"][target.planet_slug]["m5_modeling_input_sha256"]
        == input_digest,
        "clean-room M5 input differs from the scientific run",
    )
    evidence["clean_rebuild"] = {
        "status": clean_rebuild["status"],
        "network_used": clean_rebuild["network_used"],
        "network_isolation": network_isolation,
        "python_version": clean_rebuild["python_version"],
        "source_raw_tree_sha256": clean_rebuild["source_raw_tree_sha256"],
        "targets": clean_rebuild["targets"],
    }

    sensitivity = json.loads(
        (
            PROJECT_ROOT
            / "reports"
            / "sensitivity"
            / target.planet_slug
            / "sensitivity_002"
            / "sensitivity_summary.json"
        ).read_text(encoding="utf-8")
    )
    require(sensitivity["all_scientific_gates_pass"] is True, "sensitivity gate failed")
    require(sensitivity["all_runs_completed"] is True, "a sensitivity run is incomplete")
    require(
        sensitivity["formal_comparison_contract"]["formal_comparison_valid"] is True,
        "sensitivity runs are not formally comparable",
    )
    require(sensitivity["dataset_id"] == config["input_summary"]["dataset_id"], "sensitivity dataset mismatch")
    require(sensitivity["modeling_input_sha256"] == input_digest, "sensitivity input mismatch")
    require(
        {profile["profile"] for profile in sensitivity["profiles"]}
        == {"catalog_tighter", "baseline", "weak"},
        "sensitivity prior grid is incomplete",
    )
    require(
        all(profile["scientifically_interpretable"] for profile in sensitivity["profiles"]),
        "a sensitivity profile is not interpretable",
    )
    evidence["prior_sensitivity"] = {
        "experiment_id": sensitivity["experiment_id"],
        "profiles": sensitivity["profiles"],
        "maximum_relative_shifts_from_baseline": sensitivity[
            "maximum_relative_shifts_from_baseline"
        ],
        "conclusion": sensitivity["conclusion"],
    }

    formal_comparison = json.loads(
        (
            PROJECT_ROOT
            / "reports"
            / "model_comparison"
            / "prior_sensitivity_002"
            / "comparison_summary.json"
        ).read_text(encoding="utf-8")
    )
    require(
        formal_comparison["comparison_contract"]["formal_comparison_valid"] is True,
        "current formal comparison contract failed",
    )
    metrics = formal_comparison["formal_bayesian_metrics"]
    require(metrics is not None, "current formal comparison metrics are missing")
    require(metrics["diagnostic_status"] == "warning", "expected LOO diagnostic warning missing")
    require(
        metrics["ranking_status"] == "not_ranked_due_to_diagnostic_warning",
        "LOO warning was incorrectly promoted to a ranking",
    )
    require(all(row["warning"] for row in metrics["loo"]), "LOO warning missing for a run")
    require(not any(row["warning"] for row in metrics["waic"]), "unexpected WAIC warning")
    evidence["formal_prior_comparison"] = formal_comparison

    interrupted = json.loads(
        (
            PROJECT_ROOT
            / "models"
            / "bayesian_physical_transit"
            / target.planet_slug
            / "runs"
            / "sensitivity_001_weak_interrupted"
            / "run_status.json"
        ).read_text(encoding="utf-8")
    )
    require(interrupted["status"] == "failed", "interrupted run is not marked failed")
    require(
        "invalid for interpretation" in interrupted["error_message"],
        "interrupted run lacks an interpretation warning",
    )
    evidence["interrupted_run_negative_control"] = interrupted
    print(json.dumps(evidence, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
