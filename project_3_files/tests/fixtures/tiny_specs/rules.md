# tiny rules

```yaml
emissionFactors:
  transport:
    car_kgco2_per_mile: 0.4
    bus_kgco2_per_mile: 0.1
    walk_kgco2_per_mile: 0.0
    bike_kgco2_per_mile: 0.0
  homeEnergy:
    kgco2_per_kwh: 0.5
  diet:
    meal_mixed_kgco2: 1.5
    meal_meat_heavy_kgco2: 3.0
    meal_plant_forward_kgco2: 1.0
rules:
  - id: transport_emissions
    formula: "miles * factor_for_mode"
  - id: home_energy_emissions
    formula: "kwh * kgco2_per_kwh"
  - id: diet_emissions
    formula: "meals * factor_for_pattern"
```
