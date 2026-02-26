# Eco-Tracker Social Simulator

Spec-driven simulator where Markdown/YAML files in `specs/` are the source of truth.

## Abstract

Eco-Tracker is a command-line social simulation that estimates community carbon emissions from three categories: transport, home energy, and diet. Instead of hardcoding the world in Python, the simulator reads Markdown files with YAML blocks in `specs/` (world setup, citizen archetypes, emissions rules, metrics, scenarios, and bias audit notes). You can switch scenarios and rerun the model without changing code, then generate machine-readable and human-readable reports in `out/`.

## Quickstart

```bash
pip install -e .[dev]
eco validate
eco run --scenario baseline --days 30 --seed 42
```

## PowerShell shortcut

```powershell
./run.ps1 -Action validate
./run.ps1 -Action run -Scenario baseline -Days 30 -Seed 42
./run.ps1 -Action all
```

## Commands

### Main CLI (`eco`)

- `eco validate`
	- Validates all spec files and reports schema/reference issues.
- `eco list-scenarios`
	- Prints available scenario names from `specs/scenarios.md`.
- `eco run --scenario baseline --days 30 --seed 42`
	- Runs the simulation and writes:
		- `out/report.md`
		- `out/report.json`
		- `out/run_meta.json`
- `eco report --format markdown|json --scenario baseline --days 30 --seed 42`
	- Runs simulation and prints selected report format to terminal.

### Shortcut script (`run.ps1`)

- `./run.ps1 -Action validate`
- `./run.ps1 -Action list`
- `./run.ps1 -Action run -Scenario baseline -Days 30 -Seed 42`
- `./run.ps1 -Action report -Scenario baseline`
- `./run.ps1 -Action test`
- `./run.ps1 -Action all`
