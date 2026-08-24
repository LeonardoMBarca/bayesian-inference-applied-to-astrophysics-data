"""Shared filesystem, HTTP, logging, checksum, and manifest helpers."""

from __future__ import annotations

import csv
import hashlib
import json
import logging
import os
import re
import tempfile
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from portable_paths import repo_relative_posix

MANIFEST_COLUMNS = (
    "collected_at_utc",
    "source_name",
    "source_url",
    "planet_name",
    "host_star",
    "local_path",
    "file_name",
    "file_type",
    "mission",
    "product_type",
    "query_or_search_term",
    "status",
    "error_message",
    "sha256",
    "file_size_bytes",
    "notes",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def safe_slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"_+", "_", re.sub(r"[^a-zA-Z0-9]+", "_", ascii_value)).strip("_").lower()


def sha256_file(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_raw_directories(raw_dir: Path) -> None:
    directories = (
        raw_dir / "nasa_exoplanet_archive" / "pscomppars",
        raw_dir / "nasa_exoplanet_archive" / "ps",
        raw_dir / "nasa_exoplanet_archive" / "manifests",
        raw_dir / "mast" / "lightkurve",
        raw_dir / "mast" / "astroquery",
        raw_dir / "mast" / "manifests",
        raw_dir / "exomast" / "manifests",
        raw_dir / "etd_varastro" / "html_snapshots",
        raw_dir / "etd_varastro" / "extracted_metadata",
        raw_dir / "etd_varastro" / "downloaded_lightcurves",
        raw_dir / "etd_varastro" / "manifests",
        raw_dir / "_manifests",
        raw_dir / "_logs",
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("raw_data_ingestion")
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


def build_http_session(config: Any) -> requests.Session:
    retry = Retry(
        total=config.HTTP_RETRY_COUNT,
        connect=config.HTTP_RETRY_COUNT,
        read=config.HTTP_RETRY_COUNT,
        backoff_factor=config.HTTP_BACKOFF_FACTOR,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=frozenset({"GET", "POST"}),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.headers.update({"User-Agent": config.USER_AGENT})
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def atomic_write_bytes(path: Path, content: bytes) -> bool:
    """Write a new artifact once. Return False when the destination exists."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return False

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
        if path.exists():
            Path(temporary_name).unlink(missing_ok=True)
            return False
        os.replace(temporary_name, path)
        return True
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def atomic_write_text(path: Path, content: str) -> bool:
    return atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> bool:
    content = json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n"
    return atomic_write_text(path, content)


def versioned_path(path: Path, content: bytes, label: str) -> Path:
    """Return a content-addressed path when an existing artifact differs."""
    if not path.exists() or path.read_bytes() == content:
        return path
    digest = hashlib.sha256(content).hexdigest()[:12]
    return path.with_name(f"{path.stem}_{label}_{digest}{path.suffix}")


def csv_bytes(
    rows: Iterable[Mapping[str, Any]],
    fieldnames: Iterable[str] | None = None,
) -> bytes:
    materialized = list(rows)
    if fieldnames is None:
        ordered_fields: list[str] = []
        for row in materialized:
            for key in row:
                if key not in ordered_fields:
                    ordered_fields.append(key)
        fieldnames = ordered_fields

    from io import StringIO

    output = StringIO(newline="")
    writer = csv.DictWriter(
        output,
        fieldnames=list(fieldnames),
        extrasaction="ignore",
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(materialized)
    return output.getvalue().encode("utf-8")


def relative_path(path: Path, project_root: Path) -> str:
    return repo_relative_posix(path, project_root)


class RawDataManifest:
    """Append run events and atomically refresh CSV and JSON manifest views."""

    def __init__(self, raw_dir: Path, project_root: Path) -> None:
        self.project_root = project_root
        self.csv_path = raw_dir / "_manifests" / "raw_data_manifest.csv"
        self.json_path = raw_dir / "_manifests" / "raw_data_manifest.json"
        self.current_state_csv_path = (
            raw_dir / "_manifests" / "raw_data_current_state.csv"
        )
        self.current_state_json_path = (
            raw_dir / "_manifests" / "raw_data_current_state.json"
        )
        self.rows: list[dict[str, Any]] = []
        if self.csv_path.exists():
            with self.csv_path.open("r", encoding="utf-8", newline="") as handle:
                self.rows.extend(dict(row) for row in csv.DictReader(handle))

    def add(
        self,
        *,
        source_name: str,
        source_url: str = "",
        planet_name: str = "",
        host_star: str = "",
        path: Path | None = None,
        file_type: str = "",
        mission: str = "",
        product_type: str = "",
        query_or_search_term: str = "",
        status: str,
        error_message: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        checksum = ""
        file_size: str | int = ""
        local = ""
        file_name = ""
        if path is not None:
            local = relative_path(path, self.project_root)
            file_name = path.name
            if path.is_file():
                checksum = sha256_file(path)
                file_size = path.stat().st_size

        row = {
            "collected_at_utc": utc_now(),
            "source_name": source_name,
            "source_url": source_url,
            "planet_name": planet_name,
            "host_star": host_star,
            "local_path": local,
            "file_name": file_name,
            "file_type": file_type,
            "mission": mission,
            "product_type": product_type,
            "query_or_search_term": query_or_search_term,
            "status": status,
            "error_message": error_message,
            "sha256": checksum,
            "file_size_bytes": file_size,
            "notes": notes,
        }
        self.rows.append(row)
        return row

    def record_artifact(
        self,
        *,
        path: Path,
        created: bool,
        source_name: str,
        source_url: str = "",
        planet_name: str = "",
        host_star: str = "",
        file_type: str = "",
        mission: str = "",
        product_type: str = "",
        query_or_search_term: str = "",
        notes: str = "",
    ) -> dict[str, Any]:
        return self.add(
            source_name=source_name,
            source_url=source_url,
            planet_name=planet_name,
            host_star=host_star,
            path=path,
            file_type=file_type,
            mission=mission,
            product_type=product_type,
            query_or_search_term=query_or_search_term,
            status="downloaded" if created else "skipped_existing",
            notes=notes,
        )

    def flush(self) -> None:
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        csv_content = csv_bytes(self.rows, MANIFEST_COLUMNS)
        json_content = (
            json.dumps(self.rows, indent=2, ensure_ascii=False, default=str) + "\n"
        ).encode("utf-8")
        self._replace_manifest(self.csv_path, csv_content)
        self._replace_manifest(self.json_path, json_content)
        current_rows = self._current_state_rows()
        self._replace_manifest(
            self.current_state_csv_path,
            csv_bytes(current_rows, MANIFEST_COLUMNS),
        )
        self._replace_manifest(
            self.current_state_json_path,
            (json.dumps(current_rows, indent=2, ensure_ascii=False) + "\n").encode("utf-8"),
        )

    def _current_state_rows(self) -> list[dict[str, Any]]:
        """Return one checksum-verified row per currently existing RAW file."""

        seen: set[str] = set()
        current: list[dict[str, Any]] = []
        for event in reversed(self.rows):
            local_path = str(event.get("local_path", "")).replace("\\", "/").strip()
            if not local_path or local_path in seen:
                continue
            seen.add(local_path)
            absolute_path = self.project_root / Path(local_path)
            if not absolute_path.is_file():
                continue
            row = {column: event.get(column, "") for column in MANIFEST_COLUMNS}
            row["local_path"] = local_path
            row["file_name"] = absolute_path.name
            row["status"] = "current"
            row["error_message"] = ""
            row["sha256"] = sha256_file(absolute_path)
            row["file_size_bytes"] = absolute_path.stat().st_size
            current.append(row)
        return sorted(current, key=lambda row: str(row["local_path"]))

    @staticmethod
    def _replace_manifest(path: Path, content: bytes) -> None:
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


def save_artifact(
    manifest: RawDataManifest,
    path: Path,
    content: bytes,
    **manifest_fields: Any,
) -> bool:
    created = atomic_write_bytes(path, content)
    manifest.record_artifact(path=path, created=created, **manifest_fields)
    return created


def register_error(
    manifest: RawDataManifest,
    logger: logging.Logger,
    *,
    source_name: str,
    error: Exception | str,
    source_url: str = "",
    planet_name: str = "",
    host_star: str = "",
    mission: str = "",
    product_type: str = "",
    query_or_search_term: str = "",
    notes: str = "",
) -> None:
    message = str(error)
    logger.error(
        "%s | planet=%s | mission=%s | %s",
        source_name,
        planet_name or "-",
        mission or "-",
        message,
    )
    manifest.add(
        source_name=source_name,
        source_url=source_url,
        planet_name=planet_name,
        host_star=host_star,
        mission=mission,
        product_type=product_type,
        query_or_search_term=query_or_search_term,
        status="failed",
        error_message=message,
        notes=notes,
    )
