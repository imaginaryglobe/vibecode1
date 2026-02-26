from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from eco.config.models import (
    CitizensSpec,
    FullConfig,
    MetricsSpec,
    PrejudicesSpec,
    RulesSpec,
    ScenariosSpec,
    WorldSpec,
)
from eco.config.scenario import apply_scenario
from eco.util.errors import EcoConfigError

_YAML_BLOCK_RE = re.compile(r"```yaml\s*(.*?)```", re.IGNORECASE | re.DOTALL)


def _extract_yaml_dict(markdown_text: str, file_name: str) -> dict[str, Any]:
    matches = _YAML_BLOCK_RE.findall(markdown_text)
    if not matches:
        raise EcoConfigError(file_name, "root", "No fenced yaml block found", "Add one ```yaml ... ``` block")

    combined: dict[str, Any] = {}
    for block in matches:
        parsed = yaml.safe_load(block) or {}
        if not isinstance(parsed, dict):
            raise EcoConfigError(file_name, "root", "YAML block must parse to an object", "Start with key: value pairs")
        combined = {**combined, **parsed}
    return combined


def _raise_validation_error(file_name: str, exc: ValidationError) -> None:
    first = exc.errors()[0]
    field_path = ".".join(str(p) for p in first.get("loc", ["root"]))
    message = first.get("msg", "invalid value")
    raise EcoConfigError(file_name, field_path, message, "Check field type/required keys")


def _validate_cross_references(world: WorldSpec, citizens: CitizensSpec, scenario_spec: ScenariosSpec) -> None:
    citizen_names = {citizen.name for citizen in citizens.citizenTypes}

    for entry in world.population.distribution:
        if entry.type not in citizen_names:
            raise EcoConfigError(
                "world.md",
                f"population.distribution[{entry.type}]",
                "Unknown citizen type reference",
                "Ensure type exists in citizens.md",
            )

    shares = [entry.share for entry in world.population.distribution if entry.share is not None]
    if shares:
        total = sum(shares)
        if abs(total - 1.0) > 1e-6:
            raise EcoConfigError(
                "world.md",
                "population.distribution.share",
                f"Shares must sum to 1.0 (got {total:.6f})",
                "Adjust shares to sum to 1.0",
            )

    for citizen in citizens.citizenTypes:
        if citizen.home.kwhPerDay < 0 or citizen.transport.commuteMilesPerDay < 0 or citizen.diet.mealsPerDay < 0:
            raise EcoConfigError(
                "citizens.md",
                f"citizenTypes[{citizen.name}]",
                "Negative miles/kwh/meals are not allowed",
                "Use zero or positive values",
            )

    scenario_names = {scenario.name for scenario in scenario_spec.scenarios}
    if "baseline" not in scenario_names:
        raise EcoConfigError("scenarios.md", "scenarios", "Missing baseline scenario", "Add scenario named baseline")


def load_all_specs(spec_dir: Path) -> FullConfig:
    paths = {
        "world": spec_dir / "world.md",
        "citizens": spec_dir / "citizens.md",
        "rules": spec_dir / "rules.md",
        "metrics": spec_dir / "metrics.md",
        "scenarios": spec_dir / "scenarios.md",
        "prejudices": spec_dir / "prejudices.md",
    }

    try:
        raw_world = _extract_yaml_dict(paths["world"].read_text(encoding="utf-8"), "world.md")
        raw_citizens = _extract_yaml_dict(paths["citizens"].read_text(encoding="utf-8"), "citizens.md")
        raw_rules = _extract_yaml_dict(paths["rules"].read_text(encoding="utf-8"), "rules.md")
        raw_metrics = _extract_yaml_dict(paths["metrics"].read_text(encoding="utf-8"), "metrics.md")
        raw_scenarios = _extract_yaml_dict(paths["scenarios"].read_text(encoding="utf-8"), "scenarios.md")
        raw_prejudices = _extract_yaml_dict(paths["prejudices"].read_text(encoding="utf-8"), "prejudices.md")
    except FileNotFoundError as exc:
        raise EcoConfigError("specs", "root", "Missing required spec file", str(exc)) from exc

    try:
        world = WorldSpec.model_validate(raw_world)
    except ValidationError as exc:
        _raise_validation_error("world.md", exc)
    try:
        citizens = CitizensSpec.model_validate(raw_citizens)
    except ValidationError as exc:
        _raise_validation_error("citizens.md", exc)
    try:
        rules = RulesSpec.model_validate(raw_rules)
    except ValidationError as exc:
        _raise_validation_error("rules.md", exc)
    try:
        metrics = MetricsSpec.model_validate(raw_metrics)
    except ValidationError as exc:
        _raise_validation_error("metrics.md", exc)
    try:
        scenarios = ScenariosSpec.model_validate(raw_scenarios)
    except ValidationError as exc:
        _raise_validation_error("scenarios.md", exc)
    try:
        prejudices = PrejudicesSpec.model_validate(raw_prejudices)
    except ValidationError as exc:
        _raise_validation_error("prejudices.md", exc)

    _validate_cross_references(world, citizens, scenarios)

    return FullConfig(
        world=world,
        citizens=citizens,
        rules=rules,
        metrics=metrics,
        scenarios=scenarios,
        prejudices=prejudices,
    )


def load_with_scenario(spec_dir: Path, scenario_name: str) -> FullConfig:
    config = load_all_specs(spec_dir)
    scenario = next((item for item in config.scenarios.scenarios if item.name == scenario_name), None)
    if scenario is None:
        raise EcoConfigError(
            "scenarios.md",
            "scenarios",
            f"Unknown scenario name '{scenario_name}'",
            "Use `eco list-scenarios` to view valid names",
        )

    world_data, citizens_data, rules_data = apply_scenario(
        config.world.model_dump(mode="python"),
        config.citizens.model_dump(mode="python"),
        config.rules.model_dump(mode="python"),
        scenario.overrides,
    )

    world = WorldSpec.model_validate(world_data)
    citizens = CitizensSpec.model_validate(citizens_data)
    rules = RulesSpec.model_validate(rules_data)
    _validate_cross_references(world, citizens, config.scenarios)

    return FullConfig(
        world=world,
        citizens=citizens,
        rules=rules,
        metrics=config.metrics,
        scenarios=config.scenarios,
        prejudices=config.prejudices,
    )
