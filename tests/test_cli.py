import json

from eval_sample_curator.cli import main


def test_cli_writes_output_and_returns_zero(tmp_path):
    input_path = tmp_path / "results.jsonl"
    rules_path = tmp_path / "rules.json"
    output_path = tmp_path / "packets" / "packet.md"
    input_path.write_text(
        json.dumps({"id": "x", "prompt": "p", "output": "o", "score": 0.1, "passed": False})
        + "\n",
        encoding="utf-8",
    )
    rules_path.write_text("{}", encoding="utf-8")

    code = main(
        [
            str(input_path),
            "--rules",
            str(rules_path),
            "--output",
            str(output_path),
        ]
    )

    assert code == 0
    assert "failure" in output_path.read_text(encoding="utf-8")


def test_cli_check_writes_no_output(tmp_path):
    input_path = tmp_path / "results.jsonl"
    output_path = tmp_path / "packets" / "empty.md"
    input_path.write_text(
        json.dumps({"id": "x", "score": 0.99, "passed": True}) + "\n",
        encoding="utf-8",
    )

    code = main([str(input_path), "--output", str(output_path), "--check"])

    assert code == 1
    assert not output_path.exists()


def test_cli_pr_comment_output(tmp_path):
    input_path = tmp_path / "results.jsonl"
    output_path = tmp_path / "packets" / "comment.md"
    input_path.write_text(
        json.dumps({"id": "x", "prompt": "contact alice@team.test", "score": 0.1, "passed": False})
        + "\n",
        encoding="utf-8",
    )

    code = main([str(input_path), "--format", "pr-comment", "--output", str(output_path)])

    assert code == 0
    text = output_path.read_text(encoding="utf-8")
    assert "Eval Review Packet" in text
    assert "alice@team.test" not in text


def test_cli_check_returns_one_when_no_samples_selected(tmp_path):
    input_path = tmp_path / "results.jsonl"
    input_path.write_text(
        json.dumps({"id": "x", "score": 0.99, "passed": True}) + "\n",
        encoding="utf-8",
    )

    code = main([str(input_path), "--check"])

    assert code == 1


def test_cli_invalid_input_returns_one():
    code = main(["missing.jsonl", "--check"])

    assert code == 1
