# Tier 6 — AI/ML Security Progress Tracker

## Status: 🚧 In Progress

---

## Modules

| # | Module                         | Status        | Notes |
|---|--------------------------------|---------------|-------|
| 1 | SKILL.md                       | ✅ Complete   | Frontmatter + sections |
| 2 | adversarial_gen.py             | ✅ Complete   | FGSM + PGD |
| 3 | model_extract.py               | ✅ Complete   | Random + boundary strategies |
| 4 | prompt_injection_advanced.py   | ✅ Complete   | Multi-turn, encoding, role-play |
| 5 | PROGRESS.md                    | ✅ Complete   | This file |

---

## Learning Objectives Checklist

- [ ] Understand gradient-based evasion (FGSM, PGD, C&W)
- [ ] Implement adversarial example generator
- [ ] Build model extraction pipeline
- [ ] Train surrogate model from API outputs
- [ ] Craft multi-turn prompt injections
- [ ] Encode payloads to bypass filters
- [ ] Use role-play to shift context
- [ ] Document detection/blue-team patterns

---

## Exercises

### Exercise 1: Adversarial Examples
- [ ] Run `adversarial_gen.py --method fgsm --epsilon 0.05`
- [ ] Run `adversarial_gen.py --method pgd --epsilon 0.05 --iterations 50`
- [ ] Compare L∞ / L₂ perturbation metrics
- [ ] Try different epsilon values (0.01, 0.03, 0.1, 0.3)

### Exercise 2: Model Extraction
- [ ] Run with `--budget 100` and `--budget 5000` — observe agreement change
- [ ] Compare `random` vs `decision_boundary` strategies
- [ ] Try to achieve >95% victim agreement
- [ ] Reflect: what defenses could prevent this?

### Exercise 3: Prompt Injection
- [ ] Run with `--technique all` to see all three methods
- [ ] Try `--encoding-method unicode` for zero-width smuggling
- [ ] Add a custom payload with `--payload "your text here"`
- [ ] Analyze which detection rules trigger

---

## Key Takeaways

1. **Small perturbations fool models** — ε=0.03 changes predictions
2. **Black-box models are extractable** — query budget matters more than architecture
3. **Context is the attack surface** — multi-turn > single-prompt
4. **Defense requires layers** — no single rule catches all injections

---

## Notes & Observations

_Record findings here as you work through exercises._

```
[Date]: [Your notes on what you learned or observed]
```

---

## Completion Criteria

Tier 6 is complete when:
- [ ] All 5 files are created and readable
- [ ] All 3 Python scripts run without errors
- [ ] At least 2 exercises are completed
- [ ] Key takeaways are understood and documented
