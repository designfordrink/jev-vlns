# jev-vlns — документация на русском

Исследовательский прототип для проверки подхода **JEV + VLNS (Variable Large Neighborhood Search)**.

Проект использует небольшую среду Container Stack как контролируемый стенд. Архитектура построена так, чтобы ядро поиска и интерфейс selector можно было позднее перенести на другие задачи оптимизации, включая Railroad Blocking Problem.

**English:** [README.md](README.md)

## Что исследуется

**VLNS** — вариант локального поиска: часть текущего решения разрушается (**Destroy**), после чего решение восстанавливается (**Repair**).

**JEV / System-1** в этом проекте используется как selector: программа заранее генерирует конечный набор допустимых кандидатов, а JEV выбирает один из них.

Основной pipeline:

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

Для VLNS:

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

JEV **не** отвечает за правила среды, проверку допустимости, изменение состояния или вычисление objective. Его роль — сделать локальный выбор среди уже подготовленных вариантов.

## Текущий этап

Репозиторий находится на этапе **M9 — Real JEV Destroy**.

В M9 механизм Repair фиксирован как Random. Сравниваются:

| Destroy | Repair |
|---|---|
| Random | Random |
| Oracle | Random |
| **Real JEV** | Random |

Это позволяет отдельно исследовать качество выбора Destroy, не смешивая его с качеством Repair.

Для benchmark фиксируются и/или измеряются:

- конечное число ходов;
- feasibility;
- число кандидатов;
- Destroy regret;
- число вызовов JEV;
- fallback events;
- confidence;
- latency;
- input/output tokens;
- provider-reported cost.

Главный исследовательский вопрос M9:

> Может ли реальный JEV выбирать Destroy-neighborhood так, чтобы его локальные решения отличались от Random и приближались к Oracle landscape?

Один запуск не считается достаточным основанием для вывода о качестве метода.

## Быстрый старт

### Требования

- Python 3.11+
- Git

Клонирование:

```bash
git clone https://github.com/designfordrink/jev-vlns.git
cd jev-vlns
```

Создание virtual environment:

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

Установка проекта и dev-зависимостей:

```bash
python -m pip install -e ".[dev]"
```

## Запуск тестов

```bash
pytest
```

Обычные тесты **не требуют JEV API key**.

CI использует локальные/fake JEV clients и mock/recorded response shapes, поэтому тестовый контур не зависит от внешнего API.

## Offline benchmark

Основной benchmark можно запускать полностью без API.

Минимальный запуск:

```bash
python experiments/run_benchmark.py
```

Фиксированная серия:

```bash
python experiments/run_benchmark.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

Расширенная матрица:

```bash
python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json
```

Расширенный benchmark включает Random/JEV-compatible controls, heuristic System-1 surrogate и Oracle modes. Heuristic surrogate является детерминированным control и **не является реальным JEV**.

Анализ результатов:

```bash
python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

## Real JEV через OpenRouter

Real JEV является опциональным. Он не нужен для обычных тестов и offline benchmark.

Создай локальную конфигурацию на основе [.env.example](.env.example).

Для OpenRouter текущая конфигурация:

```dotenv
OPENROUTER_API_KEY=...
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
JEV_TIMEOUT_SECONDS=30
JEV_MIN_CONFIDENCE=0.0
```

Клиент также умеет читать:

- `JEV_API_KEY`;
- `TYPESAFE_API_KEY`;
- `OPENROUTER_API_KEY`;
- `~/.claude/jev.env`;
- переменные окружения.

Переменные окружения имеют приоритет над `~/.claude/jev.env`.

**API key нельзя коммитить в Git.**

### Smoke test

```bash
python experiments/run_real_jev_destroy.py --seeds 1 --iterations 3
```

### Серия M9

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

При отсутствии API key live M9 завершается с ошибкой. Он **не** превращается молча в baseline.

### Телеметрия стоимости

Provider response с:

```json
{
  "usage": {
    "input_tokens": 123,
    "output_tokens": 12,
    "cost": 0.000123
  }
}
```

нормализуется в:

- `DecisionResult.cost_usd`;
- `JevClientStats.total_cost_usd`.

Также собираются latency и token usage.

## Как устроен выбор JEV

JEV получает сериализованное состояние и конечный набор legal candidates.

Схема:

```
Environment
    ↓
Generate legal candidates
    ↓
JEV
    ↓
Selected candidate ID
    ↓
Deterministic executor
```

То есть JEV не придумывает произвольное действие.

Например, вместо:

```
JEV → "придумай действие"
```

используется:

```
candidates = {
  "d1": "...",
  "d2": "...",
  "d3": "..."
}

JEV → "d2"
```

После выбора обычный код выполняет действие и проверяет результат.

## Container Stack

Текущий стенд использует небольшую задачу укладки контейнеров.

В сериализованном состоянии передаются, в частности:

- stacks;
- destinations;
- containers;
- container destination;
- priority;
- текущие moves;
- delivered containers.

JEV работает только с представлением состояния, подготовленным application code.

## Oracle и regret

**Oracle** — диагностический control, а не production solver.

Он может посмотреть на доступные кандидаты текущего neighborhood и выбрать лучший кандидат относительно заданного локального score.

Для Destroy:

```
D-regret = selected destroy score - best available destroy score
```

Для Repair аналогично сравнивается выбранный repair с лучшим доступным вариантом для данного Destroy.

Regret нужно интерпретировать относительно конкретного локального выбора. Низкий D-regret сам по себе **не доказывает**, что конечное решение solver стало лучше.

## Что измерять

Результаты разделяются на три уровня.

### 1. Solver outcome

- final moves;
- feasibility;
- improvement относительно initial solution.

### 2. Decision quality

- Destroy regret;
- Repair regret;
- candidate count.

### 3. Runtime и стоимость

- JEV calls;
- fallback count;
- confidence;
- latency;
- input/output tokens;
- provider-reported cost.

Такое разделение важно: качество отдельного решения JEV и качество всего solver — разные измерения.

## Воспроизводимость

Для offline benchmark фиксируются:

- seed;
- iteration budget;
- mode;
- initial state;
- selector configuration.

Сравниваемые методы должны использовать одинаковые seeds и одинаковый бюджет.

Для Real JEV побитовая воспроизводимость не гарантируется, поскольку ответ приходит от внешнего API.

Поэтому live-эксперименты должны отдельно сохранять telemetry и, по мере развития проекта, поддерживать replay.

## CI

GitHub Actions workflow находится в:

```
.github/workflows/benchmark.yml
```

CI выполняет:

1. checkout;
2. установку Python 3.11;
3. `pip install -e ".[dev]"`;
4. `pytest`;
5. extended benchmark на seeds 1..5 и 50 iterations;
6. анализ benchmark;
7. публикацию `matrix.json` и `analysis.md` как artifact.

Обычный CI **не вызывает реальный JEV API**. Это сделано для воспроизводимости, безопасности секретов и отсутствия неожиданных расходов.

Подробности: [docs/CI.md](docs/CI.md).

## Структура репозитория

```
jev-vlns/
├── README.md
├── README.ru.md
├── pyproject.toml
├── .env.example
│
├── docs/
│   ├── TRD.md
│   ├── DEVELOPMENT.md
│   ├── CI.md
│   ├── EXPERIMENTS.md
│   └── M9.md
│
├── src/jev_vlns/
│   ├── container_stack/
│   ├── evaluation/
│   ├── jev/
│   ├── search/
│   └── selectors/
│
├── tests/
│
└── experiments/
    ├── run_benchmark.py
    ├── run_real_jev_destroy.py
    ├── analyze_benchmark.py
    └── runs/
```

## Принципы проекта

1. Сначала детерминированно генерировать legal candidates.
2. Использовать JEV как selector, а не как executor.
3. Держать validator и objective вне JEV.
4. Сравнивать с Random и Oracle controls.
5. Фиксировать seeds и budgets до сравнения методов.
6. Разделять solver outcome, decision quality, runtime и API cost.
7. Не делать выводов по одному запуску.
8. Не делать JEV обязательным для baseline и CI.
9. Не хранить секреты в benchmark artifacts или state dumps.
10. Не добавлять LLM там, где достаточно обычного deterministic code.

## Текущая архитектура JEV client

Python client изолирован в:

```
src/jev_vlns/jev/
├── client.py
├── config.py
├── types.py
└── fake.py
```

Нормализованный результат имеет поля:

```python
DecisionResult(
    choice=...,
    confidence=...,
    latency_ms=...,
    cost_usd=...,
    raw=...,
)
```

Selector не должен знать URL, API key или детали HTTP-протокола.

## Документация проекта

- [Development Guide](docs/DEVELOPMENT.md) — установка, тесты, benchmark и Real JEV.
- [CI Guide](docs/CI.md) — GitHub Actions и локальное воспроизведение проверок.
- [Experiments Guide](docs/EXPERIMENTS.md) — методология benchmark, seeds, Oracle и regret.
- [TRD](docs/TRD.md) — архитектурные требования и исходный технический дизайн.
- [M9 — Real JEV Destroy](docs/M9.md) — исходный live-протокол.
- [M19 — Real JEV K=2](docs/M19_REAL_JEV_K2.md) — отрицательный live-результат.
- [M20 — Expected-Value Landscape](docs/LOCAL_NEXT_STEP_M20.md) — выравнивание downstream objective.
- [M21 — State Representation Diagnostics](docs/LOCAL_NEXT_STEP_M21.md) — текущий диагностический эксперимент.
- [.env.example](.env.example) — шаблон конфигурации без секретов.

## Roadmap

Текущая последовательность:

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

Следующий шаг после M21 определяется его результатами. Если B/C/D не улучшат качество выбора, наиболее сильной следующей гипотезой станет отказ от требования JEV сразу выбирать один лучший кандидат и переход к **ranking/proposal → Top-K → deterministic rollout/evaluator**. Если один из вариантов улучшит выбор, сначала будет изолирован именно выигравший элемент контекста.

## Дополнительные документы

Если нужно понять проект глубже, рекомендуется читать в таком порядке:

1. этот README;
2. [docs/M21 — State Representation Diagnostics](docs/LOCAL_NEXT_STEP_M21.md);
3. [docs/M20 — Expected-Value Landscape](docs/LOCAL_NEXT_STEP_M20.md);
4. [docs/M19_REAL_JEV_K2.md](docs/M19_REAL_JEV_K2.md);
3. [docs/EXPERIMENTS.md](docs/EXPERIMENTS.md);
4. [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md);
5. [docs/CI.md](docs/CI.md);
6. [docs/TRD.md](docs/TRD.md).

