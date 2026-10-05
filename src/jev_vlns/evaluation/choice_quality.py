"""Metrics for evaluating discrete selector choices against a local landscape."""

from __future__ import annotations

from collections import Counter
from typing import Any


def choice_metrics(trace: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> dict[str, float]:
    """Measure how close selected Destroy choices were to the local oracle.

    Rank 1 means the selected candidate had the best downstream score.
    Normalized regret is regret divided by the observed score range for that
    iteration, so 0 is best and 1 is worst among the available candidates.
    """
    ranks: list[int] = []
    regrets: list[float] = []
    normalized: list[float] = []
    top1 = 0

    for step in trace:
        scores = [
            float(score) for score in step.get("destroy_scores", {}).values()
            if score != float("inf")
        ]
        selected = step.get("selected_destroy")
        selected_score = step.get("selected_destroy_score")
        if selected is None or selected_score == float("inf") or not scores:
            continue
        ordered = sorted(scores)
        rank = 1 + sum(score < float(selected_score) for score in ordered)
        ranks.append(rank)
        if rank == 1:
            top1 += 1
        best = min(ordered)
        worst = max(ordered)
        regret = float(selected_score) - best
        regrets.append(regret)
        normalized.append(regret / (worst - best) if worst > best else 0.0)

    n = len(ranks)
    return {
        "decisions": float(n),
        "top1_rate": top1 / n if n else 0.0,
        "mean_rank": sum(ranks) / n if n else 0.0,
        "mean_regret": sum(regrets) / n if n else 0.0,
        "mean_normalized_regret": sum(normalized) / n if n else 0.0,
    }


def summarize_choice_metrics(documents: list[dict[str, Any]]) -> dict[str, Any]:
    per_run = []
    for document in documents:
        metrics = choice_metrics(document.get("trace", []))
        row: dict[str, Any] = {
            "mode": document.get("mode"),
            "seed": document.get("seed"),
            **metrics,
        }
        # Live-JEV telemetry travels with the run so reports can aggregate
        # calls, fallbacks and cost. Offline documents have no such block.
        if "jev_stats" in document:
            row["jev_stats"] = document["jev_stats"]
        per_run.append(row)

    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in per_run:
        grouped.setdefault(str(row["mode"]), []).append(row)

    summary = {}
    for mode, rows in grouped.items():
        summary[mode] = {
            "runs": len(rows),
            "top1_rate": sum(r["top1_rate"] for r in rows) / len(rows),
            "mean_rank": sum(r["mean_rank"] for r in rows) / len(rows),
            "mean_regret": sum(r["mean_regret"] for r in rows) / len(rows),
            "mean_normalized_regret": (
                sum(r["mean_normalized_regret"] for r in rows) / len(rows)
            ),
        }
    return {"per_run": per_run, "summary": summary}
