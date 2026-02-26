import json
from pathlib import Path

from eco.config.loader import load_with_scenario
from eco.report.render_json import render_json_payload
from eco.sim.engine import simulate


def _run_fixture(spec_dir: Path, scenario: str = "baseline") -> dict:
    config = load_with_scenario(spec_dir, scenario)
    result = simulate(config, days=config.world.simulation.defaultDays, seed=config.world.simulation.seed or 42)
    return render_json_payload(result, scenario=scenario, seed=config.world.simulation.seed or 42)


def test_engine_matches_golden() -> None:
    fixture = Path(__file__).parent / "fixtures" / "tiny_specs"
    expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
    actual = _run_fixture(fixture)
    assert actual == expected


def test_spec_change_alters_output_without_code_change() -> None:
    baseline_fixture = Path(__file__).parent / "fixtures" / "tiny_specs"
    alt_fixture = Path(__file__).parent / "fixtures" / "tiny_specs_alt_rules"

    base = _run_fixture(baseline_fixture)
    changed = _run_fixture(alt_fixture)

    assert changed["totalKgCO2"] != base["totalKgCO2"]
    assert changed["byCategory"]["transport"] > base["byCategory"]["transport"]
