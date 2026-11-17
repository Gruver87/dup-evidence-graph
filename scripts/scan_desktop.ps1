#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

python -m pip install -e . -q
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$Desktop = Join-Path $env:USERPROFILE "Desktop"
python -m evidence_graph --desktop $Desktop scan
python -m evidence_graph --desktop $Desktop query radar soak_48h
# expected fail-closed exit 1 unless real 48h pack exists
$soakExit = $LASTEXITCODE
python -m evidence_graph --desktop $Desktop query radar ops_ready
$opsExit = $LASTEXITCODE
python -m evidence_graph --desktop $Desktop export --dir (Join-Path $Root "out")
python -m evidence_graph --desktop $Desktop board | Select-Object -First 40

Write-Host "soak_48h_exit=$soakExit ops_ready_exit=$opsExit"
if ($opsExit -ne 0) {
  Write-Host "WARN: ops_ready not allowed — check READY_OPS.json"
}
exit 0
