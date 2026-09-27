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

## Limits

This does not promise continuity through disk failure, full disk, permanent
permission denial, manual process termination, shutdown or power loss. The
36-hour soft budget and graceful-stop behavior remain in force. An unbounded
restart loop is deliberately not added: it could hide persistent failures or
repeat interrupted work. The campaign still advances without Codex or an LLM.
