"""Immutable acquisition of exact precommitted publication FITS products."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from publication.contracts import safe_path, sha256_file, utc_now


def acquire_selected_kepler4(root: Path, selection_path: Path, selection_commit: str) -> dict:
    """No target discovery or fit-based selection; all exact URLs are committed."""
    import requests
    from astropy.io import fits

    root = root.resolve()
    selection_path = (selection_path if selection_path.is_absolute() else root / selection_path).resolve()
    relative = selection_path.relative_to(root).as_posix()
    original = subprocess.check_output(["git", "-C", str(root), "show", f"{selection_commit}:{relative}"])
    if original != selection_path.read_bytes():
        raise ValueError("Selection changed since its committed pre-acquisition snapshot")
    subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", selection_commit, "HEAD"], check=True)
    protocol = json.loads(original)
    if protocol.get("selection_status") != "FROZEN":
        raise ValueError("Target selection must be frozen and committed before acquisition")
    selected = [entry for entry in protocol["targets"] if entry["config"]["planet_slug"] == "kepler_4_b"]
    if len(selected) != 1:
        raise ValueError("Exactly one Kepler-4 selection is required")
    target = selected[0]
    policy = target["acquisition_policy"]
    urls = policy["preselected_product_urls"]
    if len(urls) != 3 or len(set(urls)) != 3:
        raise ValueError("Expected exactly three independently named selected products")
    destination = safe_path(root, policy["destination"].rstrip("/"))
    if not destination.is_relative_to(root / "publication/inputs/raw"):
        raise ValueError("New RAW acquisition must use publication/inputs/raw")
    destination.mkdir(parents=True, exist_ok=False)
    metadata = {
        "schema_version": "publication-raw-acquisition-v1", "target_id": "kepler_4_b",
        "selection_commit": selection_commit, "selection_path": relative,
        "selection_file_sha256": hashlib.sha256(original).hexdigest(),
        "started_at_utc": utc_now(), "status": "running", "files": [],
    }
    with (destination / "acquisition_started.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2)
    for index, url in enumerate(urls):
        parsed = urlparse(url)
        filename = Path(parsed.path).name
        record = {"url": url, "retrieved_at_utc": utc_now(), "status": "failed"}
        partial = destination / (filename + ".part")
        final = destination / filename
        try:
            if parsed.scheme != "https" or parsed.netloc != "archive.stsci.edu" or not filename.endswith("_llc.fits"):
                raise ValueError("Unexpected source URI in committed selection")
            if final.exists():
                raise FileExistsError(final)
            with requests.get(url, stream=True, timeout=(20, 120)) as response:
                response.raise_for_status()
                record.update(http_status=response.status_code, final_url=response.url,
                              etag=response.headers.get("ETag"), last_modified=response.headers.get("Last-Modified"))
                with partial.open("xb") as stream:
                    for chunk in response.iter_content(chunk_size=1 << 20):
                        if chunk:
                            stream.write(chunk)
            with fits.open(partial, memmap=False) as hdul:
                primary, table = hdul[0].header, hdul[1].header
                if primary.get("KEPLERID") != target["archive_identity"]["value"]:
                    raise ValueError("Downloaded FITS target is not preselected KIC 11853905")
                if primary.get("QUARTER") != policy["quarter_selection"][index]:
                    raise ValueError("Downloaded FITS quarter differs from preselected quarter")
                if table.get("TIMESYS") != "TDB" or table.get("BJDREFI") != 2454833:
                    raise ValueError("Downloaded FITS time convention is inconsistent")
                exposure = float(table["TIMEDEL"]) * 86400
                if not 1600 <= exposure <= 1900:
                    raise ValueError("Downloaded product is not Kepler long cadence")
                if not {"PDCSAP_FLUX", "PDCSAP_FLUX_ERR"}.issubset(hdul[1].columns.names):
                    raise ValueError("Downloaded product lacks measured PDCSAP flux/error")
                record.update(quarter=int(primary["QUARTER"]), exposure_time_seconds=exposure,
                              bjd_reference=2454833, timesys="TDB", row_count=len(hdul[1].data))
            digest = sha256_file(partial)
            # Atomic exclusive link fails instead of replacing an existing file
            # on either POSIX or NTFS. Only our completed .part link is removed.
            os.link(partial, final)
            partial.unlink()
            if sha256_file(final) != digest:
                raise ValueError("Acquired file readback checksum mismatch")
            record.update(path=final.relative_to(root).as_posix(), sha256=digest,
                          size_bytes=final.stat().st_size, status="completed")
        except Exception as exc:
            record.update(error=repr(exc), partial_path=partial.relative_to(root).as_posix())
            if partial.exists():
                record.update(partial_sha256=sha256_file(partial), partial_size_bytes=partial.stat().st_size)
        metadata["files"].append(record)
        print(json.dumps({"url": url, "status": record["status"], "error": record.get("error")}), flush=True)
    metadata.update(status="completed" if all(row["status"] == "completed" for row in metadata["files"]) else "failed",
                    completed_at_utc=utc_now())
    with (destination / "acquisition_manifest.json").open("x", encoding="utf-8") as stream:
        json.dump(metadata, stream, indent=2, allow_nan=False)
        stream.write("\n")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("selection", type=Path)
    parser.add_argument("--selection-commit", required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = acquire_selected_kepler4(args.root, args.selection, args.selection_commit)
    if result["status"] != "completed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
