# Project: Eco-Tracker Social Simulator
**Vibe:** Transparent, spec-first, ethical-by-design.  
**Goal:** A small-town carbon-footprint simulator where **Markdown is the single source of truth** (MDD).  
**Tech Stack (recommended):** Python 3.12+, `typer` (CLI), `rich` (pretty output), `pydantic` (validation), `markdown-it-py` (parse Markdown), `pytest`.

---

## Core Idea (MDD Rule)
1. **All “world logic” lives in `/specs/*.md`.**
2. Code must be mostly a **runner + validator + simulator** for the spec.
3. Any new behavior requires a spec change first (tests enforce this).

---

## Core Functional Requirements

### 1) Spec Files (Source of Truth)
The simulator must load and validate these Markdown files:

- `specs/world.md` — global world + population distribution
- `specs/citizens.md` — citizen archetypes and daily habits
- `specs/rules.md` — emission factors + calculation rules
- `specs/metrics.md` — what the simulator must report
- `specs/scenarios.md` — scenario overrides (no code changes)
- `specs/prejudices.md` — explicit bias/assumption audit + improvements

### 2) Simulation Engine
- Simulates a town population across **N days** (default: 30).
- Each simulated day:
  - For each citizen: generate activities from their archetype habits.
  - Compute emissions from activities using `rules.md`.
  - Aggregate into metrics required by `metrics.md`.

### 3) CLI (Minimum UI)
- `eco run --scenario baseline --days 30 --seed 42`
- `eco validate` (validate Markdown specs; fail fast)
- `eco report --format markdown|json`

### 4) Outputs
The simulator must produce:
- `out/report.md` (human-friendly, aligns with `metrics.md`)
- `out/report.json` (machine-readable)
- `out/run_meta.json` (spec hash, scenario name, days, seed, timestamp)

---

## Markdown Spec Schema (Minimal DSL)

> Keep it simple: use fenced YAML blocks inside Markdown to avoid building a full parser.

### `world.md`
Must contain:
- `world`: name, description
- `simulation`: defaultDays, optionalSeed
- `population`: totalCount OR explicit counts per archetype

Example:
```yaml
world:
  name: "West Lafayette (Toy Model)"
  description: "Small town carbon sim for class."
simulation:
  defaultDays: 30
  seed: 42
population:
  totalCount: 2000
  distribution:
    - type: Student
      share: 0.35
    - type: Commuter
      share: 0.45
    - type: RemoteWorker
      share: 0.20
```

### `citizens.md`
Defines archetypes and habits as *activity templates*:

Example:
```yaml
citizenTypes:
  - name: Student
    home:
      kind: dorm
      kwhPerDay: 6
    transport:
      mode: walk
      commuteMilesPerDay: 0.5
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: mixed
  - name: Commuter
    home:
      kind: house
      kwhPerDay: 18
    transport:
      mode: car
      commuteMilesPerDay: 18
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: meat_heavy
```

### `rules.md`
Defines emission factors and formula rules.

Example:
```yaml
emissionFactors:
  transport:
    car_kgco2_per_mile: 0.404
    bus_kgco2_per_mile: 0.089
    walk_kgco2_per_mile: 0.0
    bike_kgco2_per_mile: 0.0
  homeEnergy:
    kgco2_per_kwh: 0.39
  diet:
    meal_mixed_kgco2: 1.7
    meal_meat_heavy_kgco2: 3.3
    meal_plant_forward_kgco2: 1.1

rules:
  - id: transport_emissions
    formula: "miles * factor_for_mode"
  - id: home_energy_emissions
    formula: "kwh * kgco2_per_kwh"
  - id: diet_emissions
    formula: "meals * factor_for_pattern"
```

**Requirement:** the engine must support:
- transport emissions
- home energy emissions
- diet emissions

(Stretch rules can be added later.)

### `metrics.md`
Defines required report tables/sections (spec-driven reporting).

Example:
```yaml
report:
  sections:
    - id: headline
      fields: [totalKgCO2, avgKgCO2PerCitizenPerDay]
    - id: byCategory
      breakdown: [transport, homeEnergy, diet]
    - id: byCitizenType
      breakdown: [Student, Commuter, RemoteWorker]
    - id: timeSeries
      granularity: day
```

### `scenarios.md`
Defines overrides to apply *on top of* the base specs.

Example:
```yaml
scenarios:
  - name: baseline
    overrides: {}
  - name: transit_push
    overrides:
      citizens:
        Commuter:
          transport:
            mode: bus
  - name: remote_work_wave
    overrides:
      world:
        population:
          distribution:
            - type: RemoteWorker
              share: 0.40
```

### `prejudices.md`
A checklist + explicit corrections.

Example:
```yaml
audit:
  - assumption: "Everyone can choose any transport mode"
    risk: "Ignores disability, rural access, safety"
    fix:
      addConstraint: "transport.mode options depend on access"
  - assumption: "Homes are all same size/efficiency"
    risk: "Erases income/age of housing differences"
    fix:
      addCitizenTypeField: "home.efficiencyBand"
```

---

## Determinism & Randomness
- Runs must be reproducible with `--seed`.
- Any probabilistic habit variation must be spec-defined (e.g., weekend multiplier).

---

## Success Metrics
- **Correctness:** totals and breakdowns match golden tests.
- **MDD compliance:** changing spec changes outcomes **without code changes**.
- **Usability:** `eco validate` clearly explains spec errors.
- **Ethics:** `prejudices.md` is integrated into the workflow and reflected in scenario comparisons.

---

## Non-goals (v1)
- No real-world accuracy guarantee (toy model unless you provide verified factors).
- No external API calls.
- No fancy web UI (CLI-first).
- No optimization for massive populations (keep ≤ 50k unless extended).

---

## Stretch Goals (v2+)
- Add “access constraints” (transit availability, disability, income band).
- Add policy levers (subsidies, bike lanes, heat pumps) as spec modules.
- Add simple charts (ASCII or matplotlib export).
- Add Monte Carlo runs with confidence intervals (still seedable).
