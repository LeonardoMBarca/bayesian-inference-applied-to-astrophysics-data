# Independent P2 precision extension (2026-09-27)

The user authorized `tcc_calibration_confirmatory_v1` after inspecting the
completed `tcc_campaign_v1` results. The new primary cohort has **100 new datasets
in each of the four original scenarios**, 400 runs total. This is prospective
confirmation of the unchanged workflow; the original results were already known
when the extension was chosen. It is not retrospective preregistration.

The authoritative specification is
`publication/protocols/PUB-02-confirmatory-v1.json`. It preserves the parent
scenario truth/design, inference assumptions, priors, sampler and gates exactly.
The original protocol, ledger, results and historical `scientific_003` remain
their own evidence. The protocol links the parent summary by SHA-256.

## Estimand and stopping rule

Primary estimates use only the new 400-run cohort, with all failures and
rejections accounted for under the inherited rules. The 80 parent simulations
remain a separate comparison cohort. No silent pooling, seed selection,
post-result sample-size adjustment, or stopping when coverage looks favorable.
The planned size is fixed at 100 per scenario regardless of outcomes.

Coverage is conditional repeated-sampling coverage at fixed truths, not SBC.
For planning, binomial standard errors at probabilities .50/.80/.94 decrease
from .112/.089/.053 at n=20 to .050/.040/.02375 at n=100. Actual coverage is
unknown before execution; Wilson95 intervals and interval widths are required.
High coverage alone does not establish precise or unbiased inference.

Any later pooled analysis must be explicitly secondary and disclose that the
extension was chosen after parent outcomes. Neither cohort validates correlated
noise modeling. The parent benchmark and observational rejections remain
important limitations; they are not replaced by more white-noise simulations.

## Compute allocation

The parent P2 result artifacts record mean inference wall times of approximately
144, 45, 206 and 148 seconds for deep_short, intermediate_long, shallow_short and
near_limit_long respectively (20 results each). These exclude some preparation
and orchestration overhead. Median complete-attempt timings imply approximately
17.2 hours for 400 new jobs. Paused/recovered attempts make raw elapsed-time
averages misleading; the estimates do not remove any result from science.

The config assigns 195/75/265/185 seconds per corresponding job, a conservative
**20-hour planning estimate**, not an ETA guarantee. The additional soft budget
is **22 hours**, with one worker using four cores. Together with the parent's
13.42 checkpointed hours this is within the earlier 36-hour compute envelope.
When dispatch would exceed the remaining budget, the runner finishes current
work, checkpoints and leaves remaining jobs PLANNED. An incomplete cohort must
be reported as incomplete; the cap is not increased automatically.

The new campaign namespace determines all generation/inference/predictive seeds
before execution. The launch validation checks no seed overlaps with the parent
ledger and that every output path/run ID is distinct. The generated integer
ledger, config and protocol must be committed before the first final inference.

## Commands

All commands start at the repository root on `publication-grade-validation`.
Use the locked scientific interpreter in WSL for Python commands:

```sh
python scripts/run_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --dry-run
python scripts/run_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --resume
python scripts/run_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --status
python scripts/run_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --stop
python scripts/run_publication_campaign.py --config configs/publication/tcc_calibration_confirmatory_v1.json --verify
```

The Windows background supervisor keeps its WSL client attached and requests
temporary system-awake state. Start it once, independently of the log window:

```powershell
powershell.exe -NoProfile -File scripts/start_publication_campaign_background.ps1 -Config configs/publication/tcc_calibration_confirmatory_v1.json
powershell.exe -NoProfile -NoExit -File scripts/watch_publication_campaign.ps1 -CampaignId tcc_calibration_confirmatory_v1
```

The monitor may be closed without stopping the supervisor. Manual shutdown,
logoff and power loss still stop computation; resume uses the same command and
preserves finished runs. See `BACKGROUND_WINDOWS.md` for operational details.

In Windows VS Code, use **Terminal > Run Task** and select
`Calibration 100x4: Background / Resume (Windows)` or
`Calibration 100x4: Logs (Windows)`. These tasks explicitly select the new
campaign; existing Publication tasks still refer to the original campaign.

State: `artifacts/publication_campaign/tcc_calibration_confirmatory_v1/`.
Logs: `logs/publication_campaign/tcc_calibration_confirmatory_v1/`.
Automatic final tables, figures and reports:
`reports/publication_campaign/tcc_calibration_confirmatory_v1/`.

Prelaunch engineering evidence is generated without final inference:

```sh
python tests/manual/validate_confirmatory_campaign.py --output publication/validation/confirmatory_launch_v1
```

Use a new evidence directory for each validation invocation. It verifies
unchanged science, separate seeds/paths, the locked environment and historical
baseline, existing parent report integrity, focused tests, and the actual CLI
dry-run. Runner/source implementations are unchanged by this extension.

## Launch record

The prelaunch validation passed on 2026-09-27 with 124 focused tests, zero
failures and zero skips; exact environment/baseline verification; parent report
integrity; and a 400-job CLI dry-run. The campaign was launched at
`2026-09-27T17:30:18Z` through the independent Windows supervisor, launch ID
`20260927T173017943Z_7bb0c9e112834c9cb0e2e3460c27e34a`. Initial state recorded
one RUNNING and 399 PLANNED jobs. This is an operational snapshot only; use the
machine-readable state for current progress and the final aggregate for results.
