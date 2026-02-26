# Citizens Spec

```yaml
citizenTypes:
  - name: Student
    home:
      kind: dorm
      kwhPerDay: 6
    transport:
      mode: walk
      commuteMilesPerDay: 0.5
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: mixed
    transportAccess: [walk, bus]

  - name: Commuter
    home:
      kind: house
      kwhPerDay: 18
    transport:
      mode: car
      commuteMilesPerDay: 18
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: meat_heavy
    transportAccess: [car, bus]

  - name: RemoteWorker
    home:
      kind: apartment
      kwhPerDay: 14
    transport:
      mode: bike
      commuteMilesPerDay: 2
      commuteDaysPerWeek: 2
    diet:
      mealsPerDay: 3
      pattern: plant_forward
    transportAccess: [bike, walk]
```
