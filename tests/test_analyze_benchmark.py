from experiments.analyze_benchmark import deltas_vs_random_random, render_markdown, summarize

def _row(mode: str, seed: int, moves: int, feasible: bool = True) -> dict:
    return {"mode": mode, "seed": seed, "iterations": 10, "feasible": feasible, "moves": moves,
            "projected_objective": float(moves), "destroy_jev_calls": 0, "repair_jev_calls": 0}

def test_summarize_reports_distribution():
    summary = summarize([_row("random-random", 1, 20), _row("random-random", 2, 10), _row("random-random", 3, 30)])
    assert summary == [{
        "mode": "random-random", "n": 3, "feasible_rate": 1.0,
        "min": 10, "median": 20, "mean": 20, "max": 30, "stdev": 10.0,
        "mean_destroy_regret": 0.0, "mean_repair_regret": 0.0,
    }]

def test_deltas_are_paired_by_seed():
    rows = [_row("random-random", 1, 20), _row("heuristic-heuristic", 1, 15), _row("random-random", 2, 30), _row("heuristic-heuristic", 2, 35)]
    assert deltas_vs_random_random(rows) == [{"seed": 1, "mode": "heuristic-heuristic", "baseline_moves": 20, "moves": 15, "delta_moves": -5}, {"seed": 2, "mode": "heuristic-heuristic", "baseline_moves": 30, "moves": 35, "delta_moves": 5}]

def test_markdown_contains_summary_and_guardrails():
    payload = {"seeds": [1, 2], "iterations": 10, "results": [_row("random-random", 1, 20), _row("heuristic-heuristic", 1, 15)]}
    report = render_markdown(payload)
    assert "## Summary by mode" in report
    assert "## Per-seed delta vs random-random" in report
    assert "negative means fewer final moves" in report
    assert "not evidence about real JEV quality" in report