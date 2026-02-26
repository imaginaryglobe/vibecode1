# Scenarios Spec

```yaml
scenarios:
  - name: baseline
    overrides: {}

  - name: transit_push
    overrides:
      citizens:
        Commuter:
          transport:
            mode: bus

  - name: remote_work_wave
    overrides:
      world:
        population:
          distribution:
            - type: Student
              share: 0.30
            - type: Commuter
              share: 0.30
            - type: RemoteWorker
              share: 0.40

  - name: equity_access
    overrides:
      citizens:
        Student:
          transport:
            mode: bus
        Commuter:
          transport:
            mode: bus
```
