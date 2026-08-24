"""Fail loudly unless every locked scientific and validation dependency imports."""

from __future__ import annotations

import importlib
import json
import sys
from importlib.metadata import version

IMPORTS = {
    "numpy": "numpy",
    "pandas": "pandas",
    "scipy": "scipy",
    "requests": "requests",
    "astropy": "astropy",
    "astroquery": "astroquery",
    "lightkurve": "lightkurve",
    "beautifulsoup4": "bs4",
    "lxml": "lxml",
    "tqdm": "tqdm",
    "matplotlib": "matplotlib",
    "pymc": "pymc",
    "pytensor": "pytensor",
    "arviz": "arviz",
    "exoplanet": "exoplanet",
    "exoplanet-core": "exoplanet_core",
    "h5netcdf": "h5netcdf",
    "h5py": "h5py",
    "ruff": "ruff",
}


def main() -> None:
    imported: dict[str, str] = {}
    failures: list[str] = []
    for distribution, module_name in IMPORTS.items():
        try:
            importlib.import_module(module_name)
            imported[distribution] = version(distribution)
        except Exception as exc:
            failures.append(f"{distribution}/{module_name}: {type(exc).__name__}: {exc}")
    if failures:
        raise SystemExit("Scientific environment validation failed:\n- " + "\n- ".join(failures))
    print(
        json.dumps(
            {
                "status": "passed",
                "python_version": sys.version.split()[0],
                "imports": imported,
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
