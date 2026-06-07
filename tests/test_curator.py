from eval_sample_curator.curator import curate_samples
from eval_sample_curator.models import EvalSample, Rules


def test_selection_strategy_prioritizes_required_reasons():
    samples = [
        EvalSample(id="fail", score=0.2, passed=False, latency_ms=100, cost_usd=0.01),
        EvalSample(id="band", score=0.6, passed=True, latency_ms=100, cost_usd=0.01),
        EvalSample(id="slow", score=0.95, passed=True, latency_ms=5000, cost_usd=0.01),
        EvalSample(id="cost", score=0.95, passed=True, latency_ms=100, cost_usd=1.0),
        EvalSample(id="same", score=0.2, passed=False, model="a", latency_ms=100, cost_usd=0.01),
        EvalSample(id="same", score=0.9, passed=True, model="b", latency_ms=100, cost_usd=0.01),
        EvalSample(id="reg", score=0.9, passed=True, latency_ms=100, cost_usd=0.01, tags=["regression"]),
    ]
    rules = Rules(latency_outlier_z=1.0, cost_outlier_z=1.0)

    selected = curate_samples(samples, rules, limit=10)
    reasons_by_id = {item.sample.id: set(item.reasons) for item in selected}

    assert "failure" in reasons_by_id["fail"]
    assert "score_band" in reasons_by_id["band"]
    assert "latency_outlier" in reasons_by_id["slow"]
    assert "cost_outlier" in reasons_by_id["cost"]
    assert "model_disagreement" in reasons_by_id["same"]
    assert "regression" in reasons_by_id["reg"]


def test_tag_quotas_move_quoted_tags_earlier():
    samples = [
        EvalSample(id="a", score=0.6, passed=True, tags=["general"]),
        EvalSample(id="b", score=0.6, passed=True, tags=["rag"]),
        EvalSample(id="c", score=0.6, passed=True, tags=["rag"]),
    ]
    rules = Rules(tag_quotas={"rag": 1})

    selected = curate_samples(samples, rules, limit=3)

    assert selected[0].sample.id in {"b", "c"}
