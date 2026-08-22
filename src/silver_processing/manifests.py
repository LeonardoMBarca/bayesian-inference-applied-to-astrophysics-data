"""Silver manifest writer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from .utils import atomic_write_dataframe, atomic_write_json, relative_path, sha256_file, utc_now


SILVER_MANIFEST_COLUMNS = (
    "created_at_utc",
    "silver_layer",
    "source_raw_manifest_path",
    "source_raw_path",
    "source_name",
    "planet_name",
    "host_star",
    "mission",
    "raw_file_type",
    "silver_file_path",
    "silver_file_name",
    "silver_file_type",
    "transformation_type",
    "row_count",
    "column_count",
    "status",
    "error_message",
    "sha256",
    "file_size_bytes",
    "notes",
)


class SilverManifest:
    def __init__(self, config: Any) -> None:
        self.config = config
        self.rows: list[dict[str, Any]] = []
        self.csv_path = (
            config.SILVER_DATA_DIR / "manifests" / "silver_data_manifest.csv"
        )
        self.json_path = (
            config.SILVER_DATA_DIR / "manifests" / "silver_data_manifest.json"
        )

    def add_artifact(
        self,
        *,
        path: Path,
        source_raw_path: str = "",
        source_name: str = "",
        planet_name: str = "",
        host_star: str = "",
        mission: str = "",
        raw_file_type: str = "",
        transformation_type: str,
        row_count: int | str = "",
        column_count: int | str = "",
        status: str = "created",
        error_message: str = "",
        notes: str = "",
    ) -> None:
        if path.exists():
            checksum = sha256_file(path)
            file_size = path.stat().st_size
        else:
            checksum = ""
            file_size = ""
        self.rows.append(
            {
                "created_at_utc": utc_now(),
                "silver_layer": "silver",
                "source_raw_manifest_path": relative_path(
                    self.config.RAW_MANIFEST_PATH,
                    self.config.PROJECT_ROOT,
                ),
                "source_raw_path": source_raw_path,
                "source_name": source_name,
                "planet_name": planet_name,
                "host_star": host_star,
                "mission": mission,
                "raw_file_type": raw_file_type,
                "silver_file_path": relative_path(path, self.config.PROJECT_ROOT),
                "silver_file_name": path.name,
                "silver_file_type": path.suffix.lstrip("."),
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
        source_raw_path: str = "",
        source_name: str = "",
        planet_name: str = "",
        host_star: str = "",
        mission: str = "",
        raw_file_type: str = "",
        transformation_type: str,
        error_message: str,
        notes: str = "",
    ) -> None:
        self.rows.append(
            {
                "created_at_utc": utc_now(),
                "silver_layer": "silver",
                "source_raw_manifest_path": relative_path(
                    self.config.RAW_MANIFEST_PATH,
                    self.config.PROJECT_ROOT,
                ),
                "source_raw_path": source_raw_path,
                "source_name": source_name,
                "planet_name": planet_name,
                "host_star": host_star,
                "mission": mission,
                "raw_file_type": raw_file_type,
                "silver_file_path": "",
                "silver_file_name": "",
                "silver_file_type": "",
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
        dataframe = pd.DataFrame(self.rows, columns=SILVER_MANIFEST_COLUMNS)
        atomic_write_dataframe(self.csv_path, dataframe)
        atomic_write_json(self.json_path, self.rows)

