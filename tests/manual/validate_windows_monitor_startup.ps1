<# Windows PowerShell 5.1 regression: default repo resolution under -NoExit -File. #>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [string]$RepoRoot
)

$ErrorActionPreference = 'Stop'
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot) }
$RepoRoot = [System.IO.Path]::GetFullPath($RepoRoot)
$outputRoot = [System.IO.Path]::GetFullPath((Join-Path $RepoRoot $OutputDirectory))
$repoPrefix = $RepoRoot.TrimEnd([char[]]'\/') + [System.IO.Path]::DirectorySeparatorChar
if (-not $outputRoot.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Evidence must be created in an isolated directory below the repository.'
}
if (Test-Path -LiteralPath $outputRoot) { throw "Evidence directory already exists: $outputRoot" }
[void][System.IO.Directory]::CreateDirectory($outputRoot)
$utf8 = [System.Text.UTF8Encoding]::new($false)
$monitor = Join-Path $RepoRoot 'scripts/watch_publication_campaign.ps1'
$state = Join-Path $outputRoot 'fixture_state.json'
$relativeState = $state.Substring($repoPrefix.Length).Replace('\', '/')
$fixture = @{
    campaign_id = 'monitor_startup_fixture'; status = 'COMPLETED'; controller_pid = 0
    updated_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    jobs = @{ fixture = @{ job_id = 'fixture'; status = 'COMPLETED'; attempts = @() } }
}
[System.IO.File]::WriteAllText($state, ($fixture | ConvertTo-Json -Depth 6), $utf8)
$outside = Join-Path ([System.IO.Path]::GetTempPath()) ('monitor-startup-' + [guid]::NewGuid().ToString('N'))
[void][System.IO.Directory]::CreateDirectory($outside)
$hostExecutable = Join-Path $env:SystemRoot 'System32/WindowsPowerShell/v1.0/powershell.exe'
$share = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete

function Read-Output([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return '' }
    $stream = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $share)
    $reader = [System.IO.StreamReader]::new($stream)
    try { return $reader.ReadToEnd() } finally { $reader.Dispose(); $stream.Dispose() }
}

function Invoke-Probe([string]$Name, [string]$Script, [string]$ExtraArguments, [bool]$ExpectFailure) {
    $stdout = Join-Path $outputRoot "$Name.stdout.log"
    $stderr = Join-Path $outputRoot "$Name.stderr.log"
    $arguments = '-NoLogo -NoProfile -NoExit -File "{0}" {1}' -f $Script, $ExtraArguments
    $process = Start-Process -FilePath $hostExecutable -ArgumentList $arguments -WorkingDirectory $outside `
        -WindowStyle Hidden -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
    $null = $process.Handle
    $started = $process.StartTime
    $outText = ''; $errText = ''
    try {
        $deadline = [DateTime]::UtcNow.AddSeconds(20)
        do {
            Start-Sleep -Milliseconds 100
            $outText = Read-Output $stdout
            $errText = Read-Output $stderr
            if ($ExpectFailure) {
                $ready = $errText -match 'Split-Path|ParameterArgumentValidationErrorEmptyStringNotAllowed'
            } else {
                $ready = $outText -match 'COMPLETED=1'
            }
            if ($ready -or $process.HasExited) { break }
        } while ([DateTime]::UtcNow -lt $deadline)
        if ($ExpectFailure) {
            if (-not $ready) { throw "$Name did not reproduce the original startup failure." }
        } else {
            if (-not $ready -or -not $outText.Contains('Monitor somente leitura') -or
                -not $outText.Contains("Estado: $state") -or $errText.Trim()) {
                throw "$Name failed startup validation. See $stdout and $stderr."
            }
        }
        return @{
            name = $Name; status = 'PASS'; expected_startup_failure = $ExpectFailure
            command = 'powershell.exe ' + $arguments; working_directory_outside_repo = $true
            expected_state_path = $state; no_exit_host_was_running = -not $process.HasExited
            stdout = "$OutputDirectory/$Name.stdout.log"; stderr = "$OutputDirectory/$Name.stderr.log"
        }
    } finally {
        # This is only the exact hidden child created above, never a campaign/monitor PID lookup.
        if (-not $process.HasExited) {
            $sameProcess = Get-Process -Id $process.Id -ErrorAction SilentlyContinue
            if ($null -ne $sameProcess -and $sameProcess.StartTime -eq $started -and
                $sameProcess.Path -eq $hostExecutable) {
                Stop-Process -InputObject $sameProcess -Force
                $process.WaitForExit()
            } else { throw 'Refusing to terminate a process whose creation identity changed.' }
        }
        $process.Dispose()
    }
}

# Minimal faithful reproducer of the original parameter-default bug, kept away from live code.
$oldProbe = Join-Path $outputRoot 'old_parameter_default_probe.ps1'
$oldText = @'
[CmdletBinding()]
param([string]$RepoRoot = (Split-Path -Parent $PSScriptRoot))
Write-Host "resolved=$RepoRoot"
'@
[System.IO.File]::WriteAllText($oldProbe, $oldText, $utf8)
$cases = @()
$cases += Invoke-Probe 'old_default_reproduced' $oldProbe '' $true
$cases += Invoke-Probe 'default_repo_root' $monitor ('-Once -StatePath "{0}"' -f $relativeState) $false
$cases += Invoke-Probe 'explicit_repo_root' $monitor ('-Once -StatePath "{0}" -RepoRoot "{1}"' -f $relativeState, $RepoRoot) $false
$evidence = @{
    schema_version = 'windows-monitor-startup-validation-v1'; status = 'PASS'
    tested_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
    host = $hostExecutable; host_version = [System.Diagnostics.FileVersionInfo]::GetVersionInfo($hostExecutable).FileVersion
    monitor_path = 'scripts/watch_publication_campaign.ps1'
    monitor_sha256 = (Get-FileHash -LiteralPath $monitor -Algorithm SHA256).Hash.ToLowerInvariant()
    no_scientific_execution = $true; no_live_state_read = $true; cases = $cases
}
[System.IO.File]::WriteAllText((Join-Path $outputRoot 'validation.json'), ($evidence | ConvertTo-Json -Depth 10), $utf8)
Write-Output ($evidence | ConvertTo-Json -Depth 10)
