# author jaden fang jason lyu
from __future__ import annotations

from eco.config.models import MetricsSpec
from eco.sim.aggregate import RunResult


def _table_from_dict(title: str, values: dict[str, float]) -> list[str]:
    lines = [f"### {title}", "", "| Key | kgCO2 |", "|---|---:|"]
    for key, value in values.items():
        lines.append(f"| {key} | {value:.3f} |")
    lines.append("")
    return lines


def render_markdown(
    result: RunResult,
    metrics: MetricsSpec,
    scenario: str,
    days: int,
    seed: int,
    spec_hash: str,
) -> str:
    lines: list[str] = [
        "# Eco-Tracker Report",
        "",
        "## Configuration",
        f"- Scenario: {scenario}",
        f"- Days: {days}",
        f"- Seed: {seed}",
        f"- Spec Hash: {spec_hash}",
        "",
    ]

    for section in metrics.report.sections:
        if section.id == "headline":
            lines.extend(
                [
                    "## Headline",
                    f"- totalKgCO2: {result.total_kgco2:.3f}",
                    f"- avgKgCO2PerCitizenPerDay: {result.avg_kgco2_per_citizen_per_day:.3f}",
                    "",
                ]
            )
        elif section.id == "byCategory":
            lines.extend(_table_from_dict("By Category", result.by_category))
        elif section.id == "byCitizenType":
            lines.extend(_table_from_dict("By Citizen Type", result.by_citizen_type))
        elif section.id == "timeSeries":
            lines.extend(["## Time Series", "", "| Day | transport | homeEnergy | diet | total |", "|---:|---:|---:|---:|---:|"])
            for point in result.time_series:
                day = int(point["day"])
                lines.append(
                    f"| {day} | {point['transport']:.3f} | {point['homeEnergy']:.3f} | {point['diet']:.3f} | {point['total']:.3f} |"
                )
            lines.append("")

    return "\n".join(lines)
