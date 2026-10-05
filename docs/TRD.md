# TRD — jev-vlns

> **Status:** living document. This document describes the current architecture and research contract of the repository. Historical milestone plans are retained only where they explain the experiment design; they are not treated as the current implementation specification.

## 1. Назначение

`jev-vlns` — исследовательский прототип для проверки идеи **JEV + VLNS (Variable Large Neighborhood Search)** на задаче Container Stack.

VLNS повторяет цикл:

```
current solution
      ↓
destroy
      ↓
partial solution
      ↓
repair
      ↓
candidate solution
      ↓
evaluate
      ↓
accept / reject
      ↓
next iteration
```

Ключевая гипотеза проекта:

> если пространство допустимых локальных решений заранее генерируется обычным детерминированным кодом, может ли JEV эффективно выбирать между конечным набором кандидатов внутри поискового цикла?

Это не попытка заменить обычный solver LLM-агентом. JEV используется как **selector / decision layer**, а environment, candidate generation, execution, validation и objective остаются в коде.

---

## 2. Текущий статус

Реализованы этапы **M9–M13**: Real JEV Destroy, Visualization/Replay, JEV Choice vs Local Landscape, Real JEV Choice Quality и Real JEV End-to-End Validation. Перед live-запусками M12/M13 текущий инженерный шаг — сделать Destroy decision context state-aware.

M9 специально фиксирует Repair как Random и сравнивает:

| Destroy | Repair |
|---|---|
| Random | Random |
| Oracle | Random |
| **Real JEV** | Random |

Это изолирует вопрос:

> насколько полезен реальный JEV именно как Destroy selector, когда Repair не зависит от JEV?

Текущий M9 использует реальный JEV через HTTP API. Поддерживается конфигурация через OpenRouter; provider telemetry сохраняется в результатах решения.

Для CI и offline benchmark реальный API **не требуется**.

---

## 3. Основной архитектурный принцип: candidate-first

Правильная граница ответственности:

```
Environment
    ↓
generate legal candidates
    ↓
JEV / baseline selector
    ↓
selected candidate
    ↓
deterministic executor
    ↓
new state
```

JEV не должен:

- напрямую менять состояние;
- придумывать произвольные действия;
- самостоятельно обеспечивать legality;
- заменять validator;
- заменять objective;
- быть обязательным условием запуска baseline;
- скрывать ошибку отсутствующей конфигурации за другим экспериментальным режимом.

Таким образом можно отдельно измерять качество **выбора**, не смешивая его с качеством генерации или исполнения действий.

---

## 4. VLNS pipeline

Для текущего эксперимента логика имеет вид:

```
Initial solution
      ↓
Destroy candidate generator
      ↓
Destroy selector
      ├── Random
      ├── Oracle
      └── Real JEV
      ↓
Partial solution
      ↓
Random Repair
      ↓
Candidate solution
      ↓
Objective / feasibility
      ↓
Acceptance
      ↓
Next iteration
```

На M9 меняется только Destroy selector.

Это принципиальное условие контролируемого эксперимента.

---

## 5. Что находится внутри JEV boundary

JEV получает сериализованное состояние задачи и конечный список допустимых кандидатов.

Концептуально:

```State + legal candidates
          ↓
        JEV
          ↓
       choice ID
```

JEV возвращает выбор кандидата и confidence.

Нормализованный результат внутри проекта содержит, в частности:

- selected choice;
- confidence;
- input tokens;
- output tokens;
- provider-reported cost;
- latency;
- error/fallback information.

API-specific формат не должен распространяться по solver-коду. HTTP и normalization изолированы в `src/jev_vlns/jev/`.

---

## 6A. State-aware candidate context

Для Destroy decision JEV получает не только глобальное сериализованное состояние, но и отдельный context для каждого legal candidate.

Candidate context строится из текущего state непосредственно перед выбором и включает только локально релевантные факты: affected stack, stack destination, height, top container metadata и exposed container metadata.

Это не переносит solver logic в JEV. Candidate generation, legality, execution, validation, objective и Oracle остаются за пределами JEV.

Candidate context не содержит Oracle scores, rankings, regret или future evaluation results.

Все runtime instructions и candidate context, передаваемые JEV, формируются на английском языке.

## 6. JEV client

Основная реализация находится в:

```
src/jev_vlns/jev/
├── client.py
├── config.py
├── types.py
└── ...
```

Client вызывает:

```
POST {base_url}/v1/systemone
```

и нормализует текущий TypeSafe Choice response, включая:

```
answers.choice.choice
answers.choice.confidence
```

Поддерживаются credentials:

1. `JEV_API_KEY`
2. `TYPESAFE_API_KEY`
3. `OPENROUTER_API_KEY`

Также поддерживаются environment/config overrides, включая:

- `TYPESAFE_BASE_URL`;
- `JEV_MODEL`;
- `JEV_TIMEOUT_SECONDS`;
- `JEV_MIN_CONFIDENCE`;
- локальный `~/.claude/jev.env`.

Для M9 пример OpenRouter:

```dotenv
OPENROUTER_API_KEY=
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
JEV_TIMEOUT_SECONDS=30
JEV_MIN_CONFIDENCE=0.0
```

Секреты не должны попадать в repository, benchmark artifacts или state dumps.

---

## 7. Ошибки и отсутствие JEV

Реальный M9 не должен молча превращаться в baseline, если API key отсутствует.

Например:

```
missing API key
    ↓
explicit configuration error
```

Это необходимо для корректной интерпретации эксперимента: иначе можно ошибочно принять offline baseline за результат Real JEV.

При runtime errors проект может учитывать fallback согласно конкретному selector/experiment contract; каждое такое событие должно быть измеряемым и не должно скрываться в итоговой статистике.

---

## 8. Confidence

Confidence является отдельным сигналом JEV.

Конфигурация:

```
JEV_MIN_CONFIDENCE
```

определяет порог, ниже которого решение может быть передано fallback-механизму там, где это разрешено текущим экспериментальным контрактом.

Важно:

> confidence не является доказательством правильности выбора.

Для benchmark series threshold должен быть заранее зафиксирован и одинаков для сравниваемых runs.

---

## 9. Provider cost telemetry

Стоимость запроса не должна оцениваться только по локальному времени.

Если provider возвращает:

```json
{
  "usage": {
    "input_tokens": 123,
    "output_tokens": 12,
    "cost": 0.000123
  }
}
```

то:

```
DecisionResult.cost_usd
```

получает это значение, а клиент накапливает:

```
JevClientStats.total_cost_usd
```

Также сохраняются input/output token counts.

Это позволяет оценивать JEV не только по solver quality, но и по экономике:

```
quality / latency / tokens / USD
```

---

## 10. Container Stack

Container Stack — текущая экспериментальная среда, а не конечная цель проекта.

Задача используется потому, что она позволяет контролируемо отделить:

- state;
- legal candidate generation;
- selection;
- deterministic execution;
- objective;
- search.

В дальнейшем тот же selector/search boundary должен быть пригоден для других задач, включая Railroad Blocking Problem.

---

## 11. Baselines и controls

Проект использует несколько типов selectors/controls.

### Random

Случайный выбор допустимого кандидата.

Это основной простейший baseline.

### Oracle

Контроль верхней границы для локального выбора: selector использует доступную информацию о кандидатах и выбирает лучший вариант согласно локальному reference objective.

Oracle не является реальным алгоритмом, который предполагается использовать в production. Его роль — дать ориентир для regret.

### FakeJEV / surrogate controls

Используются для разработки и offline проверки JEV pipeline без внешнего API.

### Real JEV

Используется только в live experiment.

---

## 12. Regret

Для M9 важен не только итоговый objective, но и качество отдельных Destroy choices.

Вводится **Destroy regret** относительно Oracle.

Концептуально:

```
D-regret =
quality(oracle destroy)
vs.
quality(selected destroy)
```

Конкретная реализация метрики должна оставаться единой для сравниваемых runs.

Цель M9:

> проверить, находится ли поведение Real JEV ближе к Oracle, чем Random, а не просто получить один хороший final score.

---

## 13. Контролируемый benchmark

Для честного сравнения должны быть одинаковыми:

- instance;
- initial state;
- seed;
- iteration budget;
- candidate generator;
- Repair;
- objective;
- feasibility rules;
- acceptance rule.

Меняется только исследуемый selector.

Для M9:

```
Destroy ∈ {Random, Oracle, Real JEV}
Repair = Random
```

Нельзя делать вывод о superiority JEV по одному запуску.

Минимально полезный результат — fixed-seed series.

Пример live series:

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

---

## 14. Metrics

Основные solver metrics:

- final moves;
- feasibility;
- improvement from initial solution;
- accepted moves;
- iterations.

JEV-specific:

- JEV calls;
- successful decisions;
- fallback count;
- confidence;
- average latency;
- input tokens;
- output tokens;
- provider-reported cost USD.

Research-specific:

- Destroy regret;
- Repair regret, когда Repair-JEV снова станет частью контролируемого эксперимента;
- candidate counts;
- per-seed deltas.

Главное правило:

> итоговый score, стоимость и latency рассматриваются совместно.

---

## 15. Offline benchmark

Offline benchmark не должен зависеть от API.

Текущий benchmark runner:

```
experiments/run_benchmark.py
```

поддерживает стандартный и extended режимы.

Extended matrix включает комбинации:

- random-random;
- jev-random;
- random-jev;
- jev-jev;
- heuristic-random;
- random-heuristic;
- heuristic-heuristic;
- oracle-random;
- random-oracle;
- oracle-oracle.

Это offline research matrix. Она не заменяет M9 live experiment.

Анализ:

```
experiments/analyze_benchmark.py
```

строит summary по режимам и per-seed comparison.

---

## 16. CI

GitHub Actions должны проверять проект без необходимости JEV API key.

Текущий CI:

1. устанавливает Python 3.11;
2. устанавливает package + dev dependencies;
3. запускает `pytest`;
4. запускает extended offline benchmark на фиксированных seeds;
5. запускает analysis;
6. сохраняет benchmark artifacts.

Реальный JEV API не является частью обязательного CI.

Это необходимо по двум причинам:

- CI должен быть воспроизводимым;
- внешний API нельзя делать обязательной зависимостью обычного test pipeline.

---

## 17. Reproducibility

Offline runs должны быть воспроизводимыми по:

- seed;
- instance;
- initial state;
- iteration budget;
- selector configuration;
- objective;
- acceptance configuration.

Live JEV runs дополнительно зависят от внешней модели/provider и поэтому не гарантируют побитовую идентичность.

Для live experiments обязательно сохранять telemetry, достаточную для последующего анализа:

- model;
- selected candidate;
- confidence;
- latency;
- tokens;
- cost;
- fallback/error status.

API secrets сохраняться не должны.

---

## 18. Test strategy

Минимально тестируются:

- JEV response normalization;
- Choice parsing;
- confidence parsing;
- token telemetry;
- cost telemetry;
- missing API key behavior;
- benchmark interfaces;
- deterministic/offline selectors;
- objective and experiment accounting.

Особенно важен regression test для текущего TypeSafe response contract.

Live API не должен быть необходим для обычного unit test suite.

---

## 19. Current experiment entry points

Основные команды:

### Offline benchmark

```bash
python experiments/run_benchmark.py
```

### Extended offline matrix

```bash
python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json
```

### Analyze benchmark

```bash
python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

### Real JEV Destroy

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

---

## 20. Repository structure — current implementation

Документ не должен навязывать будущую структуру как уже существующую.

Текущие важные части:

```
jev-vlns/
├── README.md
├── README.ru.md
├── pyproject.toml
├── .env.example
├── CLAUDE.md
│
├── docs/
│   ├── TRD.md
│   ├── M9.md
│   ├── EXPERIMENTS.md
│   ├── DEVELOPMENT.md
│   └── CI.md
│
├── src/
│   └── jev_vlns/
│       ├── jev/
│       │   ├── client.py
│       │   ├── config.py
│       │   └── types.py
│       └── evaluation/
│           └── benchmark.py
│
├── tests/
│
└── experiments/
    ├── run_benchmark.py
    ├── run_real_jev_destroy.py
    ├── analyze_benchmark.py
    └── runs/
```

Структура может расширяться, но документация должна различать **current implementation** и **target architecture**.

---

## 21. Что не следует делать

До появления экспериментального основания не следует:

- превращать JEV в свободный action generator;
- переносить legality/validation в LLM;
- добавлять agent framework без необходимости;
- делать Claude Code частью runtime solver;
- смешивать benchmark accounting с core simulator;
- скрывать API failures;
- сравнивать разные методы на разных seeds/instances;
- делать вывод о solver improvement по одному run;
- использовать стоимость как единственный критерий качества;
- усложнять acceptance policy до получения чистого baseline.

---

## 22. Claude Code и System-2 / System-1

Claude Code используется как development/orchestration layer.

JEV используется как runtime decision layer.

```
Claude Code
    ↓
разработка / анализ / изменение проекта

jev-vlns runtime
    ↓
search / simulator / evaluator
    ↓
JEV System-1
```

Claude Code не является частью benchmark solver.

Это важно для чистоты эксперимента: исследуется вклад JEV внутри алгоритма, а не качество внешнего coding agent.

---

## 23. Research roadmap

Историческая последовательность проекта:

```
M0  Foundation
M1  Container simulator
M2  Validator + objective
M3  Random / Greedy
M4  LNS
M5  Selector interface
M6  JEV Repair
M7  JEV Destroy
M8  JEV + VLNS
M9  Real JEV Destroy        ← current
M10 Visualization / Replay
M11 JEV Choice vs Score
M12 Learned local policy
M13 Railroad Blocking Problem
```

### Current research priority

После M9 следующий шаг должен быть не «добавить больше сложности», а сделать результат наблюдаемым и проверяемым:

1. завершить fixed-seed M9 series;
2. сохранить raw results;
3. проверить D-regret;
4. визуализировать/реплеить решения;
5. только после этого переходить к следующему типу JEV decision.

---

## 24. Definition of Done — M9

M9 считается исследовательски завершённым, когда:

- Real JEV действительно вызывается через configured provider;
- отсутствие API key приводит к явной ошибке;
- Repair остаётся Random;
- Random / Oracle / Real JEV используют одинаковый experimental setup;
- fixed-seed series выполнена;
- JEV calls учитываются;
- fallback учитывается;
- confidence учитывается;
- latency учитывается;
- input/output tokens учитываются;
- provider-reported cost учитывается;
- Destroy regret рассчитан;
- raw results сохранены;
- conclusions не основаны на одном run.

---

## 25. Следующий исследовательский вопрос

После M9 основной вопрос:

> **Может ли JEV выбирать хорошие локальные Destroy-операторы существенно лучше Random и насколько близко его поведение к Oracle при приемлемых latency и cost?**

Если ответ положительный, следующий шаг — сделать поведение наблюдаемым через replay/visualization и затем проверить, сохраняется ли эффект в других формах выбора.

Если ответ отрицательный, это также полезный результат: необходимо определить, проблема находится в JEV selection quality, представлении состояния, candidate design, confidence policy или самой постановке Destroy choice.

---

## 26. Связанные документы

- `README.md` — основное описание проекта.
- `README.ru.md` — русская версия.
- `docs/M9.md` — подробный контракт текущего Real JEV Destroy experiment.
- `docs/EXPERIMENTS.md` — экспериментальные процедуры.
- `docs/DEVELOPMENT.md` — development workflow.
- `docs/CI.md` — CI workflow.

