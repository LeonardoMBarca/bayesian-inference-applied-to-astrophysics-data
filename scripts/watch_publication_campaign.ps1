<# Read-only monitor. No campaign command, restart, inference, or file write. #>
[CmdletBinding()]
param(
    [string]$RepoRoot,
    [string]$StatePath,
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]*$')]
    [string]$CampaignId = 'tcc_campaign_v1',
    [switch]$Once,
    [switch]$KeepAwake
)

$ErrorActionPreference = 'Stop'
# Windows PowerShell -NoExit may bind parameter defaults before PSScriptRoot exists.
# Resolve the default inside the script body, independently of the terminal's cwd.
if (-not $RepoRoot) { $RepoRoot = Split-Path -Parent $PSScriptRoot }
$resolvedRepo = [System.IO.Path]::GetFullPath($RepoRoot)
if (-not $StatePath) {
    $StatePath = "artifacts/publication_campaign/$CampaignId/campaign_state.json"
}
$resolvedState = if ([System.IO.Path]::IsPathRooted($StatePath)) {
    [System.IO.Path]::GetFullPath($StatePath)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $resolvedRepo $StatePath))
}
$shareMode = [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete
$logCursors = @{}
$observedJobStatus = @{}
$lastReadError = $null
$awakeEnabled = $false
$awakeApiReady = $false
if ($KeepAwake) {
    try {
        if (-not ('PublicationCampaign.NativePower' -as [type])) {
            Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
namespace PublicationCampaign {
    public static class NativePower {
        [DllImport("kernel32.dll")]
        public static extern uint SetThreadExecutionState(uint flags);
    }
}
'@
        }
        $awakeApiReady = $true
    } catch {
        Write-Warning "KeepAwake indisponivel: $($_.Exception.Message). Suspensao automatica NAO foi inibida."
    }
}

function Set-MonitorAwake([bool]$Required) {
    if (-not $KeepAwake -or -not $awakeApiReady -or $Required -eq $script:awakeEnabled) { return }
    # ES_CONTINUOUS (0x80000000) plus ES_SYSTEM_REQUIRED (1), never DISPLAY/AWAYMODE.
    [uint32]$flags = 2147483648
    if ($Required) { $flags = $flags -bor [uint32]1 }
    $previous = [PublicationCampaign.NativePower]::SetThreadExecutionState($flags)
    if ($previous -eq 0) {
        Write-Warning 'SetThreadExecutionState falhou; KeepAwake nao esta garantido.'
        return
    }
    $script:awakeEnabled = $Required
    if ($Required) {
        Write-Host 'KeepAwake ativo: somente suspensao automatica; tela e energia global inalteradas.'
    } else {
        Write-Host 'KeepAwake liberado: campanha gravada como terminal, sem jobs registrados RUNNING.'
    }
}

function Read-SharedState {
    for ($retry = 0; $retry -lt 3; $retry++) {
        $stream = $null
        $reader = $null
        $text = $null
        try {
            $stream = [System.IO.FileStream]::new($resolvedState,
                [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $shareMode)
            $reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
            $text = $reader.ReadToEnd()
        } catch [System.IO.IOException] {
            if ($retry -eq 2) { throw }
        } finally {
            if ($null -ne $reader) { $reader.Dispose() }
            if ($null -ne $stream) { $stream.Dispose() }
        }
        if ($null -ne $text) {
            # Parse only after releasing the handle. Atomic replacement may proceed.
            return ($text | ConvertFrom-Json)
        }
        # Brief ENOENT/sharing-race retry; no handle is retained during the wait.
        Start-Sleep -Milliseconds 120
    }
}

function Resolve-LogPath([string]$RelativePath) {
    $candidate = [System.IO.Path]::GetFullPath((Join-Path $resolvedRepo $RelativePath))
    $prefix = $resolvedRepo.TrimEnd([char[]]"\/") + [System.IO.Path]::DirectorySeparatorChar
    if (-not $candidate.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Log fora do repositorio configurado: $RelativePath"
    }
    return $candidate
}

function Show-NewLogLines([string]$RelativePath, [string]$Label) {
    if (-not $RelativePath) { return }
    $stream = $null
    $cursor = $null
    $truncated = $false
    try {
        $path = Resolve-LogPath $RelativePath
        $firstRead = -not $logCursors.ContainsKey($path)
        if ($firstRead) {
            $logCursors[$path] = @{
                Position = [long]0; Pending = ''; Decoder = [System.Text.Encoding]::UTF8.GetDecoder()
                Error = $null; Initialized = $false
            }
        }
        $cursor = $logCursors[$path]
        $firstRead = -not $cursor.Initialized
        $stream = [System.IO.FileStream]::new($path,
            [System.IO.FileMode]::Open, [System.IO.FileAccess]::Read, $shareMode)
        $length = $stream.Length
        if ($length -lt $cursor.Position) {
            $cursor.Position = [long]0
            $cursor.Pending = ''
            $cursor.Decoder.Reset()
            $truncated = $true
        }
        # On first observation, show recent context instead of replaying a huge log.
        $skipFirstLine = $firstRead -and $length -gt 32768
        if ($skipFirstLine) { $cursor.Position = $length - 32768 }
        [void]$stream.Seek($cursor.Position, [System.IO.SeekOrigin]::Begin)
        $remaining = [int][Math]::Min(1048576, [Math]::Max(0, $length - $cursor.Position))
        $bytes = New-Object byte[] $remaining
        $read = 0
        while ($read -lt $remaining) {
            $count = $stream.Read($bytes, $read, $remaining - $read)
            if ($count -eq 0) { break }
            $read += $count
        }
        $cursor.Position += $read
        $stream.Dispose()
        $stream = $null
        $cursor.Error = $null
        $cursor.Initialized = $true
        if ($truncated) { Write-Host "[$Label] Log truncado; retomando leitura." }
        if ($read -eq 0) { return }
        # Retain partial UTF-8 characters and incomplete lines only in memory.
        $chars = New-Object char[] ([System.Text.Encoding]::UTF8.GetMaxCharCount($read))
        $charCount = $cursor.Decoder.GetChars($bytes, 0, $read, $chars, 0, $false)
        $chunk = $cursor.Pending + [string]::new($chars, 0, $charCount)
        $lines = $chunk -split "`r`n|`n|`r"
        $cursor.Pending = $lines[-1]
        $complete = @($lines | Select-Object -SkipLast 1)
        if ($skipFirstLine) { $complete = @($complete | Select-Object -Skip 1) }
        if ($firstRead) { $complete = @($complete | Select-Object -Last 15) }
        foreach ($line in $complete) { Write-Host "[$Label] $line" }
    } catch {
        $message = $_.Exception.Message
        if ($null -ne $stream) { $stream.Dispose(); $stream = $null }
        if (($null -eq $cursor) -or $cursor.Error -ne $message) {
            Write-Host "[$Label] Log indisponivel neste ciclo: $message"
        }
        if ($null -ne $cursor) { $cursor.Error = $message }
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
    }
}

Write-Host 'Monitor somente leitura | atualizacao: 10 s | Ctrl+C encerra so o monitor.'
Write-Host "Estado: $resolvedState"
Write-Host 'COMPLETED_REJECTED e resultado cientifico rejeitado, nao falha tecnica.'
if ($KeepAwake) {
    Write-Host 'KeepAwake solicitado explicitamente; nao impede suspensao manual, desligamento ou falta de energia.'
}
try {
do {
    try {
        $snapshot = Read-SharedState
        if ($null -eq $snapshot -or $null -eq $snapshot.jobs) {
            throw 'Checkpoint sem o campo jobs; nenhum progresso sera inferido.'
        }
        $lastReadError = $null
        $rows = @($snapshot.jobs.PSObject.Properties | ForEach-Object { $_.Value })
        $counts = @{}
        foreach ($row in $rows) {
            $label = [string]$row.status
            if (-not $counts.ContainsKey($label)) { $counts[$label] = 0 }
            $counts[$label]++
        }
        $terminalSnapshot = $snapshot.status -in @('COMPLETED', 'COMPLETED_WITH_FAILURES', 'STOPPED')
        $terminalSnapshot = $terminalSnapshot -and [int]$counts['RUNNING'] -eq 0
        Set-MonitorAwake (-not $terminalSnapshot)
        $finished = [int]$counts['COMPLETED'] + [int]$counts['COMPLETED_REJECTED']
        $percent = if ($rows.Count) { 100.0 * $finished / $rows.Count } else { 0.0 }
        $stampText = [string]$snapshot.budget.last_checkpoint_utc
        if (-not $stampText) { $stampText = [string]$snapshot.updated_at_utc }
        $age = $null
        try {
            $stamp = [System.DateTimeOffset]::Parse($stampText, [System.Globalization.CultureInfo]::InvariantCulture)
            $age = ([System.DateTimeOffset]::UtcNow - $stamp.ToUniversalTime()).TotalSeconds
        } catch { }
        $fresh = ($null -ne $age) -and $age -ge -5 -and $age -le 30
        $ageText = if ($null -eq $age) { 'desconhecida' } else { '{0:N1} s' -f $age }
        $health = if ($fresh) { 'RECENTE (atividade nao confirmada)' } else { 'STALE / atualidade nao confirmada' }
        Write-Host ("`n[{0}] {1} | checkpoint: {2} | idade: {3}" -f
            [DateTimeOffset]::Now.ToString('HH:mm:ss'), $snapshot.campaign_id, $health, $ageText)
        Write-Host ("Ultimo estado GRAVADO: {0}; PID gravado: {1}" -f $snapshot.status, $snapshot.controller_pid)
        if ($snapshot.controller_process.platform) {
            Write-Host ("Plataforma do controller: {0}; PID nao comparado com processos Windows." -f $snapshot.controller_process.platform)
        }
        Write-Host ('Concluidos (COMPLETED + COMPLETED_REJECTED): {0}/{1} = {2:N1}%' -f $finished, $rows.Count, $percent)
        Write-Host (($counts.Keys | Sort-Object | ForEach-Object { '{0}={1}' -f $_, $counts[$_] }) -join ' | ')
        if (-not $fresh) {
            Write-Host 'ALERTA STALE: RUNNING no arquivo NAO confirma execucao atual. O monitor continuara observando; nao reinicia nada.'
            Write-Host 'Controller pode estar parado (STOPPED); para liveness consulte o comando da campanha --status no WSL/effective_status.'
            if ($awakeEnabled) { Write-Host 'KeepAwake nao garante progresso nem recupera controller/worker parado.' }
        }
        foreach ($row in $rows) {
            $previousStatus = $observedJobStatus[[string]$row.job_id]
            $observedJobStatus[[string]$row.job_id] = [string]$row.status
            $justFinished = $previousStatus -eq 'RUNNING' -and $row.status -ne 'RUNNING'
            # Never open/replay every historical log. Follow active jobs and their final transition.
            if ($row.status -ne 'RUNNING' -and -not $justFinished) { continue }
            $attempts = @($row.attempts | Where-Object { $null -ne $_ })
            if (-not $attempts.Count) { continue }
            $attempt = $attempts[-1]
            if ($row.status -eq 'RUNNING') {
                Write-Host ("Ultimo job registrado como RUNNING: {0} (tentativa {1})" -f $row.job_id, $attempt.attempt_index)
            } elseif ($justFinished) {
                Write-Host ("Transicao observada: {0}, RUNNING -> {1}" -f $row.job_id, $row.status)
            }
            Show-NewLogLines ([string]$attempt.stdout_log) "$($row.job_id) stdout"
            Show-NewLogLines ([string]$attempt.stderr_log) "$($row.job_id) stderr"
        }
    } catch {
        $message = $_.Exception.Message
        Write-Host "`nSTALE / checkpoint indisponivel: $message"
        if ($lastReadError -ne $message) {
            Write-Host 'Nenhum status atual sera presumido; nova tentativa em 10 s. O monitor nao modifica a campanha.'
        }
        $lastReadError = $message
        if ($awakeEnabled) { Write-Host 'KeepAwake permanece solicitado, mas nao garante que a campanha esteja viva.' }
    }
    if (-not $Once) { Start-Sleep -Seconds 10 }
} while (-not $Once)
} finally {
    if ($KeepAwake -and $awakeApiReady) {
        # Release this thread's request on normal exit, -Once or Ctrl+C. No power-plan change.
        $previous = [PublicationCampaign.NativePower]::SetThreadExecutionState([uint32]2147483648)
        $awakeEnabled = $false
        if ($previous -eq 0) { Write-Warning 'Nao foi possivel confirmar a liberacao de KeepAwake.' }
    }
}
