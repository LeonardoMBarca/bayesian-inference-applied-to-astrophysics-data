"""Check RAW manifest identities against Git and optional real checkouts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from repository_tools.raw_byte_audit import run_audit, write_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--revision", default="HEAD")
    parser.add_argument("--real-checkouts", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_audit(args.repo.resolve(), args.revision, args.real_checkouts)
    if args.output:
        write_report(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key != "records"}, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
