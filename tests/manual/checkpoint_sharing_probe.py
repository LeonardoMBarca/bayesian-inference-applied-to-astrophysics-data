"""WSL half of the real Windows/DrvFS checkpoint sharing integration test.

Only writes beneath an explicitly created checkpoint-sharing fixture directory.
This helper never opens a scientific campaign or starts inference.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from publication.campaign import _atomic_json  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--mode", choices=["raw", "retry", "stress"], required=True)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if not directory.name.startswith("checkpoint-sharing-") or not directory.is_dir():
        raise ValueError("Explicit isolated fixture directory required")
    path = directory / "campaign_state.json"
    if json.loads(path.read_text())["fixture"] != "checkpoint-sharing":
        raise ValueError("Refusing a non-fixture checkpoint")
    start = time.monotonic()
    count = 200 if args.mode == "stress" else 1
    for index in range(1, count + 1):
        payload = {"fixture": "checkpoint-sharing", "sequence": index, "complete": True}
        if args.mode == "raw":
            temporary = directory / "raw.tmp"
            temporary.write_text(json.dumps(payload), encoding="utf-8")
            try:
                os.replace(temporary, path)
            except PermissionError as exc:
                print(json.dumps({"expected_failure": True, "errno": exc.errno}), flush=True)
                raise SystemExit(13) from exc
        else:
            _atomic_json(path, payload)
        if args.mode == "stress":
            time.sleep(.01)
    print(json.dumps({"status": "PASS", "writes": count,
                      "seconds": time.monotonic() - start}), flush=True)


if __name__ == "__main__":
    main()
