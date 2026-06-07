from __future__ import annotations

import csv
import json
from io import StringIO
from typing import Iterable, List

from .models import CuratedSample
from .redaction import redact_text


def render_report(items: List[CuratedSample], output_format: str, redact: bool = True) -> str:
    if output_format == "markdown":
        return _render_markdown(items, redact)
    if output_format == "json":
        return json.dumps([_as_dict(item, redact) for item in items], ensure_ascii=False, indent=2)
    if output_format == "csv":
        return _render_csv(items, redact)
    raise ValueError("format must be markdown, json, or csv")


def _render_markdown(items: Iterable[CuratedSample], redact: bool) -> str:
    lines = [
        "# Eval Review Packet",
        "",
        "Curated samples selected for human review.",
        "",
    ]
    for index, item in enumerate(items, start=1):
        sample = item.sample
        lines.extend(
            [
                f"## {index}. {sample.id}",
                "",
                f"- Priority: {item.priority:.2f}",
                f"- Reasons: {', '.join(item.reasons)}",
                f"- Model: {sample.model or '-'}",
                f"- Score: {_value(sample.score)}",
                f"- Passed: {_value(sample.passed)}",
                f"- Latency ms: {_value(sample.latency_ms)}",
                f"- Cost usd: {_value(sample.cost_usd)}",
                f"- Tags: {', '.join(sample.tags) if sample.tags else '-'}",
                "",
                "### Prompt",
                "",
                _maybe_redact(sample.prompt, redact) or "-",
                "",
                "### Output",
                "",
                _maybe_redact(sample.output, redact) or "-",
                "",
                "### Expected",
                "",
                _maybe_redact(sample.expected, redact) or "-",
                "",
                "### Evidence",
                "",
                "```json",
                json.dumps(item.evidence, ensure_ascii=False, indent=2),
                "```",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def _render_csv(items: Iterable[CuratedSample], redact: bool) -> str:
    buffer = StringIO()
    fieldnames = [
        "id",
        "priority",
        "reasons",
        "model",
        "score",
        "passed",
        "latency_ms",
        "cost_usd",
        "tags",
        "prompt",
        "output",
        "expected",
        "evidence",
    ]
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for item in items:
        sample = item.sample
        writer.writerow(
            {
                "id": sample.id,
                "priority": f"{item.priority:.2f}",
                "reasons": ",".join(item.reasons),
                "model": sample.model,
                "score": _value(sample.score),
                "passed": _value(sample.passed),
                "latency_ms": _value(sample.latency_ms),
                "cost_usd": _value(sample.cost_usd),
                "tags": ",".join(sample.tags),
                "prompt": _maybe_redact(sample.prompt, redact),
                "output": _maybe_redact(sample.output, redact),
                "expected": _maybe_redact(sample.expected, redact),
                "evidence": json.dumps(item.evidence, ensure_ascii=False, sort_keys=True),
            }
        )
    return buffer.getvalue()


def _as_dict(item: CuratedSample, redact: bool) -> dict:
    sample = item.sample
    return {
        "id": sample.id,
        "priority": round(item.priority, 2),
        "reasons": item.reasons,
        "evidence": item.evidence,
        "sample": {
            "prompt": _maybe_redact(sample.prompt, redact),
            "output": _maybe_redact(sample.output, redact),
            "expected": _maybe_redact(sample.expected, redact),
            "score": sample.score,
            "passed": sample.passed,
            "model": sample.model,
            "latency_ms": sample.latency_ms,
            "cost_usd": sample.cost_usd,
            "tags": sample.tags,
        },
    }


def _maybe_redact(value: str, redact: bool) -> str:
    return redact_text(value) if redact else value


def _value(value: object) -> str:
    if value is None:
        return "-"
    return str(value)

