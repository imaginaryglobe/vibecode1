# Rules Spec

```yaml
emissionFactors:
  transport:
    car_kgco2_per_mile: 0.404
    bus_kgco2_per_mile: 0.089
    walk_kgco2_per_mile: 0.0
    bike_kgco2_per_mile: 0.0
  homeEnergy:
    kgco2_per_kwh: 0.39
  diet:
    meal_mixed_kgco2: 1.7
    meal_meat_heavy_kgco2: 3.3
    meal_plant_forward_kgco2: 1.1

rules:
  - id: transport_emissions
    formula: "miles * factor_for_mode"
  - id: home_energy_emissions
    formula: "kwh * kgco2_per_kwh"
  - id: diet_emissions
    formula: "meals * factor_for_pattern"
```
