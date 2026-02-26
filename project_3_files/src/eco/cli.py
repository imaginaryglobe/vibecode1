# author jaden fang jason lyu
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import typer
from rich.console import Console

from eco.config.loader import load_all_specs, load_with_scenario
from eco.report.render_json import render_json_payload
from eco.report.render_md import render_markdown
from eco.sim.engine import simulate
from eco.util.errors import EcoConfigError
from eco.util.hashing import spec_hash

app = typer.Typer(help="Eco-Tracker social simulator")
console = Console()


def _default_paths() -> tuple[Path, Path]:
    root = Path(__file__).resolve().parents[2]
    return root / "specs", root / "out"


@app.command("validate")
def validate(spec_dir: Path | None = typer.Option(None, "--spec-dir")) -> None:
    specs, _ = _default_paths()
    target = spec_dir or specs
    try:
        config = load_all_specs(target)
    except EcoConfigError as exc:
        console.print(f"[red]Validation failed:[/red] {exc}")
        raise typer.Exit(1)

    scenario_names = ", ".join(s.name for s in config.scenarios.scenarios)
    console.print(f"[green]Specs valid[/green]. Scenarios: {scenario_names}")


@app.command("list-scenarios")
def list_scenarios(spec_dir: Path | None = typer.Option(None, "--spec-dir")) -> None:
    specs, _ = _default_paths()
    target = spec_dir or specs
    config = load_all_specs(target)
    for scenario in config.scenarios.scenarios:
        console.print(scenario.name)


@app.command("run")
def run(
    scenario: str = typer.Option("baseline", "--scenario"),
    days: int | None = typer.Option(None, "--days"),
    seed: int | None = typer.Option(None, "--seed"),
    spec_dir: Path | None = typer.Option(None, "--spec-dir"),
    out_dir: Path | None = typer.Option(None, "--out-dir"),
) -> None:
    default_specs, default_out = _default_paths()
    specs = spec_dir or default_specs
    out = out_dir or default_out

    try:
        config = load_with_scenario(specs, scenario)
    except EcoConfigError as exc:
        console.print(f"[red]Run failed:[/red] {exc}")
        raise typer.Exit(1)

    chosen_days = days or config.world.simulation.defaultDays
    chosen_seed = seed if seed is not None else (config.world.simulation.seed or 42)

    result = simulate(config, days=chosen_days, seed=chosen_seed)
    spec_digest = spec_hash(specs)
    payload = render_json_payload(result, scenario=scenario, seed=chosen_seed)
    markdown = render_markdown(
        result,
        metrics=config.metrics,
        scenario=scenario,
        days=chosen_days,
        seed=chosen_seed,
        spec_hash=spec_digest,
    )

    out.mkdir(parents=True, exist_ok=True)
    (out / "report.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (out / "report.md").write_text(markdown, encoding="utf-8")
    (out / "run_meta.json").write_text(
        json.dumps(
            {
                "scenario": scenario,
                "days": chosen_days,
                "seed": chosen_seed,
                "specHash": spec_digest,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    console.print("[green]Run complete[/green] -> out/report.md, out/report.json, out/run_meta.json")


@app.command("report")
def report(
    format: str = typer.Option("markdown", "--format"),
    scenario: str = typer.Option("baseline", "--scenario"),
    days: int | None = typer.Option(None, "--days"),
    seed: int | None = typer.Option(None, "--seed"),
    spec_dir: Path | None = typer.Option(None, "--spec-dir"),
    out_dir: Path | None = typer.Option(None, "--out-dir"),
) -> None:
    run(scenario=scenario, days=days, seed=seed, spec_dir=spec_dir, out_dir=out_dir)
    _, default_out = _default_paths()
    out = out_dir or default_out
    if format == "markdown":
        console.print((out / "report.md").read_text(encoding="utf-8"))
    elif format == "json":
        console.print((out / "report.json").read_text(encoding="utf-8"))
    else:
        console.print("[red]Unknown format[/red]. Use markdown or json")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
