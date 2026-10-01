"""Read stored HDF posterior variables to delimit the v3 conditioning incident."""
from __future__ import annotations

import json
from pathlib import Path

from publication.evidence_archive import digest_file


def review(root: Path):
    import h5netcdf
    import numpy as np
    campaigns, sources = {}, {}
    for campaign in ("tcc_numerical_complement_v3", "tcc_numerical_complement_v4"):
        name = f"artifacts/publication_campaign/{campaign}/campaign_state.json"
        state = json.loads((root / name).read_text())
        sources[name] = digest_file(root / name)
        rows = []
        for job in state["jobs"].values():
            if not job["attempts"]:
                continue
            attempt = job["attempts"][-1]
            directory = root / attempt["output_dir"]
            if attempt["status"] not in {"COMPLETED", "COMPLETED_REJECTED"}:
                continue
            config_name = attempt["output_dir"] + "/inference_config.json"
            config = json.loads((directory / "inference_config.json").read_text())
            trace_name = attempt["output_dir"] + "/trace.nc"
            standardized = config.get("transit_center_parameterization", "direct") == "standardized"
            with h5netcdf.File(root / trace_name, "r") as file:
                variables = list(file.groups["posterior"].variables)
                has_free = "t0_standardized" in variables
                exact = None
                if has_free:
                    post = file.groups["posterior"]
                    exact = bool(np.array_equal(post.variables["t0"][:], config["t0_prior_sigma_days"] * post.variables["t0_standardized"][:]))
            sources[config_name] = digest_file(root / config_name)
            sources[trace_name] = digest_file(root / trace_name)
            sources[attempt["output_dir"] + "/completion_manifest.json"] = attempt["completion_manifest_sha256"]
            rows.append({"job_id": job["job_id"], "recorded_status": job["status"], "config_path": config_name,
                         "trace_path": trace_name, "standardized": standardized, "free_coordinate_saved": has_free,
                         "t0_transform_exact": exact, "posterior_variables": variables,
                         "predictive_invalidated": campaign.endswith("v3") and standardized and not has_free,
                         "specific_incident_unaffected": not standardized,
                         "meaning": "Preserved historical flags; invalid PPC is not a scientific rejection. Direct unaffected means only this specific incident."})
        counts = {"declared_jobs": len(state["jobs"]), "traces": len(rows),
                  "direct_traces": sum(not row["standardized"] for row in rows),
                  "standardized_traces": sum(row["standardized"] for row in rows),
                  "ppc_invalidated": sum(row["predictive_invalidated"] for row in rows),
                  "pending_jobs": sum(job["status"] == "PLANNED" for job in state["jobs"].values())}
        campaigns[campaign] = {"controller_status": state["status"], "counts": counts, "traces": rows}
    current = campaigns["tcc_numerical_complement_v4"]["traces"]
    passed = all(row["free_coordinate_saved"] and row["t0_transform_exact"] if row["standardized"] else not row["free_coordinate_saved"] for row in current)
    return {"schema_version": "complement-trace-review-v1", "status": "passed" if passed else "failed",
            "campaigns": campaigns, "source_checksums": sources,
            "generator_source_checksums": {"src/publication/complement_trace_review.py": digest_file(root / "src/publication/complement_trace_review.py")},
            "new_inference": False}
