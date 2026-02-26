# tiny citizens

```yaml
citizenTypes:
  - name: Student
    home:
      kind: dorm
      kwhPerDay: 6
    transport:
      mode: walk
      commuteMilesPerDay: 1
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: mixed

  - name: Commuter
    home:
      kind: house
      kwhPerDay: 12
    transport:
      mode: car
      commuteMilesPerDay: 10
      commuteDaysPerWeek: 5
    diet:
      mealsPerDay: 3
      pattern: meat_heavy
```
