import csv
import json
from io import StringIO

from eval_sample_curator.models import CuratedSample, EvalSample
from eval_sample_curator.report import render_report


def item():
    return CuratedSample(
        sample=EvalSample(
            id="x",
            prompt="contact alice@team.test",
            output="bad",
            expected="good",
            score=0.2,
            passed=False,
            model="m",
            latency_ms=123,
            cost_usd=0.01,
            tags=["rag"],
        ),
        reasons=["failure"],
        evidence={"passed": False},
        priority=100,
    )


def test_markdown_report_redacts_and_includes_reasons():
    report = render_report([item()], "markdown", redact=True)

    assert "# Eval Review Packet" in report
    assert "failure" in report
    assert "alice@team.test" not in report
    assert "[REDACTED_EMAIL]" in report


def test_json_report_shape():
    report = render_report([item()], "json", redact=False)
    data = json.loads(report)

    assert data[0]["id"] == "x"
    assert data[0]["sample"]["prompt"] == "contact alice@team.test"


def test_csv_report_shape():
    report = render_report([item()], "csv", redact=False)
    rows = list(csv.DictReader(StringIO(report)))

    assert rows[0]["id"] == "x"
    assert rows[0]["reasons"] == "failure"
