"""Shared utilities for GOLD processing."""

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


def relative_path(path: Path, project_root: Path) -> str:
    return repo_relative_posix(path, project_root)


def ensure_gold_directories(config: Any, planet_slug: str | None = None) -> None:
    directories = [
        config.GOLD_DATA_DIR / "selection",
        config.GOLD_DATA_DIR / "manifests",
        config.GOLD_DATA_DIR / "logs",
    ]
    if planet_slug:
        target_dir = config.GOLD_DATA_DIR / planet_slug
        directories.extend(
            [
                target_dir / "catalogs",
                target_dir / "lightcurves",
                target_dir / "modeling",
                target_dir / "validation",
                target_dir / "docs",
            ]
        )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("gold_data_processing")
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


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required SILVER file not found: {path}")
    return pd.read_csv(path, dtype=str, low_memory=False).fillna("")


def to_number(series: pd.Series | Any) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def scalar_to_float(value: Any) -> float | None:
    numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(numeric):
        return None
    return float(numeric)


def markdown_table(dataframe: pd.DataFrame, columns: list[str]) -> str:
    if dataframe.empty:
        return "_Sem registros._\n"
    rows = dataframe.loc[:, columns].astype(str).values.tolist()
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    body = ["| " + " | ".join(row) + " |" for row in rows]
    return "\n".join([header, separator, *body]) + "\n"


def path_list(config: Any, paths: list[Path]) -> str:
    return "|".join(relative_path(path, config.PROJECT_ROOT) for path in paths)
