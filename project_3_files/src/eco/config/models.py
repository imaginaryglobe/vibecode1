from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class WorldInfo(BaseModel):
    name: str
    description: str


class SimulationConfig(BaseModel):
    defaultDays: int = 30
    seed: int | None = None


class PopulationDistributionEntry(BaseModel):
    type: str
    share: float | None = None
    count: int | None = None


class PopulationConfig(BaseModel):
    totalCount: int | None = None
    distribution: list[PopulationDistributionEntry] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_distribution(self) -> "PopulationConfig":
        if not self.distribution:
            raise ValueError("population.distribution must include at least one entry")
        if self.totalCount is None and any(item.count is None for item in self.distribution):
            raise ValueError("population.totalCount is required when distribution uses shares")
        return self


class WorldSpec(BaseModel):
    world: WorldInfo
    simulation: SimulationConfig
    population: PopulationConfig


class HomeHabit(BaseModel):
    kind: str
    kwhPerDay: float


class TransportHabit(BaseModel):
    mode: str
    commuteMilesPerDay: float
    commuteDaysPerWeek: int = 5


class DietHabit(BaseModel):
    mealsPerDay: float
    pattern: str


class CitizenType(BaseModel):
    name: str
    home: HomeHabit
    transport: TransportHabit
    diet: DietHabit
    transportAccess: list[str] | None = None


class CitizensSpec(BaseModel):
    citizenTypes: list[CitizenType]


class TransportFactors(BaseModel):
    car_kgco2_per_mile: float = 0.404
    bus_kgco2_per_mile: float = 0.089
    walk_kgco2_per_mile: float = 0.0
    bike_kgco2_per_mile: float = 0.0


class HomeEnergyFactors(BaseModel):
    kgco2_per_kwh: float


class DietFactors(BaseModel):
    meal_mixed_kgco2: float
    meal_meat_heavy_kgco2: float
    meal_plant_forward_kgco2: float


class EmissionFactors(BaseModel):
    transport: TransportFactors
    homeEnergy: HomeEnergyFactors
    diet: DietFactors


class RuleDefinition(BaseModel):
    id: str
    formula: str


class RulesSpec(BaseModel):
    emissionFactors: EmissionFactors
    rules: list[RuleDefinition] = Field(default_factory=list)


class ReportSection(BaseModel):
    id: Literal["headline", "byCategory", "byCitizenType", "timeSeries"]
    fields: list[str] | None = None
    breakdown: list[str] | None = None
    granularity: str | None = None


class MetricsReport(BaseModel):
    sections: list[ReportSection]


class MetricsSpec(BaseModel):
    report: MetricsReport


class Scenario(BaseModel):
    name: str
    overrides: dict[str, Any] = Field(default_factory=dict)


class ScenariosSpec(BaseModel):
    scenarios: list[Scenario]


class AuditFix(BaseModel):
    addConstraint: str | None = None
    addCitizenTypeField: str | None = None


class AuditItem(BaseModel):
    assumption: str
    risk: str
    fix: AuditFix


class PrejudicesSpec(BaseModel):
    audit: list[AuditItem]


class FullConfig(BaseModel):
    world: WorldSpec
    citizens: CitizensSpec
    rules: RulesSpec
    metrics: MetricsSpec
    scenarios: ScenariosSpec
    prejudices: PrejudicesSpec
