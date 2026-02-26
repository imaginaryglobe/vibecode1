# Metrics Spec

```yaml
report:
  sections:
    - id: headline
      fields: [totalKgCO2, avgKgCO2PerCitizenPerDay]
    - id: byCategory
      breakdown: [transport, homeEnergy, diet]
    - id: byCitizenType
      breakdown: [Student, Commuter, RemoteWorker]
    - id: timeSeries
      granularity: day
```
