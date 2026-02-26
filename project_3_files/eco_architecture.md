# Architecture: Eco-Tracker Social Simulator
The system is **spec-driven**: Markdown/YAML specs define the world, citizens, and rules; code validates + executes.

## Repository Layout
```
eco-tracker/
  specs/                # SOURCE OF TRUTH
    world.md
    citizens.md
    rules.md
    metrics.md
    scenarios.md
    prejudices.md
  src/
    eco/
      __init__.py
      cli.py            # typer commands
      config/
        models.py       # pydantic models for all specs
        loader.py       # load Markdown -> extract YAML -> validate models
        scenario.py     # apply scenario overrides
      sim/
        engine.py       # simulation loop
        activities.py   # activity generation from archetypes (deterministic + seed)
        emissions.py    # applies rules + factors to activities
        aggregate.py    # metrics aggregation
      report/
        render_md.py    # spec-driven markdown report
        render_json.py  # json output
      util/
        hashing.py      # spec hash, run meta
        errors.py       # friendly error types
  tests/
    test_loader.py
    test_engine_golden.py
    fixtures/
      tiny_specs/       # 2 archetypes, tiny population, fixed expected outputs
```

---

## Core Data Flow
1. **Load** specs from `/specs/*.md`
2. **Extract YAML blocks** (fenced ```yaml) from each file
3. **Validate** with pydantic models (fail fast)
4. **Select scenario** and apply overrides (deep merge with rules)
5. **Simulate** N days with deterministic RNG
6. **Aggregate** using `metrics.md`
7. **Render outputs** (`out/report.md`, `out/report.json`, `out/run_meta.json`)

---

## Key Modules

### 1) `eco.config.loader`
Responsibilities:
- Read Markdown files
- Extract fenced YAML (support multiple blocks, but require exactly one “main” block per file)
- Validate schema and emit actionable errors:
  - missing keys
  - invalid shares (must sum to ~1.0)
  - unknown citizen type references
  - negative miles/kwh/meals
  - unknown scenario name

### 2) `eco.config.scenario`
Responsibilities:
- Apply scenario overrides without mutating base spec objects
- Override rules:
  - citizen-type fields (e.g., Commuter transport mode)
  - population distribution
  - emission factors (optional)
- Implement deep-merge rules:
  - dict merges recursively
  - lists are replaced unless explicitly keyed by `name`/`type`

### 3) `eco.sim.engine`
Responsibilities:
- Build the population (count by distribution)
- Loop days:
  - generate daily activities for each citizen from archetype + day index
  - compute emissions per activity
  - aggregate by category and type
- Provide hooks for:
  - weekday/weekend logic
  - habit variability (if spec includes it)

### 4) `eco.sim.activities`
Responsibilities:
- Convert “habit templates” into concrete per-day activities:
  - `TransportActivity(mode, miles)`
  - `HomeEnergyActivity(kwh)`
  - `DietActivity(pattern, meals)`
- Must be deterministic given (seed, citizen_index, day_index)

### 5) `eco.sim.emissions`
Responsibilities:
- Apply emission factors and rules:
  - transport: miles × factor(mode)
  - home energy: kwh × kgco2_per_kwh
  - diet: meals × factor(pattern)
- Output structured records for aggregation.

### 6) `eco.sim.aggregate`
Responsibilities:
- Accumulate totals:
  - total kgCO2
  - by day (time series)
  - by category
  - by citizen type
- Produce a single `RunResult` object used by report renderers.

### 7) `eco.report.render_md` / `eco.report.render_json`
Responsibilities:
- Use `metrics.md` to decide what to print (sections + fields)
- Markdown report should include:
  - configuration summary (scenario/days/seed/spec hash)
  - emissions summary
  - breakdown tables
  - scenario comparison section (optional if multiple runs)

---

## CLI Commands (typer)
- `eco validate` — validates specs and prints a readable summary
- `eco run --scenario NAME --days N --seed S` — generates outputs in `/out`
- `eco list-scenarios` — prints scenario names from `scenarios.md`

---

## Testing Strategy
### Golden Test (most important)
- A tiny fixture world (e.g., 10 citizens, 2 types, 2 days, fixed seed)
- Expected totals committed as JSON
- Ensures:
  - spec parsing works
  - emissions math is stable
  - aggregation is correct
  - scenario overrides change results

### Spec-change test
- Modify `rules.md` factor in fixture (or load alternate fixture)
- Assert totals change **without code changes**

---

## Performance & Constraints
- Target: 10k citizens × 30 days runs in seconds locally.
- If needed later: vectorize aggregation, but **don’t optimize until correct**.

---

## Extension Points (v2+)
- Additional categories (waste, water, goods)
- Access constraints (transit availability, disability, income)
- Policy levers as spec overlays
- Multi-run scenario comparisons + charts
