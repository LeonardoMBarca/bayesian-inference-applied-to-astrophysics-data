param(
    [string]$RepoRoot = (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)),
    [string]$Distribution = 'Ubuntu-24.04',
    [string]$Python = '/home/leonardo_barca/mc3/bin/python3.14'
)
$ErrorActionPreference = 'Stop'
$fixtureRoot = Join-Path $RepoRoot ('artifacts/checkpoint-sharing-' + [guid]::NewGuid().ToString('N'))
[void](New-Item -ItemType Directory -Path $fixtureRoot)
$fixturePath = Join-Path $fixtureRoot 'campaign_state.json'
$linuxFixture = (& wsl.exe -d $Distribution -- wslpath -a $fixtureRoot).Trim()
$utf8 = [Text.UTF8Encoding]::new($false)
$checks = [ordered]@{}

function Reset-Fixture {
    [IO.File]::WriteAllText($fixturePath, '{"fixture":"checkpoint-sharing","sequence":0,"complete":true}', $utf8)
}
function Read-SharedText([string]$Path) {
    $stream = [IO.FileStream]::new($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read,
        ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
    $reader = $null
    try { $reader = [IO.StreamReader]::new($stream); return $reader.ReadToEnd() }
    finally { if ($reader) { $reader.Dispose() } else { $stream.Dispose() } }
}
function Start-Probe([string]$Mode, [string]$Label) {
    $arguments = '-d {0} -- {1} tests/manual/checkpoint_sharing_probe.py --directory "{2}" --mode {3}' -f $Distribution, $Python, $linuxFixture, $Mode
    $child = Start-Process -FilePath wsl.exe -ArgumentList $arguments -WorkingDirectory $RepoRoot -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $fixtureRoot ($Label + '.stdout.log')) `
        -RedirectStandardError (Join-Path $fixtureRoot ($Label + '.stderr.log'))
    $null = $child.Handle # Retain native handle so ExitCode survives a quick exit.
    return $child
}
function Finish-Probe($Process, [int]$ExpectedCode) {
    if (-not $Process.WaitForExit(60000)) { throw 'Probe timed out (only fixture process, no scientific work)' }
    $Process.Refresh()
    if ($Process.ExitCode -ne $ExpectedCode) { throw ('Unexpected probe exit {0}, expected {1}' -f $Process.ExitCode, $ExpectedCode) }
}

Reset-Fixture
$blocking = [IO.FileStream]::new($fixturePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
try { $probe = Start-Probe 'raw' 'baseline'; Finish-Probe $probe 13 }
finally { $blocking.Dispose() }
if ((Read-SharedText $fixturePath | ConvertFrom-Json).sequence -ne 0) { throw 'Old checkpoint was not preserved' }
$checks['unshared_delete_reproduces_original_permission_error'] = $true

Reset-Fixture
$blocking = [IO.FileStream]::new($fixturePath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
try {
    $probe = Start-Probe 'retry' 'retry'
    $deadline = [DateTime]::UtcNow.AddSeconds(8)
    $sawRetry = $false
    while ([DateTime]::UtcNow -lt $deadline -and -not $probe.HasExited) {
        $log = Join-Path $fixtureRoot 'retry.stderr.log'
        if ((Test-Path $log) -and (Read-SharedText $log) -match '(?i)retry|transient|blocked') { $sawRetry = $true; break }
        Start-Sleep -Milliseconds 50
    }
    if (-not $sawRetry) { throw 'Did not observe the real sharing violation retry' }
    Start-Sleep -Milliseconds 300
} finally { $blocking.Dispose() }
Finish-Probe $probe 0
if ((Read-SharedText $fixturePath | ConvertFrom-Json).sequence -ne 1) { throw 'Retry did not commit the full checkpoint' }
$checks['real_lock_release_recovers_without_restart'] = $true

Reset-Fixture
$sharing = [IO.FileStream]::new($fixturePath, [IO.FileMode]::Open, [IO.FileAccess]::Read,
    ([IO.FileShare]::ReadWrite -bor [IO.FileShare]::Delete))
try { $probe = Start-Probe 'retry' 'delete_shared'; Finish-Probe $probe 0 }
finally { $sharing.Dispose() }
$checks['delete_shared_reader_does_not_block_replace'] = $true

Reset-Fixture
$probe = Start-Probe 'stress' 'stress'
$reads = 0
$deadline = [DateTime]::UtcNow.AddSeconds(60)
while (-not $probe.HasExited -and [DateTime]::UtcNow -lt $deadline) {
    try {
        $snapshot = Read-SharedText $fixturePath | ConvertFrom-Json
        if (-not $snapshot.complete -or $snapshot.fixture -ne 'checkpoint-sharing') { throw 'Partial/invalid checkpoint' }
        $reads++
    } catch [IO.FileNotFoundException] { } # bounded DrvFS rename visibility gap
    Start-Sleep -Milliseconds 10
}
Finish-Probe $probe 0
if ((Read-SharedText $fixturePath | ConvertFrom-Json).sequence -ne 200 -or $reads -lt 2) { throw 'Stress fixture did not complete' }
$checks['concurrent_reader_200_atomic_writes_no_partial_json'] = $true
$result = [ordered]@{status='PASS'; kind='windows_wsl_checkpoint_integration_not_science';
    utc=[DateTimeOffset]::UtcNow.ToString('o'); fixture_directory=$fixtureRoot; checks=$checks; concurrent_reads=$reads}
[IO.File]::WriteAllText((Join-Path $fixtureRoot 'validation.json'), ($result | ConvertTo-Json -Depth 6), $utf8)
$result | ConvertTo-Json -Depth 6
