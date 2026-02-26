param(
    [ValidateSet("validate", "list", "run", "report", "test", "all")]
    [string]$Action = "run",
    [string]$Scenario = "baseline",
    [int]$Days = 30,
    [int]$Seed = 42
)

$ErrorActionPreference = "Stop"

$python = "C:/Users/Jaden/coding/Purdue/vibecode1/.venv/Scripts/python.exe"

if (-not (Test-Path $python)) {
    Write-Error "Python executable not found at $python"
}

switch ($Action) {
    "validate" {
        & $python -m eco.cli validate
    }
    "list" {
        & $python -m eco.cli list-scenarios
    }
    "run" {
        & $python -m eco.cli run --scenario $Scenario --days $Days --seed $Seed
        Write-Host "Report: out/report.md"
        Write-Host "JSON:   out/report.json"
    }
    "report" {
        & $python -m eco.cli report --format markdown --scenario $Scenario --days $Days --seed $Seed
    }
    "test" {
        & $python -m pytest -q
    }
    "all" {
        & $python -m eco.cli validate
        & $python -m eco.cli run --scenario $Scenario --days $Days --seed $Seed
        & $python -m pytest -q
        Write-Host "Done. See out/report.md"
    }
}
