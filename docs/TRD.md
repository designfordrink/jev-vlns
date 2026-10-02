# TRD — jev-vlns

## 1. Назначение

`jev-vlns` — исследовательский стенд для проверки архитектуры **JEV + VLNS** на простой визуальной задаче укладки контейнеров.

**VLNS (Variable Large Neighborhood Search)** — вариант локального поиска, в котором на каждой итерации часть текущего решения разрушается, а затем восстанавливается.

**JEV / System-1** — быстрый decision-модель, которая получает конечный набор вариантов и выбирает один из них. JEV не должен самостоятельно придумывать произвольное действие.

Цель первого этапа — не получить «умного игрового агента», а экспериментально проверить гипотезу:

> если пространство допустимых локальных решений заранее генерируется обычным кодом, может ли JEV эффективно выбирать между ними внутри цикла destroy → repair → evaluate?

Проект должен затем позволить заменить Container Stack на Railroad Blocking Problem без переписывания ядра поиска и selector-интерфейса.

---

## 2. Целевые среды выполнения

Основная среда разработки:

- Claude Code в Claude Desktop / Claude Code Desktop;
- Python 3.11+;
- Git;
- macOS / Linux / Windows;
- JEV API через TypeSafe или OpenRouter.

Проект должен быть пригоден для запуска обычным Python CLI без Claude Code.

Claude Code используется как **System-2 / orchestration layer** разработки, а JEV — как **System-1 / fast decision layer** внутри приложения.

Это принципиально разные роли:

```
Claude Code
   │
   │ проектирование, код, анализ экспериментов
   ▼
jev-vlns
   │
   ├── simulator
   ├── candidate generator
   ├── JEV selector
   ├── VLNS
   └── evaluator
```

---

## 3. Архитектурный принцип

Базовый pipeline:

```
State
  ↓
Candidate Generator
  ↓
Selector
  ↓
Executor
  ↓
New State
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

Для JEV:

```
State + Candidates
       ↓
      JEV
       ↓
Selected Candidate
       ↓
Deterministic Executor
```

JEV находится только в точке выбора. Правила допустимости и изменение состояния принадлежат обычному детерминированному коду.

---

## 4. Что НЕ должен делать JEV

JEV не должен:

- придумывать Python-код;
- напрямую менять State;
- самостоятельно проверять все правила игры;
- генерировать произвольные координаты;
- принимать решение на основании скрытого состояния;
- заменять Validator;
- заменять Objective Function;
- выполнять файловые операции;
- быть необходимым для запуска baseline.

Если JEV недоступен, эксперимент должен продолжать работать с Random или Greedy selector.

Это позволит измерять именно вклад JEV.

---

## 5. Интеграция JEV

### 5.1. Источник идей

В качестве reference implementation используется:

urldesignfordrink/jev-pluginhttps://github.com/designfordrink/jev-plugin

Из него следует использовать архитектурные идеи, а не копировать plugin целиком:

1. отдельный API client;
2. credentials через environment / `~/.claude/jev.env`;
3. поддержка TypeSafe и OpenRouter;
4. timeout и retry;
5. единый JSON request;
6. typed questions;
7. обработка confidence;
8. логирование расходов и ответов;
9. graceful failure — ошибка JEV не должна ломать основной pipeline.

Reference plugin использует запрос к `/v1/systemone` с формой:

```json
{
  "model": "jev-latest",
  "state": {},
  "questions": {}
}
```

В новом проекте этот механизм должен быть изолирован в:

```
src/jev_vlns/jev/
├── client.py
├── types.py
├── selector.py
└── config.py
```

### 5.2. Credentials

Поддержать:

1. `JEV_API_KEY`
2. `TYPESAFE_API_KEY`
3. `OPENROUTER_API_KEY`
4. `TYPESAFE_BASE_URL`

Также поддержать:

```
~/.claude/jev.env
```

и локальный:

```
.env
```

Секреты никогда не должны попадать в git, state dump, benchmark или replay.

### 5.3. Provider detection

Если используется OpenRouter key `sk-or-...`, по умолчанию использовать OpenRouter.

Иначе использовать TypeSafe.

Но provider должен быть явно переопределяемым через `TYPESAFE_BASE_URL`.

### 5.4. JEV request abstraction

Внутренний интерфейс:

```python
class JevClient(Protocol):
    def decide(
        self,
        state: dict,
        question: DecisionQuestion,
    ) -> DecisionResult:
        ...
```

Selector не должен знать URL, API key или HTTP.

---

## 6. Typed decision model

В Container Stack JEV должен получать **не список Python objects**, а компактное сериализованное состояние.

Пример:

```json
{
  "task": "choose_repair",
  "objective": "minimize_total_moves",
  "state": {
    "stacks": [
      ["C1", "C7"],
      ["C2"],
      [],
      ["C3", "C4"]
    ],
    "containers": {
      "C1": {"destination": "A", "priority": 2},
      "C2": {"destination": "B", "priority": 1},
      "C3": {"destination": "A", "priority": 3},
      "C4": {"destination": "C", "priority": 1}
    }
  },
  "candidates": {
    "r1": "move C7 from stack 0 to stack 2",
    "r2": "move C7 from stack 0 to stack 3",
    "r3": "deliver C7"
  }
}
```

Вопрос JEV:

> Which candidate is the best legal next repair action for minimizing future total moves?

Criteria должны быть сформулированы так, чтобы JEV выбирал **только ID кандидата**.

Ответ:

```json
{
  "choice": "r2",
  "confidence": 0.81
}
```

Если конкретный API возвращает другой формат, адаптер должен нормализовать его в `DecisionResult`.

---

## 7. Candidate-first design

Это ключевой принцип проекта.

Не:

```
JEV → invent action
```

а:

```
Environment
    ↓
generate legal candidates
    ↓
JEV chooses candidate
    ↓
Environment executes candidate
```

Таким образом:

- legality определяется кодом;
- search space определяется кодом;
- JEV выполняет ranking / choice;
- executor остаётся детерминированным.

Это делает эксперимент воспроизводимым.

---

## 8. Core interfaces

### State

```python
@dataclass(frozen=True)
class State:
    ...
```

State должен быть immutable с точки зрения selector.

### Action

```python
@dataclass(frozen=True)
class Action:
    id: str
    kind: str
    payload: dict
```

### Candidate Generator

```python
class CandidateGenerator(Protocol):
    def generate(self, state: State) -> list[Action]:
        ...
```

### Selector

```python
class Selector(Protocol):
    def select(
        self,
        state: State,
        candidates: Sequence[Action],
    ) -> Action:
        ...
```

Реализации:

- `RandomSelector`
- `GreedySelector`
- `JevSelector`

### Executor

```python
class Executor(Protocol):
    def apply(self, state: State, action: Action) -> State:
        ...
```

### Evaluator

```python
@dataclass(frozen=True)
class Evaluation:
    feasible: bool
    objective: float
    metrics: dict
```

---

## 9. Container Stack model

### Board

MVP: 5×5.

Каждая клетка содержит стек.

Максимальная высота:

```
MAX_STACK_HEIGHT = 3
```

### Container

Минимальные поля:

- `id`
- `destination`
- `priority`

Позднее:

- `commodity`
- `weight`
- `due_time`

### Legal actions

MVP:

1. move top container from stack A to stack B;
2. deliver top container if destination condition satisfied.

Все legal actions генерируются environment.

---

## 10. Objective

MVP objective:

```
minimize(total_moves)
```

Дополнительные metrics:

- delivered_count;
- blocked_containers;
- empty_moves;
- max_stack_height;
- average stack height;
- number of iterations;
- wall-clock time;
- JEV calls;
- JEV failures.

Objective и feasibility должны быть независимы от selector.

---

## 11. Initial solution

VLNS не должен начинать с утверждения, что решение оптимально.

Допустимые источники initial solution:

1. Random;
2. Greedy;
3. deterministic seed layout;
4. позже — saved best solution.

Для каждого benchmark run фиксировать:

- instance seed;
- initial solution;
- selector;
- search seed.

---

## 12. Destroy

Destroy переводит полное решение в частичное.

MVP destroy operators:

- `random_k`
- `stack_k`
- `blocked_group`
- `worst_local_region`

На первом этапе JEV получает небольшой набор уже допустимых destroy candidates.

Например:

```
d1 = destroy stacks [0,1]
d2 = destroy stacks [2,3]
d3 = destroy top 3 blocked containers
d4 = destroy containers with highest estimated delay
```

JEV выбирает **WHERE**.

---

## 13. Repair

Repair получает partial solution и создаёт небольшой набор legal repairs.

Например:

```
r1 = place C7 on stack 2
r2 = place C7 on stack 4
r3 = deliver C7
```

JEV выбирает **HOW**.

---

## 14. VLNS acceptance

MVP использовать простой acceptance:

```
accept if objective(new) < objective(current)
```

Позже добавить:

- simulated annealing;
- threshold acceptance;
- adaptive acceptance.

Не добавлять это до получения базовых результатов.

---

## 15. Experiment matrix

Минимальный обязательный эксперимент:

| Destroy | Repair |
|---|---|
| Random | Random |
| JEV | Random |
| Random | JEV |
| JEV | JEV |

Каждая конфигурация должна использовать одинаковые:

- instances;
- seeds;
- iteration budget;
- time budget.

Главный вопрос:

> JEV приносит пользу как Destroy selector, как Repair selector или только в комбинации?

---

## 16. JEV modes

Нужно поддержать три режима.

### 16.1. Disabled

JEV вообще не вызывается.

Используется для baseline.

### 16.2. Shadow

JEV вызывается и делает выбор, но выбранное действие не используется.

Основной selector продолжает работу.

Это позволяет:

- измерять latency;
- считать стоимость;
- анализировать disagreement;
- собирать dataset.

### 16.3. Active

JEV реально определяет выбранный candidate.

Это основной экспериментальный режим.

---

## 17. Fallback

При:

- timeout;
- HTTP error;
- invalid JSON;
- unknown candidate;
- low confidence;

selector должен использовать fallback.

MVP:

```
JEV → fallback Greedy
```

Для эксперимента также иметь:

```
JEV → fallback Random
```

Все fallback события логировать.

---

## 18. Confidence policy

JEV не должен считаться oracle.

Минимальная политика:

```
confidence >= threshold
    → accept JEV choice

confidence < threshold
    → fallback
```

Threshold должен быть конфигурируемым.

Например:

```
jev:
  min_confidence: 0.70
```

В benchmark confidence не должен менять baseline задним числом: все правила должны быть зафиксированы до запуска серии.

---

## 19. Logging

Каждый JEV decision должен иметь запись:

```json
{
  "run_id": "...",
  "iteration": 17,
  "mode": "active",
  "decision_type": "repair",
  "candidate_ids": ["r1", "r2", "r3"],
  "selected": "r2",
  "confidence": 0.81,
  "latency_ms": 214,
  "cost_usd": 0.000001,
  "fallback": false
}
```

Не сохранять API key.

Logs:

```
experiments/runs/<run_id>/
├── config.json
├── decisions.jsonl
├── states.jsonl
├── metrics.json
└── replay.json
```

---

## 20. Replay

Любой experiment run должен быть воспроизводим по:

```
instance_seed
search_seed
config
initial_state
```

JEV active replay не гарантирует побитовую идентичность из-за внешнего API.

Поэтому поддержать:

### Deterministic replay

Сохранять JEV decision ID и selected candidate.

### Live replay

Повторно обращаться к JEV.

В отчёте явно различать эти режимы.

---

## 21. Claude Code Desktop integration

Claude Code должен использоваться как development orchestrator.

В корне проекта создать `CLAUDE.md`.

Он должен заставлять Claude Code:

1. сначала читать `docs/TRD.md`;
2. не менять core interfaces без явного основания;
3. объяснять архитектурные изменения;
4. запускать tests после изменений;
5. не добавлять LLM/JEV туда, где достаточно deterministic code;
6. сохранять экспериментальные параметры;
7. не смешивать benchmark code и production-like core;
8. использовать JEV через `JevSelector`, а не напрямую из game logic.

Claude Code не должен сам быть частью runtime benchmark.

То есть:

```
Claude Code ≠ solver
```

Claude Code помогает разрабатывать solver.

---

## 22. Recommended Claude Code workflow

Для каждого milestone:

```
1. Claude reads TRD
2. Claude inspects current repository
3. Claude proposes minimal implementation
4. Claude writes tests
5. Claude implements
6. Claude runs tests
7. Claude runs small experiment
8. Claude records result
9. Git commit
```

Не переходить к следующему milestone, если предыдущий не имеет работающего теста или демонстрации.

---

## 23. Repository structure

Целевая структура:

```
jev-vlns/
├── CLAUDE.md
├── README.md
├── LICENSE
├── pyproject.toml
│
├── docs/
│   ├── TRD.md
│   ├── experiments.md
│   └── architecture.md
│
├── src/
│   └── jev_vlns/
│       ├── core/
│       │   ├── state.py
│       │   ├── action.py
│       │   ├── candidate.py
│       │   ├── selector.py
│       │   └── evaluator.py
│       │
│       ├── container_stack/
│       │   ├── state.py
│       │   ├── actions.py
│       │   ├── destroy.py
│       │   ├── repair.py
│       │   └── renderer.py
│       │
│       ├── search/
│       │   └── vlns.py
│       │
│       ├── selectors/
│       │   ├── random.py
│       │   ├── greedy.py
│       │   └── jev.py
│       │
│       ├── jev/
│       │   ├── client.py
│       │   ├── types.py
│       │   ├── selector.py
│       │   └── config.py
│       │
│       ├── evaluation/
│       │   └── benchmark.py
│       │
│       └── visualization/
│           └── replay.py
│
├── tests/
│
└── experiments/
    └── runs/
```

---

## 24. Dependency policy

MVP должен использовать минимум зависимостей.

Предпочтительно:

- Python standard library;
- pytest;
- matplotlib — только когда начнётся visualization;
- requests/httpx — только если это оправдано для JEV client.

Не использовать LangChain/LangGraph и другие agent frameworks без отдельного архитектурного решения.

Причина: нам нужно исследовать именно JEV + search, а не framework overhead.

---

## 25. Testing strategy

### Unit tests

Проверять:

- legal actions;
- stack constraints;
- delivery rules;
- destroy;
- repair;
- validator;
- objective;
- selector contract;
- JEV response normalization.

### Property tests

Позже:

- apply(action) сохраняет допустимость;
- destroy + repair может восстановить feasible solution;
- delivered containers не появляются снова.

### Integration tests

JEV API не должен быть обязательным для CI.

Использовать FakeJevClient.

---

## 26. Fake JEV

Обязательный компонент для разработки.

```python
class FakeJevClient:
    def decide(...):
        return DecisionResult(...)
```

Режимы:

- always_first;
- always_last;
- scripted;
- probabilistic;
- replay.

Это позволит тестировать весь JEV pipeline без API key.

---

## 27. Metrics

Основные:

- best objective;
- final objective;
- improvement from initial;
- feasibility rate;
- iterations;
- accepted moves;
- JEV decisions;
- fallback rate;
- average JEV latency;
- p50/p95 latency;
- estimated API cost.

Не использовать только «победил/проиграл». Нужна серия одинаковых runs.

---

## 28. Definition of Done для M0

M0 завершён, когда:

- есть `pyproject.toml`;
- package импортируется;
- pytest запускается;
- `CLAUDE.md` существует;
- `docs/TRD.md` существует;
- есть базовые core interfaces;
- FakeJevClient определён;
- секреты исключены из git.

## 29. Definition of Done для M1

M1 завершён, когда:

- Container Stack state работает;
- legal actions генерируются;
- actions применяются детерминированно;
- validator определяет feasibility;
- есть seed;
- можно вывести состояние в текстовом виде;
- минимум 10 unit tests проходят.

## 30. Definition of Done для M4

LNS baseline завершён, когда:

- есть initial feasible solution;
- destroy создаёт partial solution;
- repair создаёт feasible solution;
- objective вычисляется до/после;
- acceptance работает;
- benchmark можно повторить по seed.

## 31. Definition of Done для M8

JEV-VLNS завершён, когда:

- работают четыре комбинации Random/JEV Destroy/Repair;
- JEV можно отключить;
- JEV можно заменить FakeJevClient;
- fallback работает;
- решения и JEV decisions логируются;
- существует воспроизводимый benchmark;
- можно визуально сравнить траектории.

---

## 32. Roadmap

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
M9  Benchmark
 ↓
M10 Visualization
 ↓
M11 JEV Choice vs Score
 ↓
M12 Learned local policy
 ↓
M13 Railroad Blocking Problem
```

---

## 33. Первое практическое действие

После добавления этого TRD следующий Claude Code task:

> Прочитай `docs/TRD.md` и реализуй только M0. Не переходи к Container Stack. Создай минимальный Python package, core interfaces, FakeJevClient, pytest configuration и CLAUDE.md. Запусти tests. Не добавляй реальные вызовы JEV API до M6.

После успешного M0:

> Реализуй M1 согласно TRD. Сначала tests, затем simulator. Не добавляй JEV и VLNS.

Это намеренное разделение: сначала проверяем механику задачи, затем search, затем JEV.
