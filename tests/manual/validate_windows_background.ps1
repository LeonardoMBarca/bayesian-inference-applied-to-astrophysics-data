<# Engineering only: temporary fake runner, no scientific imports, data or MCMC. #>
[CmdletBinding()]
param([string]$RepoRoot, [string]$EvidencePath)
$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
function Read-TestText([string]$Path) {
    $stream = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read,
        ([System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete))
    $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose(); $stream.Dispose() }
}
$fixture = Join-Path ([System.IO.Path]::GetTempPath()) ('publication background test ' + [guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $fixture)
[void](New-Item -ItemType Directory -Path (Join-Path $fixture 'scripts'))
[void](New-Item -ItemType Directory -Path (Join-Path $fixture 'configs'))
$utf8 = [System.Text.UTF8Encoding]::new($false)
# Generated fixtures belong only to this unique temporary directory.
[System.IO.File]::WriteAllText((Join-Path $fixture 'configs/delay only.json'),
    '{"campaign_id":"windows_background_fixture","mode":"engineering_delay_only","runtime":{"scientific_python":"/usr/bin/python3","wsl_distribution":"Ubuntu-24.04"}}', $utf8)
[System.IO.File]::WriteAllText((Join-Path $fixture 'scripts/run_publication_campaign.py'), @'
import argparse, json, os, pathlib, sys, time
parser = argparse.ArgumentParser()
parser.add_argument("--config", required=True)
parser.add_argument("--resume", action="store_true")
args = parser.parse_args()
assert args.resume
assert json.loads(pathlib.Path(args.config).read_text())["mode"] == "engineering_delay_only"
print(json.dumps({"event":"start", "cwd":os.getcwd(), "pid":os.getpid(), "config":args.config}), flush=True)
print("engineering_stderr", file=sys.stderr, flush=True)
time.sleep(95)
print("engineering_finished_without_science", flush=True)
'@, $utf8)
[System.IO.File]::WriteAllText((Join-Path $fixture 'monitor_state.json'),
    '{"campaign_id":"windows_background_fixture","status":"RUNNING","updated_at_utc":"2000-01-01T00:00:00Z","jobs":{}}', $utf8)
$launcher = Join-Path $RepoRoot 'scripts/start_publication_campaign_background.ps1'
$launchOut = Join-Path $fixture 'launcher.stdout.json'
$launchErr = Join-Path $fixture 'launcher.stderr.log'
$launchArgs = '-NoProfile -File "' + $launcher + '" -RepoRoot "' + $fixture + '" -Config "configs/delay only.json"'
$launcherProcess = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $launchArgs `
    -WindowStyle Hidden -PassThru -RedirectStandardOutput $launchOut -RedirectStandardError $launchErr
$launcherHandle = $launcherProcess.Handle
if (-not $launcherProcess.WaitForExit(15000)) { throw 'Launcher did not return independently.' }
if ($launcherProcess.ExitCode -ne 0) { throw 'Launcher failed.' }
$launchDirectory = Get-ChildItem -LiteralPath (Join-Path $fixture 'logs/publication_campaign/windows_background_fixture') -Directory | Select-Object -First 1
$launch = (Read-TestText (Join-Path $launchDirectory.FullName 'launch.json')) | ConvertFrom-Json
$launcherExitedAt = [DateTimeOffset]::UtcNow
$startedPath = Join-Path $launch.log_directory 'supervisor.started.json'
for ($retry = 0; $retry -lt 30 -and -not [System.IO.File]::Exists($startedPath); $retry++) { Start-Sleep -Seconds 1 }
$started = (Read-TestText $startedPath) | ConvertFrom-Json
$monitorPath = Join-Path $RepoRoot 'scripts/watch_publication_campaign.ps1'
$monitorArgs = '-NoProfile -File "' + $monitorPath + '" -RepoRoot "' + $fixture + '" -StatePath monitor_state.json'
$monitor = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') -ArgumentList $monitorArgs -WindowStyle Hidden -PassThru
Start-Sleep -Seconds 2
$monitor.Refresh()
if ($monitor.HasExited) { throw 'Fixture monitor did not stay open.' }
# Only the monitor created by this test is closed. Never touch a real campaign/monitor.
Stop-Process -Id $monitor.Id
$monitorClosedAt = [DateTimeOffset]::UtcNow
Write-Output "Fixture launcher exited; monitor $($monitor.Id) closed. Waiting >60 seconds."
Start-Sleep -Seconds 32
Start-Sleep -Seconds 32
$verifiedAt = [DateTimeOffset]::UtcNow
$supervisor = Get-Process -Id $launch.supervisor_pid -ErrorAction Stop
$wslClient = Get-Process -Id $started.wsl_client_pid -ErrorAction Stop
if ($supervisor.ProcessName -ne 'powershell' -or $wslClient.ProcessName -ne 'wsl') { throw 'Wrong process identity.' }
if ([Math]::Abs(($wslClient.StartTime.ToUniversalTime() - [DateTimeOffset]::Parse($started.wsl_client_start_utc).UtcDateTime).TotalSeconds) -gt 1) { throw 'WSL PID reused.' }
$exitPath = Join-Path $launch.log_directory 'supervisor.exit.json'
for ($retry = 0; $retry -lt 60 -and -not [System.IO.File]::Exists($exitPath); $retry++) { Start-Sleep -Seconds 1 }
$exitRecord = (Read-TestText $exitPath) | ConvertFrom-Json
$controllerOut = Read-TestText (Join-Path $launch.log_directory 'controller.stdout.log')
$controllerErr = Read-TestText (Join-Path $launch.log_directory 'controller.stderr.log')
if ($exitRecord.exit_code -ne 0 -or $exitRecord.error -or $exitRecord.keep_awake_release_confirmed -ne $true) { throw 'Supervisor did not exit/release successfully.' }
if ($controllerOut -notmatch 'engineering_finished_without_science' -or $controllerErr -notmatch 'engineering_stderr') { throw 'Fixture output was not captured.' }
$evidence = [ordered]@{
    schema_version = 'publication-windows-background-validation-v1'; status = 'PASS'
    validated_at_utc = [DateTimeOffset]::UtcNow.ToString('o'); scientific_runs_executed = 0
    launcher_sha256 = (Get-FileHash -LiteralPath $launcher -Algorithm SHA256).Hash.ToLowerInvariant()
    validation_script_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    fixture_root = $fixture; log_directory = $launch.log_directory
    launcher_exited_at_utc = $launcherExitedAt.ToString('o'); monitor_closed_at_utc = $monitorClosedAt.ToString('o')
    supervisor_and_wsl_alive_at_utc = $verifiedAt.ToString('o')
    survival_after_monitor_close_seconds = ($verifiedAt - $monitorClosedAt).TotalSeconds
    monitor_pid = $monitor.Id; supervisor_pid = $supervisor.Id; wsl_client_pid = $wslClient.Id
    keep_awake_release_confirmed = $exitRecord.keep_awake_release_confirmed
    controller_exit_code = $exitRecord.exit_code; paths_with_spaces_verified = $true
    stdout_and_stderr_verified = $true; automatic_restart = $false
    limitation = 'Engineering lifetime test, not proof against manual suspension, logoff, forced WSL shutdown or host failure.'
}
$json = $evidence | ConvertTo-Json -Depth 8
if ($EvidencePath) {
    $outputStream = [System.IO.FileStream]::new([System.IO.Path]::GetFullPath($EvidencePath), [System.IO.FileMode]::CreateNew)
    $writer = [System.IO.StreamWriter]::new($outputStream, $utf8)
    try { $writer.WriteLine($json) } finally { $writer.Dispose(); $outputStream.Dispose() }
}
$json
