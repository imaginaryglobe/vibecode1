# author jaden fang jason lyu
from __future__ import annotations

from dataclasses import dataclass
from random import Random

from eco.config.models import CitizenType


@dataclass(frozen=True)
class TransportActivity:
    mode: str
    miles: float


@dataclass(frozen=True)
class HomeEnergyActivity:
    kwh: float


@dataclass(frozen=True)
class DietActivity:
    pattern: str
    meals: float


@dataclass(frozen=True)
class DailyActivities:
    transport: TransportActivity
    home_energy: HomeEnergyActivity
    diet: DietActivity


def _is_commute_day(day_index: int, commute_days_per_week: int) -> bool:
    day_of_week = day_index % 7
    commute_days = max(0, min(7, commute_days_per_week))
    return day_of_week < commute_days


def generate_daily_activities(
    citizen: CitizenType,
    day_index: int,
    citizen_index: int,
    seed: int,
) -> DailyActivities:
    random = Random(seed + (citizen_index * 10_000) + day_index)

    commute_today = _is_commute_day(day_index, citizen.transport.commuteDaysPerWeek)
    miles = citizen.transport.commuteMilesPerDay if commute_today else 0.0

    variation = 1.0 + random.uniform(-0.05, 0.05)
    kwh = max(0.0, citizen.home.kwhPerDay * variation)
    meals = max(0.0, citizen.diet.mealsPerDay)

    return DailyActivities(
        transport=TransportActivity(mode=citizen.transport.mode, miles=miles),
        home_energy=HomeEnergyActivity(kwh=kwh),
        diet=DietActivity(pattern=citizen.diet.pattern, meals=meals),
    )
