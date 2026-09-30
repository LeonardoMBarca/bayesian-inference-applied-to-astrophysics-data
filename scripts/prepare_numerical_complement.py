"""Create a new bounded numerical study; never launches inference."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from publication.numerical_campaign import CAMPAIGN_ID, prepare_study  # noqa: E402

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--campaign-id", default=CAMPAIGN_ID)
    parser.add_argument("--freeze-plan", action="store_true", help="Freeze a prepared study only after all sources and protocols are committed")
    arguments = parser.parse_args()
    if arguments.freeze_plan:
        from publication.campaign_plan import (
            build_plan,
            freeze_plan,
            source_identity,
            uncommitted_sources,
        )
        config_path = Path(f"configs/publication/{arguments.campaign_id}.json")
        plan = build_plan(ROOT, config_path)
        destination = ROOT / plan["frozen_plan_path"]
        if destination.exists():
            raise FileExistsError("Frozen ledger exists; preserve it and use a new campaign ID")
        if uncommitted_sources(ROOT, source_identity(ROOT)):
            raise ValueError("Commit tested sources before freezing the numerical ledger")
        errors = [error for error in plan["preflight_errors"] if not error.startswith("Frozen campaign plan unavailable: [Errno 2]")]
        if errors:
            raise ValueError("; ".join(errors))
        print(freeze_plan(ROOT, config_path))
    else:
        print(prepare_study(ROOT, arguments.campaign_id))
