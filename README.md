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
