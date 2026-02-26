## Phase 1: MDD Foundation (Ready for Generation)

    [ ] Repo Scaffold: Create folder structure (`specs/`, `src/eco/`, `tests/`, `out/`).

    [ ] CLI Bootstrap: Initialize `typer` app with commands: `validate`, `run`, `list-scenarios`.

    [ ] Spec Templates: Create starter Markdown specs with fenced YAML blocks:
        - [ ] `world.md`
        - [ ] `citizens.md`
        - [ ] `rules.md`
        - [ ] `metrics.md`
        - [ ] `scenarios.md`
        - [ ] `prejudices.md`

    [ ] Validation Models: Implement pydantic models for every spec file.

    [ ] Loader: Read Markdown → extract YAML → validate → return structured config.

    [ ] Error UX: Friendly validation errors (show file, field path, and suggestion).

## Phase 2: Core Simulation (In Progress)

    [ ] Population Builder:
        - [ ] Convert distribution shares into counts (handle rounding cleanly).
        - [ ] Validate shares sum to 1.0 (± small epsilon).

    [ ] Activity Generation (Deterministic):
        - [ ] Weekday/weekend handling from `commuteDaysPerWeek`.
        - [ ] Build activity objects (transport, home energy, diet).

    [ ] Emissions Calculator:
        - [ ] Transport: miles × factor(mode)
        - [ ] Home Energy: kwh × kgco2_per_kwh
        - [ ] Diet: meals × factor(pattern)

    [ ] Aggregation:
        - [ ] Total kgCO2
        - [ ] By category
        - [ ] By citizen type
        - [ ] Time series per day

    [ ] Golden Tests:
        - [ ] Add `tests/fixtures/tiny_specs/`
        - [ ] Commit expected `expected.json`
        - [ ] Test exact match totals for seed + days

## Phase 3: Scenarios & Ethics Twist (Pending)

    [ ] Scenario Overrides:
        - [ ] Deep merge overrides into base specs
        - [ ] Validate scenario references (unknown citizen types, etc.)

    [ ] Scenario Runs:
        - [ ] Run baseline + 2 variants
        - [ ] Output `out/report.md` and `out/report.json` per run

    [ ] Data Prejudice Audit Integration:
        - [ ] Fill out `prejudices.md` with at least 5 assumptions + fixes
        - [ ] Implement at least 2 fixes in the spec (not code)
        - [ ] Compare before/after outputs and summarize change

## Phase 4: Reporting Polish (Future)

    [ ] Spec-driven Report Renderer:
        - [ ] Implement `metrics.md` sections in Markdown output
        - [ ] Add tables for breakdowns
        - [ ] Add run metadata: scenario, days, seed, spec hash

    [ ] JSON Export:
        - [ ] Stable schema for autograding
        - [ ] Include category + type breakdowns + time series

    [ ] Optional: Pretty Terminal Output (Rich):
        - [ ] Summary panel + tables

## Phase 5: Stretch Goals (Optional)

    [ ] Access Constraints:
        - [ ] Add fields like `transport.access: [bus, walk]`
        - [ ] Enforce constraints in activity generation

    [ ] Policy Levers:
        - [ ] Heat pump adoption, bike lanes, transit frequency as scenario knobs

    [ ] Monte Carlo Mode:
        - [ ] Multiple runs, average + variance, still seedable
