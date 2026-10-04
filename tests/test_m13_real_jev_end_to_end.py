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
