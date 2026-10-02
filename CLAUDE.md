# CLAUDE.md

## Project

This repository implements the JEV + VLNS research prototype described in `docs/TRD.md`.

## Mandatory first step

Before changing code, read:

1. `docs/TRD.md`
2. the current repository structure
3. relevant tests

## Architecture rule

Keep this separation:

`State → Candidate Generator → Selector → Executor → Evaluator`

JEV is a selector, not an environment, validator, executor, or planner.

Do not put JEV API calls inside Container Stack game logic.

## Development order

Follow milestones in the TRD:

M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8 ...

Do not implement later milestones early unless explicitly requested.

## Testing

For every change:

1. add/update tests;
2. run the relevant tests;
3. run the complete test suite when practical;
4. report failures rather than hiding them.

JEV API access must never be required for CI. Use FakeJevClient.

## JEV integration

The reference implementation is:

https://github.com/designfordrink/jev-plugin

Reuse its useful ideas around:

- credential discovery;
- TypeSafe/OpenRouter support;
- `/v1/systemone`;
- typed questions;
- confidence;
- timeout/retry;
- graceful failure;
- logging.

Do not copy the plugin wholesale. Keep the runtime dependency small and isolate it under `src/jev_vlns/jev/`.

## Research discipline

Do not claim that JEV improves the solver until a controlled benchmark demonstrates it.

Every comparison must use the same:

- instances;
- seeds;
- iteration budget;
- time budget;
- initial solutions.

Always preserve Random/Greedy baselines.

## Security

Never commit API keys, tokens, `.env`, `~/.claude/jev.env`, or secret-bearing logs.

## Scope

The current goal is a research laboratory, not a production optimizer.

Prefer small, explicit, testable code over frameworks and abstractions that are not required by the TRD.
