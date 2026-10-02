# jev-vlns

Research prototype for testing **JEV + VLNS** (Variable Large Neighborhood Search).

The project starts with a small Container Stack environment and is designed so the search core can later be reused for the Railroad Blocking Problem.

## What is the project?

**VLNS (Variable Large Neighborhood Search)** is a local-search method in which part of the current solution is destroyed and then repaired.

**JEV / System-1** is used as a fast selector: the program generates a finite set of legal candidates, and JEV chooses one of them.

The central architecture is:

```
State
  ↓
Candidate Generator
  ↓
Selector
  ↓
Executor
  ↓
Evaluator
```

For VLNS:

```
Current Solution
      ↓
Destroy Generator
      ↓
Destroy Selector
      ↓
Partial Solution
      ↓
Repair Candidate Generator
      ↓
Repair Selector
      ↓
Repaired Solution
      ↓
Validator + Objective
      ↓
Accept / Reject
      ↓
Next Iteration
```

JEV does **not** own environment rules, validation, objective calculation or state mutation.

## Current research stage

The repository has reached the **M9 Real JEV Destroy** experiment.

M9 keeps Repair fixed to Random and compares:

| Destroy | Repair |
|---|---|
| Random | Random |
| Oracle | Random |
| Real JEV | Random |

The purpose is to measure the quality of JEV's local Destroy choices separately from the quality of the Repair mechanism.

The benchmark records final moves, feasibility, candidate counts, regret, JEV calls, fallback events, latency, token usage and provider-reported cost.

## Quick start

Requirements:

- Python 3.11+
- Git

Install:

```bash
python -m venv .venv
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

Tests do **not** require a JEV API key.

## Run the offline benchmark

```bash
python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json
```

Analyze the result:

```bash
python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

The same benchmark is executed by GitHub Actions as part of CI.

## Run Real JEV

Real JEV is optional and is **not** required for normal tests or CI.

For OpenRouter:

```dotenv
OPENROUTER_API_KEY=...
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
JEV_TIMEOUT_SECONDS=30
JEV_MIN_CONFIDENCE=0.0
```

See [.env.example](.env.example).

Smoke test:

```bash
python experiments/run_real_jev_destroy.py --seeds 1 --iterations 3
```

M9 series:

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

No real API key is stored in the repository.

## Documentation

- [Development Guide](docs/DEVELOPMENT.md) — installation, tests, benchmarks and Real JEV.
- [CI Guide](docs/CI.md) — what GitHub Actions does and how to reproduce its checks locally.
- [Experiments Guide](docs/EXPERIMENTS.md) — benchmark methodology, seeds, Oracle and regret.
- [TRD](docs/TRD.md) — technical requirements and architecture.
- [M9 — Real JEV Destroy](docs/M9.md) — current live JEV experiment.
- [.env.example](.env.example) — configuration template without secrets.

## Repository architecture

```
jev-vlns/
├── docs/
│   ├── TRD.md
│   ├── DEVELOPMENT.md
│   ├── CI.md
│   ├── EXPERIMENTS.md
│   └── M9.md
├── src/jev_vlns/
├── tests/
└── experiments/
    ├── run_benchmark.py
    ├── analyze_benchmark.py
    └── runs/
```

## Research principles

1. Generate legal candidates with deterministic code.
2. Let the selector choose among candidates.
3. Keep validator and objective outside JEV.
4. Compare against Random and Oracle controls.
5. Fix seeds and budgets before comparing methods.
6. Separate solver outcome, decision quality, runtime and API cost.
7. Do not infer solver superiority from a single run.

See [TRD.md](docs/TRD.md) for the full architecture and roadmap.

## Roadmap

```
M0  Project foundation
 ↓
M1  Container simulator
 ↓
M2  Validator + objective
 ↓
M3  Random + Greedy
 ↓
M4  LNS
 ↓
M5  Selector interface
 ↓
M6  JEV Repair
 ↓
M7  JEV Destroy
 ↓
M8  JEV + VLNS
 ↓
M9  Real JEV Destroy
 ↓
M10 Visualization
 ↓
M11 JEV Choice vs Score
 ↓
M12 Learned local policy
 ↓
M13 Railroad Blocking Problem
```
