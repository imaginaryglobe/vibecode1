# Prejudices / Bias Audit

```yaml
audit:
  - assumption: "Everyone can choose any transport mode"
    risk: "Ignores disability, transit deserts, and safety constraints"
    fix:
      addConstraint: "transportAccess list required for each citizen type"

  - assumption: "Commuting happens the same all week"
    risk: "Ignores weekend behavior and job schedule variance"
    fix:
      addCitizenTypeField: "transport.commuteDaysPerWeek"

  - assumption: "Home energy usage is fixed across housing quality"
    risk: "Flattens efficiency differences by income/housing age"
    fix:
      addCitizenTypeField: "home.kind + future efficiency band"

  - assumption: "Food patterns are evenly available and affordable"
    risk: "Misses food desert and budget constraints"
    fix:
      addConstraint: "future scenario constraints for diet availability"

  - assumption: "Remote work access is equal"
    risk: "Overstates ability to reduce transport emissions"
    fix:
      addConstraint: "scenario-based remote eligibility shares"
```
