# jev-vlns

Research prototype for testing **JEV + VLNS** (Variable Large Neighborhood Search).

The project starts with a small Container Stack environment and is designed so the search core can later be reused for the Railroad Blocking Problem.

## Architecture

`State → Candidate Generator → Selector → Executor → Evaluator`

JEV is a selector: the environment generates legal candidates, JEV chooses among them, and deterministic code executes the selected candidate.

## Development

Python 3.11+.

```bash
python -m pip install -e ".[dev]"
pytest
```

See [docs/TRD.md](docs/TRD.md) for the technical requirements and milestone plan.


## M8.5 — Oracle / Candidate Landscape

The current Container Stack neighborhood is small enough to enumerate exactly. The research harness therefore includes an **Oracle** control: it evaluates every legal destroy candidate and every complete repair plan using the same greedy-completion objective used by VLNS.

This is not a production optimizer. It answers a diagnostic question:

> Does the current neighborhood contain substantially better candidates that Random or JEV simply fail to select?

The benchmark reports:

- **Destroy regret** — selected destroy neighborhood score minus the best destroy score available in that iteration.
- **Repair regret** — selected complete repair score minus the best repair score for the selected destroy.
- candidate counts for both stages.

Oracle modes are `oracle-random`, `random-oracle`, and `oracle-oracle`.
