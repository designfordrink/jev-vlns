# jev-vlns

**Русская версия:** [README.ru.md](README.ru.md)

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

## Research reset: M15+

The project follows the methodological remediation plan in [Research Remediation Plan](docs/RESEARCH_REMEDIATION_PLAN.md). The key distinction is between:

- **search/projected objective** — the objective used while exploring virtual Destroy/Repair configurations;
- **executable objective** — the number of actions in a deterministic executable plan;
- **exact reference** — an exact small-instance optimum, when available.

Until the physical reconfiguration path from an initial state to a VLNS virtual configuration is modeled, historical VLNS numbers must be described as **projected-search / greedy-completion evidence**, not as validated physical-move performance.

See [Objective Semantics](docs/OBJECTIVE_SEMANTICS.md) and [Research Remediation Plan](docs/RESEARCH_REMEDIATION_PLAN.md).

## Current research stage: M21

M18 established the protocol for variable Destroy neighborhoods and produced a matched 10-seed comparison:

| K | Mean moves | Mean candidates |
|---:|---:|---:|
| 1 | 15.10 | 4.50 |
| 2 | 14.80 | 12.47 |
| 3 | 14.80 | 20.60 |

K=2 was selected for the next live experiment because it improved the mean over K=1 while K=3 provided no additional mean improvement and substantially enlarged the candidate set. The M18 evidence remains projected-search / greedy-completion evidence.

M19 then tested **Real JEV Destroy + Random Repair** against **Random Destroy + Random Repair** with K=2, non-adjacent neighborhoods enabled, 50 iterations and seeds 1..5.

M19 result:

- Random mean: **15.8**
- Real JEV mean: **17.4**
- Mean paired delta (JEV − Random): **+1.6**
- JEV wins: **0/5**
- JEV calls: **250/250 successful**
- Fallbacks: **0**
- Choice quality: Top-1 **0.004**, mean rank **9.84**, mean normalized regret **0.972**

This is the first strong negative live result. It is **not** explained by API failure, infeasibility or fallback. Real JEV made legal successful choices, but those choices were poor on the tested K=2 candidate landscape.

The M20 Expected-Value Landscape analysis aligned the offline target with the actual Random-Repair downstream process. Real JEV remained substantially below the aligned target, so M21 isolates the next hypothesis: whether JEV lacks useful state representation or struggles with elementary counting/bookkeeping.

M21 compares four frozen-context variants: **A_compact** (M20 control), **B_full_state**, **C_consequence**, and **D_decision_ready**. Only the state/candidate serialization changes; model, prompt, K=2 candidate set, Random Repair, greedy completion, EV evaluator, seeds and sample budget remain fixed.

See [M21 Local Execution Handoff](docs/LOCAL_NEXT_STEP_M21.md). The live run requires the user's local JEV/OpenRouter credentials and is intentionally not part of CI.

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
.venv\\Scripts\\Activate.ps1
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

M19 fixed K=2 run:

```powershell
python experiments/run_m13_real_jev_end_to_end.py `
  --seeds 1 2 3 4 5 `
  --iterations 50 `
  --destroy-min-stacks 2 `
  --destroy-max-stacks 2 `
  --destroy-include-non-adjacent
```

No real API key is stored in the repository.

## Documentation

- [Development Guide](docs/DEVELOPMENT.md) — installation, tests, benchmarks and Real JEV.
- [CI Guide](docs/CI.md) — what GitHub Actions does and how to reproduce its checks locally.
- [Experiments Guide](docs/EXPERIMENTS.md) — benchmark methodology, seeds, Oracle and regret.
- [TRD](docs/TRD.md) — technical requirements and architecture.
- [M9 — Real JEV Destroy](docs/M9.md) — Real JEV Destroy protocol.
- [M12 — Real JEV Choice Quality](docs/M12.md) — live selector-quality protocol.
- [M13 — Real JEV End-to-End Validation](docs/M13.md) — paired live end-to-end protocol.
- [M19 — Real JEV with K=2](docs/M19_REAL_JEV_K2.md) — fixed K=2 live experiment protocol and result context.
- [M20 — JEV Decision Failure Analysis](docs/LOCAL_NEXT_STEP_M20.md) — controlled diagnostic handoff.
- [JEV State-Aware Context](docs/JEV_CONTEXT.md) — state-derived candidate context contract.
- [.env.example](.env.example) — configuration template without secrets.

## Repository architecture

```
jev-vlns/
├── docs/
│   ├── TRD.md
│   ├── DEVELOPMENT.md
│   ├── CI.md
│   ├── EXPERIMENTS.md
│   ├── M9.md
│   ├── M19_REAL_JEV_K2.md
│   ├── LOCAL_NEXT_STEP_M20.md
│   └── LOCAL_NEXT_STEP_M21.md
├── src/jev_vlns/
├── tests/
└── experiments/
```

## Research principles

1. Generate legal candidates with deterministic code.
2. Let the selector choose among candidates.
3. Keep validator and objective outside JEV.
4. Compare against Random and Oracle controls.
5. Fix seeds and budgets before comparing methods.
6. Separate solver outcome, decision quality, runtime and API cost.
7. Diagnose negative results before optimizing the selector.
8. Never leak Oracle/evaluation results into the live JEV request.
9. Do not claim physical-move superiority until the executable reconfiguration path is modeled.
10. Do not infer solver superiority from a single run.

See [TRD.md](docs/TRD.md) for the architecture and roadmap.
