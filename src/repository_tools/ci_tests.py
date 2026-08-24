"""Run the practical CI suite and reject any skipped test."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def enforce_ci_result(result: unittest.TestResult) -> None:
    if not result.wasSuccessful():
        raise RuntimeError(
            f"CI test suite failed: failures={len(result.failures)}, errors={len(result.errors)}"
        )
    if result.skipped:
        details = "; ".join(f"{test}: {reason}" for test, reason in result.skipped)
        raise RuntimeError(
            f"CI test suite skipped {len(result.skipped)} test(s); skips are forbidden: "
            f"{details}"
        )


def main() -> None:
    suite = unittest.defaultTestLoader.discover(str(PROJECT_ROOT / "tests"))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    try:
        enforce_ci_result(result)
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc
    print(
        json.dumps(
            {
                "status": "passed",
                "tests_run": result.testsRun,
                "skipped": len(result.skipped),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
