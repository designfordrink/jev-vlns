# Experiments Guide

## 1. Зачем нужны отдельные experiments

Исследовательский код должен позволять отделить:

- механику задачи;
- алгоритм поиска;
- selector;
- JEV;
- измерение результата.

Поэтому benchmark запускается отдельными CLI-скриптами, а результаты сохраняются отдельно от core package.

## 2. Основной benchmark

`experiments/run_benchmark.py` запускает матрицу режимов.

Пример:

```bash
python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json
```

Затем:

```bash
python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

## 3. Seeds

Seed фиксирует случайность эксперимента.

Для честного сравнения разные selectors должны работать на одинаковых seeds и одинаковом iteration budget.

Один запуск на одном seed не является достаточным основанием для вывода о качестве метода.

## 4. Oracle

Oracle — диагностический control.

Он перебирает доступные кандидаты текущего neighborhood и показывает, насколько далеко Random или другой selector находится от лучшего доступного кандидата.

Oracle не является реалистичным production solver: его задача — показать landscape пространства локальных решений.

## 5. Regret

**Regret** здесь — разница между результатом выбранного кандидата и лучшим кандидатом, доступным в том же локальном выборе.

Для Destroy:

```
D-regret = selected destroy score - best destroy score
```

Для Repair аналогично сравнивается выбранный repair с лучшим доступным repair для выбранного destroy.

Чем ближе regret к нулю, тем ближе выбор к локальному Oracle для данного определения score.

## 6. M9 Real JEV

M9 проверяет отдельную гипотезу: способен ли реальный JEV выбирать Destroy candidate так, чтобы его выбор отличался от случайного и был ближе к Oracle landscape.

Repair остаётся Random, чтобы не смешивать два эффекта.

Основная команда:

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

Smoke test:

```bash
python experiments/run_real_jev_destroy.py --seeds 1 --iterations 3
```

## 7. Интерпретация

Нужно различать:

**Solver outcome**

- final moves;
- feasibility;
- improvement from initial solution.

**Decision quality**

- destroy regret;
- repair regret;
- candidate count.

**Runtime/cost**

- JEV calls;
- latency;
- token usage;
- provider-reported cost;
- fallback rate.

Хороший эксперимент не смешивает эти уровни.

Например, низкий D-regret показывает качество локального выбора относительно текущего Oracle, но сам по себе не доказывает улучшение конечного решения.

## 8. Reproducibility

Для каждого benchmark фиксируются:

- seed;
- iteration budget;
- mode;
- initial state/solution;
- selector configuration.

Для live JEV результат не обязательно бит-в-бит воспроизводим: внешний API может вернуть другой ответ.

Поэтому для JEV полезно сохранять decision telemetry и отдельно поддерживать replay.

## 9. Не делать premature conclusions

До сравнения серии одинаковых seeds не следует делать выводы о преимуществе конкретного selector.

Минимальный исследовательский протокол:

```
5+ seeds
×
fixed iteration budget
×
same initial instances
×
same acceptance rule
```

Затем анализировать как aggregate, так и per-seed результаты.
