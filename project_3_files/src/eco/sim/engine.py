# author jaden fang jason lyu
from __future__ import annotations

from typing import Iterable

from eco.config.models import CitizenType, FullConfig
from eco.sim.activities import generate_daily_activities
from eco.sim.aggregate import Aggregator, RunResult
from eco.sim.emissions import calculate_daily_emissions


def _build_population(config: FullConfig) -> list[CitizenType]:
    citizens_by_name = {citizen.name: citizen for citizen in config.citizens.citizenTypes}
    distribution = config.world.population.distribution

    explicit_counts = [entry for entry in distribution if entry.count is not None]
    if explicit_counts and all(entry.count is not None for entry in distribution):
        population: list[CitizenType] = []
        for entry in distribution:
            citizen = citizens_by_name[entry.type]
            population.extend([citizen] * int(entry.count or 0))
        return population

    total_count = int(config.world.population.totalCount or 0)
    raw_counts = [(entry, float(entry.share or 0.0) * total_count) for entry in distribution]
    base_counts = {entry.type: int(raw) for entry, raw in raw_counts}
    remainder = total_count - sum(base_counts.values())

    by_fraction = sorted(raw_counts, key=lambda item: (item[1] - int(item[1])), reverse=True)
    for i in range(remainder):
        base_counts[by_fraction[i % len(by_fraction)][0].type] += 1

    population = []
    for citizen_type, count in base_counts.items():
        population.extend([citizens_by_name[citizen_type]] * count)
    return population


def simulate(config: FullConfig, days: int, seed: int) -> RunResult:
    population = _build_population(config)
    aggregator = Aggregator(days=days, citizen_count=len(population))

    for day_index in range(days):
        for citizen_index, citizen in enumerate(population):
            activities = generate_daily_activities(
                citizen=citizen,
                day_index=day_index,
                citizen_index=citizen_index,
                seed=seed,
            )
            emissions = calculate_daily_emissions(activities, config.rules)
            aggregator.add(day_index=day_index, citizen_type=citizen.name, emissions=emissions)

    return aggregator.finalize()
