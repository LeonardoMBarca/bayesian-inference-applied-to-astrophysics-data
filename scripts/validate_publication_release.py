"""Validate publication evidence; incomplete releases fail by default."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import json  # noqa: E402


def main():
    """Current campaigns use v2; legacy registries retain their original API."""
    arguments = sys.argv[1:]
    root = Path(__file__).resolve().parents[1]
    if "--root" in arguments:
        root = Path(arguments[arguments.index("--root") + 1])
    registry_path = root / "publication/registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
    if registry.get("campaign_registries"):
        from publication.campaign_release import main as validate
    else:
        from publication.release import main as validate
    validate()

if __name__ == "__main__":
    main()
