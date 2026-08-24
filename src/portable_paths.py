"""Platform-independent path rendering for machine-readable artifacts."""

from __future__ import annotations

from pathlib import Path


def repo_relative_posix(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError as exc:
        raise ValueError(
            f"Artifact path must be inside the repository: {path.resolve()} "
            f"is outside {project_root.resolve()}"
        ) from exc
