from __future__ import annotations

from eco.sim.aggregate import RunResult


def render_json_payload(result: RunResult, scenario: str, seed: int) -> dict:
    return {
        "scenario": scenario,
        "seed": seed,
        "days": result.days,
        "citizenCount": result.citizen_count,
        "totalKgCO2": result.total_kgco2,
        "avgKgCO2PerCitizenPerDay": result.avg_kgco2_per_citizen_per_day,
        "byCategory": result.by_category,
        "byCitizenType": result.by_citizen_type,
        "timeSeries": result.time_series,
    }
