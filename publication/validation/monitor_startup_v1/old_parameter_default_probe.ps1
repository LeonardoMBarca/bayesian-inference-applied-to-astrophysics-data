[CmdletBinding()]
param([string]$RepoRoot = (Split-Path -Parent $PSScriptRoot))
Write-Host "resolved=$RepoRoot"