"""Replay and visualization helpers for one guided VLNS run."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def replay_document(result: Any, *, mode: str, seed: int, iterations: int) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "mode": mode,
        "seed": seed,
        "iterations": iterations,
        "final": {
            "moves": int(result.evaluation.metrics["moves"]),
            "feasible": bool(result.evaluation.feasible),
            "projected_objective": result.best_projected_objective,
        },
        "trace": list(result.trace),
    }


def write_replay_json(document: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_replay_html(document: dict[str, Any]) -> str:
    def fmt(value: Any) -> str:
        if value == float("inf"):
            return "∞"
        if isinstance(value, float):
            return f"{value:.2f}"
        return str(value)

    rows = []
    for step in document["trace"]:
        scores = step["destroy_scores"]
        candidates = []
        for candidate in step["destroy_candidates"]:
            cid = candidate["id"]
            marker = " ★" if cid == step["selected_destroy"] else ""
            candidates.append(
                f"<li><b>{html.escape(cid)}</b>{marker} — score {html.escape(fmt(scores.get(cid)))}</li>"
            )
        repairs = ", ".join(
            html.escape(item["id"]) for item in step["selected_repairs"]
        ) or "none"
        status = "ACCEPTED" if step["accepted"] else "REJECTED"
        rows.append(
            f"""
            <section class="step">
              <h2>Iteration {step['iteration']} <span class="status">{status}</span></h2>
              <p><b>Before:</b> {html.escape(json.dumps(step['before']['stacks']))}</p>
              <p><b>Destroy:</b> {html.escape(step['selected_destroy'])}
                 — selected score {html.escape(fmt(step['selected_destroy_score']))},
                 best score {html.escape(fmt(step['best_destroy_score']))},
                 regret {html.escape(fmt(step['selected_destroy_score'] - step['best_destroy_score']))}</p>
              <details><summary>Destroy candidates ({len(step['destroy_candidates'])})</summary>
                <ul>{''.join(candidates)}</ul>
              </details>
              <p><b>Removed:</b> {html.escape(', '.join(step['removed']))}</p>
              <p><b>Repair choices:</b> {repairs}
                 — best repair score {html.escape(fmt(step['best_repair_score']))}</p>
              <p><b>Candidate objective:</b> {html.escape(fmt(step['candidate_projected_objective']))}
                 → <b>current:</b> {html.escape(fmt(step['score_after']))}</p>
            </section>
            """
        )

    final = document["final"]
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>JEV-VLNS Replay</title>
<style>
body{{font:15px system-ui,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;line-height:1.5}}
.step{{border:1px solid #ddd;border-radius:10px;padding:16px;margin:16px 0}}
.status{{font-size:.75em;border:1px solid #999;border-radius:999px;padding:3px 8px}}
code,pre{{background:#f5f5f5;padding:2px 5px;border-radius:4px}}
</style>
</head>
<body>
<h1>JEV + VLNS Replay</h1>
<p><b>Mode:</b> {html.escape(document['mode'])} ·
<b>Seed:</b> {document['seed']} · <b>Iterations:</b> {document['iterations']}</p>
<p><b>Final moves:</b> {final['moves']} · <b>Feasible:</b> {final['feasible']} ·
<b>Projected objective:</b> {html.escape(fmt(final['projected_objective']))}</p>
{''.join(rows)}
</body>
</html>
"""


def write_replay_html(document: dict[str, Any], path: str | Path) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_replay_html(document), encoding="utf-8")
