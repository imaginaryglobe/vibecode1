## Phase 1: MDD Foundation (Completed)

    [x] Repo Scaffold: Create folder structure (`specs/`, `src/eco/`, `tests/`, `out/`).

    [x] CLI Bootstrap: Initialize `typer` app with commands: `validate`, `run`, `list-scenarios`.

    [x] Spec Templates: Create starter Markdown specs with fenced YAML blocks:
        - [x] `world.md`
        - [x] `citizens.md`
        - [x] `rules.md`
        - [x] `metrics.md`
        - [x] `scenarios.md`
        - [x] `prejudices.md`

    [x] Validation Models: Implement pydantic models for every spec file.

    [x] Loader: Read Markdown → extract YAML → validate → return structured config.

    [x] Error UX: Friendly validation errors (show file, field path, and suggestion).

## Phase 2: Core Simulation (Completed)

    [x] Population Builder:
        - [x] Convert distribution shares into counts (handle rounding cleanly).
        - [x] Validate shares sum to 1.0 (± small epsilon).

    [x] Activity Generation (Deterministic):
        - [x] Weekday/weekend handling from `commuteDaysPerWeek`.
        - [x] Build activity objects (transport, home energy, diet).

    [x] Emissions Calculator:
        - [x] Transport: miles × factor(mode)
        - [x] Home Energy: kwh × kgco2_per_kwh
        - [x] Diet: meals × factor(pattern)

    [x] Aggregation:
        - [x] Total kgCO2
        - [x] By category
        - [x] By citizen type
        - [x] Time series per day

    [x] Golden Tests:
        - [x] Add `tests/fixtures/tiny_specs/`
        - [x] Commit expected `expected.json`
        - [x] Test exact match totals for seed + days

## Phase 3: Scenarios & Ethics Twist (Completed)

    [x] Scenario Overrides:
        - [x] Deep merge overrides into base specs
        - [x] Validate scenario references (unknown citizen types, etc.)

    [x] Scenario Runs:
        - [x] Run baseline + 2 variants
        - [x] Output `out/report.md` and `out/report.json` per run

    [x] Data Prejudice Audit Integration:
        - [x] Fill out `prejudices.md` with at least 5 assumptions + fixes
        - [x] Implement at least 2 fixes in the spec (not code)
        - [x] Compare before/after outputs and summarize change

## Phase 4: Reporting Polish (Completed)

    [x] Spec-driven Report Renderer:
        - [x] Implement `metrics.md` sections in Markdown output
        - [x] Add tables for breakdowns
        - [x] Add run metadata: scenario, days, seed, spec hash

    [x] JSON Export:
        - [x] Stable schema for autograding
        - [x] Include category + type breakdowns + time series

    [ ] Optional: Pretty Terminal Output (Rich):
        - [ ] Summary panel + tables

## Phase 5: Stretch Goals (Optional)

    [ ] Access Constraints:
        - [x] Add fields like `transport.access: [bus, walk]`
        - [ ] Enforce constraints in activity generation

    [ ] Policy Levers:
        - [ ] Heat pump adoption, bike lanes, transit frequency as scenario knobs

    [ ] Monte Carlo Mode:
        - [ ] Multiple runs, average + variance, still seedable
