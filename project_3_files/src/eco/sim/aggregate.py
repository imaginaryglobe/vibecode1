# author jaden fang jason lyu
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class RunResult:
    total_kgco2: float
    avg_kgco2_per_citizen_per_day: float
    by_category: dict[str, float]
    by_citizen_type: dict[str, float]
    time_series: list[dict[str, float]]
    citizen_count: int
    days: int


@dataclass
class Aggregator:
    days: int
    citizen_count: int
    by_category: dict[str, float] = field(default_factory=lambda: {"transport": 0.0, "homeEnergy": 0.0, "diet": 0.0})
    by_citizen_type: dict[str, float] = field(default_factory=dict)
    time_series: list[dict[str, float]] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.time_series = [
            {"day": float(day + 1), "transport": 0.0, "homeEnergy": 0.0, "diet": 0.0, "total": 0.0}
            for day in range(self.days)
        ]

    def add(self, day_index: int, citizen_type: str, emissions: dict[str, float]) -> None:
        self.by_category["transport"] += emissions["transport"]
        self.by_category["homeEnergy"] += emissions["homeEnergy"]
        self.by_category["diet"] += emissions["diet"]

        self.by_citizen_type[citizen_type] = self.by_citizen_type.get(citizen_type, 0.0) + emissions["total"]

        point = self.time_series[day_index]
        point["transport"] += emissions["transport"]
        point["homeEnergy"] += emissions["homeEnergy"]
        point["diet"] += emissions["diet"]
        point["total"] += emissions["total"]

    def finalize(self) -> RunResult:
        total = sum(self.by_category.values())
        denom = max(1, self.days * self.citizen_count)
        average = total / denom
        return RunResult(
            total_kgco2=total,
            avg_kgco2_per_citizen_per_day=average,
            by_category=self.by_category,
            by_citizen_type=self.by_citizen_type,
            time_series=self.time_series,
            citizen_count=self.citizen_count,
            days=self.days,
        )
