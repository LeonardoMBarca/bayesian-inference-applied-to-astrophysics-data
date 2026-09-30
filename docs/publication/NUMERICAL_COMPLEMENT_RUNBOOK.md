# Optional numerical complement: prepared, not executed

Campaign: `tcc_numerical_complement_v1`.
Configuration: `configs/publication/tcc_numerical_complement_v1.json`.
It uses the existing campaign engine, checkpoints, seed ledger, completion
sealing, resource limits, logs, interruption/resume and scientific rejection
handling. It is not a replacement for the historical 117+400 jobs.

## Fixed prospective design

| Family | New jobs | Question |
|---|---:|---|
| PUB-02 | 12 | Two representative regimes, three NEW simulated datasets each, direct vs equivalent standardized t0 coordinate |
| PUB-03 | 3 | Three independent local Monte Carlo streams on the SAME historical observational input and matched physical prior |
| PUB-04 | 9 | Three NEW long-cadence offset datasets, standardized baseline vs increased numerical accuracy; high-accuracy integrated vs instantaneous exposure |

There are nine new synthetic datasets, not 21 independent datasets: variants
within a pair share their generation seed and input bytes. All inference seeds
are distinct and fixed before any final outcome. The three PUB-03 fits reuse
ONE historical juliet posterior explicitly; no external inference is repeated
and this is not three independent external validations. The old external
temporal PPC rejection remains part of the interpretation.

The PUB-04 exposure contrast uses the **high-accuracy baseline**, not the
lower-accuracy baseline. High accuracy means 2,000 tune + 2,000 draws per chain,
four chains, target_accept .99. P2 uses 1,000 + 1,000, four chains, .95; the
benchmark retains 2,000 + 2,000, four chains, .97. All save warmup for the
mechanism investigation. Priors, input identity and gates are not relaxed.

Only the mathematical coordinate changes for the P2 pair: z~Normal(0,1),
t0=.025*z. Physical t0 is still Normal(0,.025 days). No truth initialization,
chain wrapping/removal, seed substitution, observational clipping or retuning
to juliet is allowed. Coordinate equivalence tests precede final execution.

Three datasets per design support a bounded numerical investigation, NOT a
precise calibration claim or proof that aliases can never occur. All failures
and missing pairs remain explicit. The protocol states rejection conditions
and the alias-review rule before new results.

## Runtime budget, not an ETA promise

The config includes every input hash and timing used in the estimate: all 20
historical deep-short attempts, 20 intermediate-long, three long-offset
baselines and the one local benchmark. Rejected attempts were not excluded.
Their median worker times were approximately 162 s, 52 s, 102 s and 1,906 s,
respectively, with four cores.

At the declared **one worker / two cores**, a linear resource-scaling
sensitivity and a factor-four allowance for longer high-accuracy fits give
about **5.4 hours** using those medians, or **6.3 hours** using the respective
observed maxima. These are planning calculations, NOT measured performance of
the new coordinate or a confidence interval. The benchmark has only one timing
observation. Compilation, load, deeper NUTS trees and the .99 setting can make
execution considerably longer. The soft budget is 20 hours; it stops starting
new jobs near the limit, lets active work finish and checkpoints remaining
jobs for a later resume. No final batch is launched during implementation.

## Freeze and launch

The coordinator first commits tested source/protocol/config files, then runs:

```text
python scripts/prepare_numerical_complement.py --freeze-plan
```

That command refuses uncommitted sources, protocol mismatch and an existing
ledger. Commit `configs/publication/tcc_numerical_complement_v1_plan.json`
before final execution. Any later scientific/config/source change must be
reviewed before launch; do not bypass preflight or edit a frozen ledger in place.

The user-facing commands, from the repository root, are:

```text
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --dry-run
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --status
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --resume
```

On Windows the wrapper routes to the configured WSL interpreter. The existing
detached Windows supervisor and visible log monitor accept this new identity:

```powershell
powershell.exe -NoProfile -File scripts/start_publication_campaign_background.ps1 -Config configs/publication/tcc_numerical_complement_v1.json
powershell.exe -NoProfile -File scripts/watch_publication_campaign.ps1 -CampaignId tcc_numerical_complement_v1
```

In VS Code, choose **Terminal → Run Task → Numerical complement: Dry Run**
first. The `Numerical complement:` tasks also expose Run / Resume, Status,
Stop gracefully, Aggregate Results, Background (Windows), and Logs (Windows).
The older Publication/Calibration tasks retain their historical campaign IDs;
do not use those to start this new study.

Alternatively in Linux/WSL, use a persistent terminal session:

```sh
tmux new -s tcc-numerical
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --resume
```

Detach with Ctrl-b, then d; reconnect with `tmux attach -t tcc-numerical`.
tmux protects against closing the terminal, not computer shutdown or WSL
termination. After such interruption, use the same `--resume` command; finished
sealed runs are not silently repeated.

Stop safely and aggregate without sampling:

```text
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --stop
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --aggregate
python scripts/run_publication_campaign.py --config configs/publication/tcc_numerical_complement_v1.json --verify
```

Outputs are isolated under
`artifacts/publication_campaign/tcc_numerical_complement_v1/`, logs under
`logs/publication_campaign/tcc_numerical_complement_v1/`, and automatically
sealed aggregate reports under
`reports/publication_campaign/tcc_numerical_complement_v1/`.

Do not change replicate counts, priors, accuracy, scenarios or seeds to obtain
a passing result. Budget/concurrency changes are operational; a different
scientific study requires a new campaign ID/protocol/ledger. Numeric agreement
alone cannot authorize astrophysical parameter claims.
