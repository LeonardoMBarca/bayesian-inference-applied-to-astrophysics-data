"""Manifest writer for GOLD outputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from .utils import atomic_write_dataframe, atomic_write_json, relative_path, sha256_file, utc_now

GOLD_MANIFEST_COLUMNS = (
    "created_at_utc",
    "gold_layer",
    "planet_name",
    "host_star",
    "planet_slug",
    "source_silver_path",
    "source_raw_path",
    "gold_file_path",
    "gold_file_name",
    "transformation_type",
    "row_count",
    "column_count",
    "status",
    "error_message",
    "sha256",
    "file_size_bytes",
    "notes",
)


class GoldManifest:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.rows: list[dict[str, Any]] = []
        self.csv_path = config.GOLD_DATA_DIR / "manifests" / "gold_data_manifest.csv"
        self.json_path = config.GOLD_DATA_DIR / "manifests" / "gold_data_manifest.json"

    def add_artifact(
        self,
        *,
        path: Path,
        transformation_type: str,
        planet_name: str = "",
        host_star: str = "",
        planet_slug: str = "",
        source_silver_path: str = "",
        source_raw_path: str = "",
        row_count: int | str = "",
        column_count: int | str = "",
        status: str = "created",
        error_message: str = "",
        notes: str = "",
    ) -> None:
        checksum = sha256_file(path) if path.exists() else ""
        file_size = path.stat().st_size if path.exists() else ""
        self.rows.append(
            {
                "created_at_utc": utc_now(),
                "gold_layer": "gold",
                "planet_name": planet_name,
                "host_star": host_star,
                "planet_slug": planet_slug,
                "source_silver_path": source_silver_path,
                "source_raw_path": source_raw_path,
                "gold_file_path": relative_path(path, self.config.PROJECT_ROOT),
                "gold_file_name": path.name,
                "transformation_type": transformation_type,
                "row_count": row_count,
                "column_count": column_count,
                "status": status,
                "error_message": error_message,
                "sha256": checksum,
                "file_size_bytes": file_size,
                "notes": notes,
            }
        )

    def add_failure(
        self,
        *,
        transformation_type: str,
        error_message: str,
        planet_name: str = "",
        host_star: str = "",
        planet_slug: str = "",
        source_silver_path: str = "",
        source_raw_path: str = "",
        notes: str = "",
    ) -> None:
        self.rows.append(
            {
                "created_at_utc": utc_now(),
                "gold_layer": "gold",
                "planet_name": planet_name,
                "host_star": host_star,
                "planet_slug": planet_slug,
                "source_silver_path": source_silver_path,
                "source_raw_path": source_raw_path,
                "gold_file_path": "",
                "gold_file_name": "",
                "transformation_type": transformation_type,
                "row_count": "",
                "column_count": "",
                "status": "failed",
                "error_message": error_message,
                "sha256": "",
                "file_size_bytes": "",
                "notes": notes,
            }
        )

    def flush(self) -> None:
        dataframe = pd.DataFrame(self.rows, columns=GOLD_MANIFEST_COLUMNS)
        atomic_write_dataframe(self.csv_path, dataframe)
        atomic_write_json(self.json_path, self.rows)
