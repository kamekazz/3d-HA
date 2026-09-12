<#
Prune throwaway render output from scratchpad/ (+ two unreferenced root screenshots).

Everything removed here is build/critic-loop OUTPUT: nothing in the running app,
no build script, and no kept doc reads any of it. Kept inside scratchpad/:
  - lightgauntlet/ref/*   external Sims 4 reference shots (an INPUT, not regenerable)
  - FINAL_* / final_*     the named final shots
  - anything cited by filename in tools/roomkit/**, frontend/**, CLAUDE.md

Every file is tracked in git, so any of it comes back with:
  git checkout HEAD -- <path>

Usage:  powershell -ExecutionPolicy Bypass -File tools\prune_images.ps1
        powershell -ExecutionPolicy Bypass -File tools\prune_images.ps1 -Apply
#>
param([switch]$Apply)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$list = Join-Path $root 'tools\prune_images.list'
if (-not (Test-Path $list)) { throw "Missing $list" }

$targets = @(Get-Content $list | Where-Object { $_.Trim() -ne '' })
$targets += @('floor2_check.png', 'guest_focus.png')

$n = 0
$bytes = [long]0
foreach ($rel in $targets) {
    $p = Join-Path $root ($rel -replace '/', '\')
    if (-not (Test-Path -LiteralPath $p -PathType Leaf)) { continue }
    $n++
    $bytes += (Get-Item -LiteralPath $p).Length
    if ($Apply) { Remove-Item -LiteralPath $p -Force }
}

$mb = [math]::Round($bytes / 1MB, 1)

if ($Apply) {
    # drop directories left empty, deepest first
    Get-ChildItem (Join-Path $root 'scratchpad') -Recurse -Directory -ErrorAction SilentlyContinue |
        Sort-Object { $_.FullName.Length } -Descending |
        Where-Object { -not (Get-ChildItem $_.FullName -Force -ErrorAction SilentlyContinue) } |
        Remove-Item -Force -Recurse -ErrorAction SilentlyContinue
    Write-Host "Deleted $n files, $mb MB."
    Write-Host 'Recover anything with: git checkout HEAD -- <path>'
} else {
    Write-Host "DRY RUN: would delete $n files, $mb MB."
    Write-Host 'Re-run with -Apply to do it.'
}
