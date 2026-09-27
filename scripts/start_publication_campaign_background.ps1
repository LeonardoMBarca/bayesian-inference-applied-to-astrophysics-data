<# Windows-only lifetime wrapper. Scientific decisions remain in the locked Python runner. #>
[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$Config = 'configs/publication/tcc_final_campaign.json',
    [Parameter(DontShow)][switch]$Supervisor,
    [Parameter(DontShow)][string]$LaunchDirectory
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
$resolvedRepo = [System.IO.Path]::GetFullPath($RepoRoot).TrimEnd([char[]]'\/')
$repoPrefix = $resolvedRepo + [System.IO.Path]::DirectorySeparatorChar
$configPath = if ([System.IO.Path]::IsPathRooted($Config)) {
    [System.IO.Path]::GetFullPath($Config)
} else { [System.IO.Path]::GetFullPath((Join-Path $resolvedRepo $Config)) }
if (-not $configPath.StartsWith($repoPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Config must be a file inside RepoRoot.'
}
$configRelative = $configPath.Substring($repoPrefix.Length).Replace('\', '/')
$settings = [System.IO.File]::ReadAllText($configPath, [System.Text.Encoding]::UTF8) | ConvertFrom-Json
$campaignId = [string]$settings.campaign_id
if ($campaignId -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]*$') { throw 'Invalid campaign ID.' }
$scientificPython = [string]$settings.runtime.scientific_python
$distribution = [string]$settings.runtime.wsl_distribution
if (-not $scientificPython.StartsWith('/') -or -not $distribution -or
    $scientificPython.Contains([char]0) -or $distribution.Contains([char]0)) {
    throw 'Config must declare an absolute Linux scientific_python and wsl_distribution.'
}
if (-not [System.IO.File]::Exists((Join-Path $resolvedRepo 'scripts/run_publication_campaign.py'))) {
    throw 'Campaign runner not found in RepoRoot.'
}
$logRoot = Join-Path $resolvedRepo "logs/publication_campaign/$campaignId"

function Quote-PowerShellLiteral([string]$Value) { return "'" + $Value.Replace("'", "''") + "'" }
function Quote-NativeArgument([string]$Value) {
    # Start-Process joins ArgumentList: supply one correctly quoted Windows command line.
    # WSL's option parser rejects unnecessarily quoted option names (for example "--cd").
    if ($Value -and $Value -notmatch '[\s"]') { return $Value }
    $escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $escaped = [regex]::Replace($escaped, '(\\+)$', '$1$1')
    return '"' + $escaped + '"'
}
function Write-NewJson([string]$Path, $Value) {
    $stream = $null
    $writer = $null
    try {
        $stream = [System.IO.FileStream]::new($Path, [System.IO.FileMode]::CreateNew,
            [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
        $writer = [System.IO.StreamWriter]::new($stream, [System.Text.UTF8Encoding]::new($false))
        $writer.WriteLine(($Value | ConvertTo-Json -Depth 8))
    } finally {
        if ($null -ne $writer) { $writer.Dispose() }
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

if (-not $Supervisor) {
    $launchId = [DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfffZ') + '_' + [guid]::NewGuid().ToString('N')
    [void][System.IO.Directory]::CreateDirectory($logRoot)
    $LaunchDirectory = Join-Path $logRoot $launchId
    [void](New-Item -ItemType Directory -Path $LaunchDirectory -ErrorAction Stop)
    $command = '& ' + (Quote-PowerShellLiteral $PSCommandPath) +
        ' -RepoRoot ' + (Quote-PowerShellLiteral $resolvedRepo) +
        ' -Config ' + (Quote-PowerShellLiteral $configRelative) +
        ' -Supervisor -LaunchDirectory ' + (Quote-PowerShellLiteral $LaunchDirectory)
    $encoded = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command))
    $process = Start-Process -FilePath (Join-Path $PSHOME 'powershell.exe') `
        -ArgumentList "-NoProfile -NonInteractive -OutputFormat Text -EncodedCommand $encoded" `
        -WorkingDirectory $resolvedRepo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput (Join-Path $LaunchDirectory 'supervisor.stdout.log') `
        -RedirectStandardError (Join-Path $LaunchDirectory 'supervisor.stderr.log')
    $launch = [ordered]@{
        schema_version = 'publication-windows-launch-v1'; launch_id = $launchId
        campaign_id = $campaignId; created_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        supervisor_pid = $process.Id; config = $configRelative; repo_root = $resolvedRepo
        log_directory = $LaunchDirectory; wsl_distribution = $distribution
        scientific_python = $scientificPython; action = '--resume'; automatic_restart = $false
    }
    Write-NewJson (Join-Path $LaunchDirectory 'launch.json') $launch
    $launch | ConvertTo-Json -Depth 8
    return
}

$LaunchDirectory = [System.IO.Path]::GetFullPath($LaunchDirectory)
$logPrefix = [System.IO.Path]::GetFullPath($logRoot).TrimEnd([char[]]'\/') + [System.IO.Path]::DirectorySeparatorChar
if (-not $LaunchDirectory.StartsWith($logPrefix, [System.StringComparison]::OrdinalIgnoreCase) -or
    -not [System.IO.Directory]::Exists($LaunchDirectory)) { throw 'Invalid supervisor launch directory.' }
$controllerOut = Join-Path $LaunchDirectory 'controller.stdout.log'
$controllerErr = Join-Path $LaunchDirectory 'controller.stderr.log'
foreach ($path in @($controllerOut, $controllerErr, (Join-Path $LaunchDirectory 'supervisor.started.json'),
                    (Join-Path $LaunchDirectory 'supervisor.exit.json'))) {
    if ([System.IO.File]::Exists($path)) { throw "Refusing to overwrite existing supervisor artifact: $path" }
}
$child = $null
$awake = $false
$exitCode = 1
$failure = $null
$startedAt = [DateTimeOffset]::UtcNow.ToString('o')
try {
    Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
namespace PublicationBackground {
    public static class NativePower {
        [DllImport("kernel32.dll")]
        public static extern uint SetThreadExecutionState(uint flags);
    }
}
'@
    $previous = [PublicationBackground.NativePower]::SetThreadExecutionState([uint32]2147483649)
    if ($previous -eq 0) { throw 'Cannot request temporary system-awake state; controller was not started.' }
    $awake = $true
    $arguments = @('--cd', $resolvedRepo, '-d', $distribution, '--exec', $scientificPython, '-u',
        'scripts/run_publication_campaign.py', '--config', $configRelative, '--resume')
    $commandLine = ($arguments | ForEach-Object { Quote-NativeArgument $_ }) -join ' '
    $child = Start-Process -FilePath (Join-Path $env:SystemRoot 'System32/wsl.exe') `
        -ArgumentList $commandLine -WorkingDirectory $resolvedRepo -WindowStyle Hidden -PassThru `
        -RedirectStandardOutput $controllerOut -RedirectStandardError $controllerErr
    $childHandle = $child.Handle
    Write-NewJson (Join-Path $LaunchDirectory 'supervisor.started.json') ([ordered]@{
        started_at_utc = $startedAt; supervisor_pid = $PID; wsl_client_pid = $child.Id
        wsl_client_start_utc = $child.StartTime.ToUniversalTime().ToString('o')
        keep_awake = 'ES_CONTINUOUS|ES_SYSTEM_REQUIRED'; arguments = $arguments
    })
    Write-Output "Supervisor $PID keeps WSL client $($child.Id) attached; no automatic restart."
    while (-not $child.WaitForExit(5000)) { }
    $child.WaitForExit()
    $exitCode = $child.ExitCode
    Write-Output "WSL client exited with code $exitCode."
} catch {
    $failure = $_.Exception.Message
    [Console]::Error.WriteLine($failure)
} finally {
    $released = $null
    if ($awake) {
        $released = [PublicationBackground.NativePower]::SetThreadExecutionState([uint32]2147483648) -ne 0
    }
    Write-NewJson (Join-Path $LaunchDirectory 'supervisor.exit.json') ([ordered]@{
        started_at_utc = $startedAt; finished_at_utc = [DateTimeOffset]::UtcNow.ToString('o')
        supervisor_pid = $PID; exit_code = $exitCode; error = $failure
        keep_awake_was_requested = $awake; keep_awake_release_confirmed = $released
        automatic_restart = $false
    })
    if ($null -ne $child) { $child.Dispose() }
}
exit $exitCode
