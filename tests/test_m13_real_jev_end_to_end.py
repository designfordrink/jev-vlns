from experiments.run_m13_real_jev_end_to_end import render_markdown, summarize


def test_m13_summary_uses_paired_deltas():
    rows = [
        {"seed": 1, "random_moves": 20, "real_jev_moves": 18, "fallbacks": 0, "jev_calls": 5, "cost_usd": 0.01},
        {"seed": 2, "random_moves": 17, "real_jev_moves": 19, "fallbacks": 1, "jev_calls": 5, "cost_usd": 0.02},
        {"seed": 3, "random_moves": 18, "real_jev_moves": 18, "fallbacks": 2, "jev_calls": 5, "cost_usd": 0.03},
    ]

    summary = summarize(rows)

    assert summary["mean_delta_moves"] == 0
    assert summary["median_delta_moves"] == 0
    assert summary["real_jev_wins"] == 1
    assert summary["ties"] == 1
    assert summary["real_jev_win_rate"] == 1 / 3
    assert summary["total_calls"] == 15
    assert summary["total_cost_usd"] == 0.06


def test_m13_report_contains_fallbacks_and_paired_outcome():
    rows = [
        {"seed": 1, "random_moves": 20, "real_jev_moves": 18, "fallbacks": 2, "jev_calls": 5, "cost_usd": 0.01},
    ]
    summary = summarize(rows)

    report = render_markdown(rows, summary, seeds=[1], iterations=50)

    assert "Delta (JEV-Random)" in report
    assert "Fallbacks" in report
    assert "Total API cost" in report
    assert "Negative delta means real JEV used fewer final moves" in report


def test_m13_summary_reports_full_live_telemetry():
    """M19 requires feasibility, latency, tokens and call outcome accounting."""
    rows = [
        {
            "seed": 1, "random_moves": 20, "real_jev_moves": 18,
            "random_feasible": True, "real_jev_feasible": True,
            "fallbacks": 0, "jev_calls": 5, "successes": 5,
            "average_latency_ms": 10.0, "input_tokens": 100,
            "output_tokens": 20, "cost_usd": 0.01,
        },
        {
            "seed": 2, "random_moves": 17, "real_jev_moves": 19,
            "random_feasible": True, "real_jev_feasible": False,
            "fallbacks": 1, "jev_calls": 5, "successes": 4,
            "average_latency_ms": 20.0, "input_tokens": 200,
            "output_tokens": 40, "cost_usd": 0.02,
        },
    ]

    summary = summarize(rows)

    assert summary["real_jev_wins"] == 1
    assert summary["ties"] == 0
    assert summary["losses"] == 1
    assert summary["min_delta_moves"] == -2
    assert summary["max_delta_moves"] == 2
    assert summary["total_successes"] == 9
    assert summary["total_fallbacks"] == 1
    assert summary["all_feasible"] is False
    assert summary["mean_latency_ms"] == 15.0
    assert summary["total_input_tokens"] == 300
    assert summary["total_output_tokens"] == 60

    report = render_markdown(rows, summary, seeds=[1, 2], iterations=50)
    assert "All runs feasible" in report
    assert "Mean latency" in report
    assert "Tokens in/out" in report
    assert "## Paired deltas" in report
    assert "| Real JEV vs Random (K=2) | 1 | 0 | 1 | +0.000 | +0.000 |" in report
