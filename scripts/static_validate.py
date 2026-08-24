"""Dependency-free static contract checks used locally and in CI."""

from __future__ import annotations

import ast
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    failures: list[str] = []
    python_files = [
        path
        for directory in ("src", "scripts", "tests")
        for path in (PROJECT_ROOT / directory).rglob("*.py")
    ]
    for path in sorted(python_files):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            failures.append(f"{path.relative_to(PROJECT_ROOT).as_posix()}: {exc}")

    physical_source = (
        PROJECT_ROOT / "src" / "bayesian_modeling" / "physical_transit.py"
    ).read_text(encoding="utf-8")
    kepler_wrapper = (PROJECT_ROOT / "scripts" / "run_kepler_10b.py").read_text(
        encoding="utf-8"
    )
    if "HAT-P-7" in physical_source or "hat_p_7_b" in physical_source:
        failures.append("shared M5 implementation contains a stale HAT-P-7 literal")
    if "HAT-P-7" in kepler_wrapper or "hat_p_7_b" in kepler_wrapper:
        failures.append("Kepler-10 wrapper contains cross-target contamination")
    if len(kepler_wrapper.splitlines()) > 40:
        failures.append("Kepler-10 entry point is no longer thin")

    for notebook in sorted((PROJECT_ROOT / "notebooks").glob("*.ipynb")):
        try:
            json.loads(notebook.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeError) as exc:
            failures.append(f"invalid notebook {notebook.name}: {exc}")

    requirements = [
        line.strip()
        for line in (PROJECT_ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    unpinned = [line for line in requirements if "==" not in line]
    if unpinned:
        failures.append(f"unpinned dependencies: {unpinned}")

    if failures:
        raise SystemExit("Static validation failed:\n- " + "\n- ".join(failures))
    print(
        json.dumps(
            {
                "status": "passed",
                "python_files_parsed": len(python_files),
                "notebooks_parsed": len(list((PROJECT_ROOT / "notebooks").glob("*.ipynb"))),
                "exact_dependencies": len(requirements),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
