#Requires -Version 5.1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
python -m pip install -e ".[dev]" -q
python -m evidence_graph demo
exit $LASTEXITCODE
