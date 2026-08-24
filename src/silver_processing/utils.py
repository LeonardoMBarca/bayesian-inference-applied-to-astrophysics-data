"""Shared utilities for SILVER processing."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from portable_paths import repo_relative_posix


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ensure_silver_directories(silver_dir: Path) -> None:
    directories = (
        silver_dir / "catalogs" / "nasa",
        silver_dir / "catalogs" / "exomast",
        silver_dir / "lightcurves" / "mast",
        silver_dir / "lightcurves" / "etd",
        silver_dir / "etd",
        silver_dir / "validation",
        silver_dir / "manifests",
        silver_dir / "logs",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("silver_data_processing")
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    log_path.parent.mkdir(parents=True, exist_ok=True)
    formatter = logging.Formatter(
        "%(asctime)sZ | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    formatter.converter = time.gmtime

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative_path(path: Path, project_root: Path) -> str:
    return repo_relative_posix(path, project_root)


def atomic_write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".part",
        dir=path.parent,
    )
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
    )


def atomic_write_dataframe(path: Path, dataframe: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".part",
        dir=path.parent,
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="") as handle:
            dataframe.to_csv(handle, index=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def read_raw_manifest(config: Any) -> pd.DataFrame:
    if not config.RAW_MANIFEST_PATH.exists():
        raise FileNotFoundError(f"RAW manifest not found: {config.RAW_MANIFEST_PATH}")
    return pd.read_csv(config.RAW_MANIFEST_PATH, dtype=str).fillna("")


def raw_manifest_lookup(raw_manifest: pd.DataFrame) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    if "local_path" not in raw_manifest.columns:
        return lookup
    for _, row in raw_manifest.iterrows():
        local_path = str(row.get("local_path", ""))
        if not local_path:
            continue
        current = lookup.get(local_path)
        candidate = {key: str(value) for key, value in row.to_dict().items()}
        if current is None:
            lookup[local_path] = candidate
            continue
        if current.get("status") == "failed" and candidate.get("status") != "failed":
            lookup[local_path] = candidate
    return lookup


def get_raw_info(
    path: Path,
    config: Any,
    raw_lookup: dict[str, dict[str, str]],
) -> dict[str, str]:
    local_path = relative_path(path, config.PROJECT_ROOT)
    row = raw_lookup.get(local_path, {})
    checksum = row.get("sha256") or (sha256_file(path) if path.exists() else "")
    return {
        "source_raw_path": local_path,
        "source_raw_sha256": checksum,
        "source_raw_file_name": path.name,
        "source_name": row.get("source_name", ""),
        "mission": row.get("mission", ""),
        "product_type": row.get("product_type", ""),
        "raw_file_type": row.get("file_type", path.suffix.lstrip(".")),
    }


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def serialize_complex_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    result = dataframe.copy()
    for column in result.columns:
        if result[column].map(lambda value: isinstance(value, (dict, list, tuple))).any():
            result[column] = result[column].map(
                lambda value: compact_json(value)
                if isinstance(value, (dict, list, tuple))
                else value
            )
    return result


def planet_by_slug(config: Any) -> dict[str, dict[str, Any]]:
    return {planet["planet_slug"]: planet for planet in config.PLANETS}


def sorted_planets(config: Any) -> list[dict[str, Any]]:
    return sorted(config.PLANETS, key=lambda item: item["priority"])
