# Development Guide

## 1. Требования

- Python 3.11+
- Git
- GitHub account для работы с PR/CI
- JEV API key нужен только для live-экспериментов с Real JEV

Проект намеренно не требует Claude Code для запуска. Claude Code — инструмент разработки, а не часть runtime solver.

## 2. Клонирование и установка

```bash
git clone https://github.com/designfordrink/jev-vlns.git
cd jev-vlns

python -m venv .venv
```

Активация:

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

## 3. Быстрая проверка

Запустить все unit/integration tests:

```bash
pytest
```

Тесты не требуют JEV API key. Для CI используется FakeJevClient и mock HTTP response.

## 4. Offline benchmark

Базовый benchmark полностью работает без JEV API.

Минимальный запуск:

```bash
python experiments/run_benchmark.py
```

Фиксированная серия:

```bash
python experiments/run_benchmark.py --seeds 1 2 3 4 5 --iterations 50
```

Расширенная матрица с Oracle/System-1 surrogate:

```bash
python experiments/run_benchmark.py --extended --seeds 1 2 3 4 5 --iterations 50
```

Сохранить raw result:

```bash
python experiments/run_benchmark.py \
  --extended \
  --seeds 1 2 3 4 5 \
  --iterations 50 \
  --output experiments/runs/matrix.json
```

Проанализировать результат:

```bash
python experiments/analyze_benchmark.py \
  experiments/runs/matrix.json \
  --output experiments/runs/analysis.md
```

## 5. Real JEV через OpenRouter

Создай локальный environment file на основе `.env.example`. Реальный API key не должен попадать в Git.

Пример переменных:

```dotenv
OPENROUTER_API_KEY=...
TYPESAFE_BASE_URL=https://openrouter.ai/api
JEV_MODEL=typesafe/jev-1.13
JEV_TIMEOUT_SECONDS=30
JEV_MIN_CONFIDENCE=0.0
```

Текущий Python client читает environment variables и также поддерживает `~/.claude/jev.env`.

Для live M9:

```bash
python experiments/run_real_jev_destroy.py \
  --seeds 1 2 3 4 5 \
  --iterations 50
```

Для smoke test:

```bash
python experiments/run_real_jev_destroy.py --seeds 1 --iterations 3
```

Live benchmark требует API key и явно завершается с ошибкой, если ключ не настроен.

## 6. Что именно измеряет M9

M9 фиксирует Repair = Random и сравнивает:

- Random Destroy + Random Repair
- Oracle Destroy + Random Repair
- Real JEV Destroy + Random Repair

Дополнительно собираются:

- число JEV calls;
- fallback count;
- confidence;
- latency;
- input/output tokens;
- provider-reported cost;
- destroy regret.

Подробнее: [M9.md](M9.md).

## 7. Работа с ветками

Обычный цикл:

```bash
git checkout -b my-change
# edit
pytest
git add .
git commit -m "..."
git push -u origin my-change
```

После push GitHub Actions автоматически запускает CI.

## 8. Перед Pull Request

Минимальная локальная проверка:

```bash
pytest
python experiments/run_benchmark.py --extended --seeds 1 2 3 4 5 --iterations 50
```

Для изменений JEV client дополнительно проверить unit test, не вызывающий реальный API.

## 9. Секреты

Никогда не коммитить:

- API keys;
- `.env`;
- `~/.claude/jev.env`;
- секреты в benchmark artifacts;
- секреты в replay/state dumps.

В репозитории хранится только `.env.example`.

## 10. Принцип разработки

Сначала deterministic code и тесты, затем JEV.

JEV выбирает среди заранее сгенерированных legal candidates. Он не отвечает за:

- правила Container Stack;
- legality;
- mutation State;
- objective;
- acceptance.

Это позволяет сравнивать Random, Greedy, Oracle и JEV как взаимозаменяемые selectors.
