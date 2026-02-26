# Eco-Tracker Social Simulator

Spec-driven simulator where Markdown/YAML files in `specs/` are the source of truth.

## Quickstart

```bash
pip install -e .[dev]
eco validate
eco run --scenario baseline --days 30 --seed 42
```
