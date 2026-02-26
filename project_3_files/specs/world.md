# World Spec

```yaml
world:
  name: "West Lafayette (Toy Model)"
  description: "Small town carbon sim for class."
simulation:
  defaultDays: 30
  seed: 42
population:
  totalCount: 2000
  distribution:
    - type: Student
      share: 0.35
    - type: Commuter
      share: 0.45
    - type: RemoteWorker
      share: 0.20
```
