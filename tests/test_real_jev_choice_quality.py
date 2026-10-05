from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from experiments.run_real_jev_choice_quality import render_report
from jev_vlns.evaluation.choice_quality import summarize_choice_metrics


def test_m12_report_marks_fallbacks_and_live_jev():
    result = {
        "summary": {
            "real-jev-random": {
                "runs": 1,
                "top1_rate": 0.5,
                "mean_rank": 2.0,
                "mean_regret": 1.0,
                "mean_normalized_regret": 0.5,
            }
        },
        "per_run": [{
            "mode": "real-jev-random",
            "decisions": 2.0,
            "jev_stats": {"calls": 2, "fallbacks": 1, "cost_usd": 0.01},
        }],
    }
    report = render_report(result)
    assert "Live JEV Destroy selector" in report
    assert "| Mode | Runs | Decisions | Top-1 rate | Mean rank | Mean regret | Normalized regret | JEV calls | Fallbacks | Cost USD |" in report
    assert "| real-jev-random | 1 | 2 | 0.500 | 2.00 | 1.000 | 0.500 | 2 | 1 | 0.010000 |" in report


def test_m12_report_renders_real_pipeline_output():
    """render_report must accept what the live pipeline actually produces.

    The previous test hand-built a per_run row carrying jev_stats, a shape
    summarize_choice_metrics did not emit, so the real run crashed on
    KeyError: 'jev_stats' while the suite stayed green.
    """
    document = {
        "mode": "real-jev-random",
        "seed": 1,
        "trace": [
            {
                "destroy_scores": {"d1": 5.0, "d2": 3.0},
                "selected_destroy": "d1",
                "selected_destroy_score": 5.0,
            }
        ],
        "jev_stats": {
            "calls": 1,
            "successes": 1,
            "failures": 0,
            "fallbacks": 0,
            "low_confidence": 0,
            "invalid_choice": 0,
            "average_latency_ms": 12.5,
            "input_tokens": 100,
            "output_tokens": 10,
            "cost_usd": 0.0001,
        },
    }

    result = summarize_choice_metrics([document])
    report = render_report(result)

    assert "| real-jev-random | 1 | 1 | 0.000 | 2.00 | 2.000 | 1.000 | 1 | 0 | 0.000100 |" in report


def test_m12_report_tolerates_summary_without_live_telemetry():
    """Offline documents carry no jev_stats block and must still render."""
    result = summarize_choice_metrics([
        {
            "mode": "random-random",
            "seed": 1,
            "trace": [
                {
                    "destroy_scores": {"d1": 4.0, "d2": 2.0},
                    "selected_destroy": "d1",
                    "selected_destroy_score": 4.0,
                }
            ],
        }
    ])

    report = render_report(result)
    assert "| random-random | 1 | 1 | 0.000 | 2.00 | 2.000 | 1.000 | 0 | 0 | 0.000000 |" in report
