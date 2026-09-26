from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from publication.batch import attempt_seeds  # noqa: E402
from publication.contracts import RunIdentity, deterministic_seed  # noqa: E402


class BatchSeedTests(unittest.TestCase):
    def test_pilot_and_final_can_never_reuse_the_same_seed_namespace(self):
        pilot = RunIdentity("PUB-02", "shallow_short", "rep_0000", "pilot_001")
        final = RunIdentity("PUB-02", "shallow_short", "rep_0000", "final_001")
        old_pilot = deterministic_seed("PUB-02", "shallow_short", "rep_0000", "generation")
        pilot_seed = attempt_seeds(pilot, pilot=True)["generation"]
        final_seed = attempt_seeds(final, pilot=False)["generation"]
        self.assertEqual(len({old_pilot, pilot_seed, final_seed}), 3)

    def test_final_seed_not_changed_to_choose_a_better_retry(self):
        first = RunIdentity("PUB-02", "shallow_short", "rep_0000", "final_001")
        second = RunIdentity("PUB-02", "shallow_short", "rep_0000", "final_002")
        self.assertEqual(attempt_seeds(first, pilot=False), attempt_seeds(second, pilot=False))

    def test_declared_six_by_hundred_generation_seeds_have_no_collisions(self):
        scenarios = ("deep_short", "intermediate_long", "shallow_short", "near_limit_long", "shallow_ou_weak", "shallow_ou_strong")
        seeds = [attempt_seeds(RunIdentity("PUB-02", scenario, f"rep_{rep:04d}", "final_001"), pilot=False)["generation"]
                 for scenario in scenarios for rep in range(100)]
        self.assertEqual(len(set(seeds)), 600)


if __name__ == "__main__":
    unittest.main()
