# author jaden fang jason lyu
from __future__ import annotations

from copy import deepcopy
from typing import Any


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
            continue

        if isinstance(value, list):
            if all(isinstance(item, dict) and ("name" in item or "type" in item) for item in value):
                existing = merged.get(key, [])
                if not isinstance(existing, list):
                    merged[key] = deepcopy(value)
                    continue
                index: dict[tuple[str, str], dict[str, Any]] = {}
                for item in existing:
                    if isinstance(item, dict):
                        if "name" in item:
                            index[("name", str(item["name"]))] = deepcopy(item)
                        if "type" in item:
                            index[("type", str(item["type"]))] = deepcopy(item)
                for item in value:
                    if "name" in item:
                        key_field = ("name", str(item["name"]))
                    else:
                        key_field = ("type", str(item["type"]))
                    if key_field in index:
                        index[key_field] = deep_merge(index[key_field], item)
                    else:
                        index[key_field] = deepcopy(item)
                merged[key] = list(index.values())
            else:
                merged[key] = deepcopy(value)
            continue

        merged[key] = deepcopy(value)
    return merged


def apply_scenario(
    world_data: dict[str, Any],
    citizens_data: dict[str, Any],
    rules_data: dict[str, Any],
    scenario_overrides: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    world_overrides = scenario_overrides.get("world", {})
    rules_overrides = scenario_overrides.get("rules", {})
    citizens_overrides = scenario_overrides.get("citizens", {})

    world_merged = deep_merge(world_data, world_overrides)
    rules_merged = deep_merge(rules_data, rules_overrides)

    citizens_merged = deepcopy(citizens_data)
    if citizens_overrides:
        by_name = {
            citizen["name"]: citizen
            for citizen in citizens_merged.get("citizenTypes", [])
            if isinstance(citizen, dict) and "name" in citizen
        }
        for citizen_name, citizen_override in citizens_overrides.items():
            if citizen_name in by_name:
                by_name[citizen_name] = deep_merge(by_name[citizen_name], citizen_override)
            else:
                by_name[citizen_name] = {"name": citizen_name, **citizen_override}
        citizens_merged["citizenTypes"] = list(by_name.values())

    return world_merged, citizens_merged, rules_merged
