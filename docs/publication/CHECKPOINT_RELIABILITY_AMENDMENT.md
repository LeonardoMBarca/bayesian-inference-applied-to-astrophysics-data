# Operational amendment: Windows/WSL checkpoint reliability

Date: 2026-09-27. Campaign: `tcc_campaign_v1`.

## Incident and acceptance criteria

The controller exited with code 1 while its scientific child completed normally.
The retained tmux pane proves `PermissionError: [Errno 13] Permission denied`
at `campaign._atomic_json -> os.replace(temporary, campaign_state.json)` on
`/mnt/c`. A persisted `RUNNING` checkpoint was therefore not live-process evidence.
The observed incident occurred at 03:08:38 UTC. Sealed outputs must not be repeated.

Acceptance requires: real Windows/WSL reproduction, atomic recovery after brief
locks, a nonblocking monitor, truthful liveness, preserved scientific identities,
and passing regression/integration/stop/resume/idempotence checks before resume.

## Mechanism and repair

Windows handles without delete sharing can block rename/replacement. The old
ad-hoc PowerShell monitor used `Get-Content`; both copies were stopped before
resuming science. The exact offending handle was not captured at the instant
of failure. The controlled FileShare experiment reproduces the same failure
class, not proof that no antivirus/editor could ever cause it.

- `_atomic_json` retains the complete fsynced candidate and retries only access,
  sharing and busy replacement errors, with backoff and a 12-second bound.
- There is no truncate/in-place fallback or deletion of the old checkpoint.
  ENOSPC/EIO and persistent failures remain errors, never successful saves.
- The replacement monitor uses read-only `FileShare.ReadWrite | FileShare.Delete`
  handles, disposed before parsing. It follows active logs, not all history.
- `--status` reports persisted status separately from `effective_status`,
  checkpoint age and reuse-resistant controller/worker liveness.
- The monitor's optional `-KeepAwake` requests only prevention of automatic
  sleep. It does not alter the power plan or override shutdown/manual sleep.

Primary references: [Microsoft CreateFile sharing rules](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew),
[FileShare.Delete](https://learn.microsoft.com/en-us/dotnet/api/system.io.fileshare)
and [SetThreadExecutionState](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-setthreadexecutionstate).

## Scientific boundary

The original final config, ledger, protocols, model, likelihood, priors, gates,
draws, targets, seeds and replicate counts remain unchanged. The historical
`scientific_003` baseline is untouched.

`publication/runtime_amendments/tcc_campaign_v1.json` separately authorizes exact
reviewed SHA-256 changes only to `campaign.py` and `campaign_plan.py`. It binds
the immutable original ledger, source commit and committed validation evidence,
and enforces append-only Git history. Other Python sources remain exactly frozen.
The ledger is also compared byte-for-byte with the original campaign initialization
commit, not its first prelaunch draft. An amendment cannot legitimize a rewritten
scientific ledger. Missing initialization state in an existing campaign namespace
fails closed instead of being treated as a new campaign.
Changes to inference/simulation/data/reporting/protocols are not permitted by
this operational exception. Accepted amendments are recorded in the journal;
old runs retain their code identity and new attempts record the new commit.

## Validation

```powershell
powershell -NoProfile -File tests/manual/validate_checkpoint_sharing.ps1
```

The isolated fixture reproduces the old sharing violation, recovers after lock
release, replaces the checkpoint with a delete-shared reader still open, and
stress-tests 200 atomic writes against concurrent readers. It never writes to
the final campaign. Two preliminary harness-launch attempts are retained under
`artifacts/checkpoint-sharing-*`; they failed due to WSL command quoting/exit-code
capture, not scientific inference. The corrected third fixture passed.

Acceptance bundle: `publication/validation/checkpoint_repair_v1/validation.json`,
including test logs, integration results and the preserved-run checksum inventory.
`runner_smoke_checkpoint_v1` is engineering smoke, not final scientific evidence.
The final guard was additionally checked by
`publication/validation/checkpoint_repair_v2/validation.json`: a new complete
practical suite and baseline validation, with the physical smoke reused only after
verifying that `campaign_plan.py` was the sole changed Python source. The controller,
worker and inference were byte-identical to the passing v1 smoke.

Final acceptance: **242 tests passed, zero skips**, Ruff and static validation
passed, the historical hardened baseline validator passed, and all 52 sealed
final completions present before repair passed checksum validation. The physical
smoke verified graceful stop, resume, idempotence, technical-failure preservation
and scientific-rejection non-retry. Its six attempts for five engineering jobs
are not additional final scientific replicates.

Implementation commit: `f5a4851e37cc87f148c8234678e92c8aed06aad8`.
Runtime-authorization commit: `bd05deeb66782b0f0de2db1f149a18595b2648ee`.
The post-commit dry-run accepted the amendment with no preflight errors and
the same 117 declared jobs. No original ledger was refrozen.

## Separate WSL shutdown observed during live acceptance

`checkpoint_repair_v2/post_resume.json` records a point-in-time passing check at
04:07:36 UTC: the orphan was adopted, the next worker was live, the heartbeat was
fresh, and all 52 pre-repair sealed manifests/results were unchanged. This is not
a claim that the process stayed alive indefinitely.

At 04:07:53 UTC the Ubuntu instance received an orderly system-level poweroff;
the controller recorded `signal:SIGTERM` and the unfinished next attempt became
`CANCELLED`. The Windows host itself did not reboot. The requesting actor was not
identified: do not attribute this to the user, memory exhaustion, or idle timeout
without further evidence. This is distinct from the repaired sharing violation.
The interruption audit is retained beside the point-in-time validation.

The Windows background launcher therefore retains an attached `wsl.exe` client
for the controller's entire lifetime, and requests automatic-sleep prevention in
its hidden supervisor rather than relying on the visible monitor. It does not
change global WSL/power settings, configure a service, or automatically retry
science. Closing only the monitor does not close that supervisor. The scientific
runner still owns locking, graceful stop, budgets and explicit resume of cancelled
attempts in new attempt directories with the same seeds.

Microsoft documents that [systemd services alone do not keep a WSL instance alive](https://learn.microsoft.com/en-us/windows/wsl/systemd).
That lifecycle limitation motivates the persistent client; it does not prove the
initiator of this observed poweroff.

## Limits

This does not promise continuity through disk failure, full disk, permanent
permission denial, manual process termination, shutdown or power loss. The
36-hour soft budget and graceful-stop behavior remain in force. An unbounded
restart loop is deliberately not added: it could hide persistent failures or
repeat interrupted work. The campaign still advances without Codex or an LLM.
