"""Capture the isolated benchmark environment; never install or modify packages."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--install-report", type=Path)
    args = parser.parse_args()
    packages = sorted((distribution.metadata["Name"], distribution.version)
                      for distribution in importlib.metadata.distributions())
    imports = {}
    sources = {}
    for name in ("juliet", "batman", "dynesty", "george", "celerite", "numpy", "scipy", "pandas", "ultranest"):
        module = importlib.import_module(name)
        imports[name] = {"imported": True, "module_version": str(getattr(module, "__version__", "not exposed"))}
        if name in {"juliet", "batman"}:
            for path in sorted(Path(module.__file__).parent.glob("*.py")):
                sources[f"{name}/{path.name}"] = hashlib.sha256(path.read_bytes()).hexdigest()
    check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
    compiler = subprocess.run(["gcc", "--version"], capture_output=True, text=True, check=False)
    manifest = {"schema_version": "benchmark-environment-v1", "python_version": platform.python_version(),
                "captured_utc": datetime.now(timezone.utc).isoformat(),
                "compiler": compiler.stdout.splitlines()[0] if compiler.returncode == 0 else "unavailable",
                "platform": platform.platform(), "machine": platform.machine(),
                "evidence_class": "engineering_environment_not_final_posterior_validation",
                "packages": [{"name": name, "version": version} for name, version in packages],
                "imports": imports, "source_sha256": sources,
                "pip_check": {"returncode": check.returncode, "stdout": check.stdout, "stderr": check.stderr},
                "lock_method": "Complete installed distribution inventory, including pip/setuptools/wheel; exact version specifiers without nonportable local build paths"}
    if args.install_report:
        report = json.loads(args.install_report.read_text(encoding="utf-8"))
        manifest["install_distributions"] = [
            {"name": item["metadata"]["name"], "version": item["metadata"]["version"],
             "url": item["download_info"]["url"], "hashes": item["download_info"]["archive_info"]["hashes"]}
            for item in report["install"]]
    args.output_directory.mkdir(parents=True, exist_ok=True)
    requirements = "\n".join(f"{name}=={version}" for name, version in packages) + "\n"
    manifest["requirements_sha256"] = hashlib.sha256(requirements.encode()).hexdigest()
    with (args.output_directory / "benchmark-requirements.txt").open("x", encoding="utf-8", newline="\n") as handle:
        handle.write(requirements)
    with (args.output_directory / "benchmark-environment.json").open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(manifest, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
    print(json.dumps({"packages": len(packages), "imports": imports, "pip_check": manifest["pip_check"]}, indent=2))
    if check.returncode:
        raise SystemExit(check.returncode)


if __name__ == "__main__":
    main()
