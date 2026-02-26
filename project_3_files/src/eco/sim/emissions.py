# author jaden fang jason lyu
from __future__ import annotations

from eco.config.models import RulesSpec
from eco.sim.activities import DailyActivities
from eco.util.errors import EcoConfigError


def _transport_factor(rules: RulesSpec, mode: str) -> float:
    key = f"{mode}_kgco2_per_mile"
    factors = rules.emissionFactors.transport.model_dump(mode="python")
    if key not in factors:
        raise EcoConfigError("rules.md", f"emissionFactors.transport.{key}", "Unknown transport mode factor", "Add factor key in rules.md")
    return float(factors[key])


def _diet_factor(rules: RulesSpec, pattern: str) -> float:
    key = f"meal_{pattern}_kgco2"
    factors = rules.emissionFactors.diet.model_dump(mode="python")
    if key not in factors:
        raise EcoConfigError("rules.md", f"emissionFactors.diet.{key}", "Unknown diet pattern factor", "Add factor key in rules.md")
    return float(factors[key])


def calculate_daily_emissions(activities: DailyActivities, rules: RulesSpec) -> dict[str, float]:
    transport = activities.transport.miles * _transport_factor(rules, activities.transport.mode)
    home_energy = activities.home_energy.kwh * rules.emissionFactors.homeEnergy.kgco2_per_kwh
    diet = activities.diet.meals * _diet_factor(rules, activities.diet.pattern)

    return {
        "transport": transport,
        "homeEnergy": home_energy,
        "diet": diet,
        "total": transport + home_energy + diet,
    }
