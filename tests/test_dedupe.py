from eval_sample_curator.dedupe import jaccard, suppress_near_duplicates, tokens
from eval_sample_curator.models import CuratedSample, EvalSample


def test_jaccard_token_similarity():
    assert tokens("Hello, hello WORLD!") == {"hello", "world"}
    assert jaccard({"a", "b"}, {"b", "c"}) == 1 / 3


def test_suppress_near_duplicates_keeps_first_high_priority_candidate():
    candidates = [
        CuratedSample(
            sample=EvalSample(id="1", prompt="refund policy for enterprise account"),
            reasons=["failure"],
            evidence={},
            priority=100,
        ),
        CuratedSample(
            sample=EvalSample(id="2", prompt="refund policy for enterprise account"),
            reasons=["failure"],
            evidence={},
            priority=90,
        ),
    ]

    selected = suppress_near_duplicates(candidates, threshold=0.8)

    assert [item.sample.id for item in selected] == ["1"]
