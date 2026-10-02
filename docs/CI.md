# CI Guide

## Что такое CI в этом проекте

**CI (Continuous Integration)** — автоматическая проверка GitHub Actions, которая запускается после push и для Pull Request.

В проекте workflow находится в:

```
.github/workflows/benchmark.yml
```

Локально CI запускать не требуется. Его аналог для разработчика — выполнить те же основные команды на своей машине.

## Что делает GitHub Actions

Workflow выполняет:

1. checkout репозитория;
2. устанавливает Python 3.11;
3. устанавливает проект через `pip install -e '.[dev]'`;
4. запускает `pytest`;
5. запускает extended benchmark на seeds 1..5 с 50 итерациями;
6. строит Markdown analysis;
7. сохраняет `matrix.json` и `analysis.md` как workflow artifacts.

## Push и Pull Request

При push запускается:

```
Benchmark / test-and-benchmark (push)
```

При Pull Request запускается отдельная проверка:

```
Benchmark / test-and-benchmark (pull_request)
```

Поэтому в PR могут одновременно отображаться две проверки.

## Если check failed

Открыть failed check и посмотреть шаг, на котором произошла ошибка.

Типичный порядок:

```
Install
  ↓
Tests
  ↓
Benchmark matrix
  ↓
Analyze benchmark
  ↓
Upload benchmark artifacts
```

Если падает `Tests`, сначала исправляется код или тест.

Если падает benchmark, проверяется воспроизводимость локально:

```bash
python experiments/run_benchmark.py --extended --seeds 1 2 3 4 5 --iterations 50
```

## Live JEV в CI

Обычный CI **не вызывает реальный JEV API**.

Это сделано намеренно:

- CI должен быть воспроизводимым;
- API key не нужен;
- тесты не должны зависеть от внешнего сервиса;
- benchmark CI не должен неожиданно расходовать деньги.

Real JEV запускается отдельно локально или в специально настроенном workflow с секретом.

## Artifacts

После успешного benchmark workflow создаёт artifact:

```
jev-vlns-benchmark
├── matrix.json
└── analysis.md
```

`matrix.json` — машинно-читаемые результаты.

`analysis.md` — человекочитаемый отчёт.

## Как повторить CI локально

Основная последовательность:

```bash
python -m pip install -e ".[dev]"
pytest

python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json

python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

Это не запускает сам GitHub Actions, но повторяет его существенную проверочную часть.
