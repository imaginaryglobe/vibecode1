from pathlib import Path

import pytest

from eco.config.loader import load_all_specs
from eco.util.errors import EcoConfigError


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "tiny_specs"


def test_loader_reads_tiny_specs() -> None:
    config = load_all_specs(FIXTURE_DIR)
    assert config.world.world.name == "Tiny"
    assert len(config.citizens.citizenTypes) == 2
    assert {scenario.name for scenario in config.scenarios.scenarios} == {"baseline", "bus_shift"}


def test_loader_fails_for_bad_distribution(tmp_path: Path) -> None:
    bad_specs = tmp_path / "specs"
    bad_specs.mkdir(parents=True)

    for name in ["citizens.md", "rules.md", "metrics.md", "scenarios.md", "prejudices.md"]:
        (bad_specs / name).write_text((FIXTURE_DIR / name).read_text(encoding="utf-8"), encoding="utf-8")

    bad_world = """# bad\n\n```yaml
world:
  name: Bad
  description: bad
simulation:
  defaultDays: 2
  seed: 1
population:
  totalCount: 10
  distribution:
    - type: Student
      share: 0.7
    - type: Commuter
      share: 0.5
```
"""
    (bad_specs / "world.md").write_text(bad_world, encoding="utf-8")

    with pytest.raises(EcoConfigError):
        load_all_specs(bad_specs)
