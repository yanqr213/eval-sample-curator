import json

from eval_sample_curator.loader import load_samples
from eval_sample_curator.models import FieldMapping


def test_load_jsonl_with_defaults(tmp_path):
    path = tmp_path / "results.jsonl"
    path.write_text(
        json.dumps(
            {
                "id": "a",
                "prompt": "p",
                "output": "o",
                "expected": "e",
                "score": "0.5",
                "passed": "false",
                "model": "m",
                "latency_ms": "123",
                "cost_usd": "0.02",
                "tags": '["rag", "regression"]',
            }
        )
        + "\n",
        encoding="utf-8",
    )

    samples = load_samples(str(path), FieldMapping())

    assert samples[0].id == "a"
    assert samples[0].score == 0.5
    assert samples[0].passed is False
    assert samples[0].tags == ["rag", "regression"]


def test_load_csv_with_custom_field_mapping(tmp_path):
    path = tmp_path / "results.csv"
    path.write_text(
        "case_id,input,actual,golden,judge_score,ok,model_name,latency,cost,labels\n"
        "1,p,o,e,0.8,true,m,99,0.01,rag;policy\n",
        encoding="utf-8",
    )
    fields = FieldMapping.from_dict(
        {
            "id": "case_id",
            "prompt": "input",
            "output": "actual",
            "expected": "golden",
            "score": "judge_score",
            "passed": "ok",
            "model": "model_name",
            "latency_ms": "latency",
            "cost_usd": "cost",
            "tags": "labels",
        }
    )

    samples = load_samples(str(path), fields)

    assert samples[0].id == "1"
    assert samples[0].prompt == "p"
    assert samples[0].passed is True
    assert samples[0].tags == ["rag", "policy"]
