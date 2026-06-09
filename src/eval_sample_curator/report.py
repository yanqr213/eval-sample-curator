from __future__ import annotations

import csv
import json
from collections import Counter
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
    if output_format == "pr-comment":
        return _render_pr_comment(items, redact)
    raise ValueError("format must be markdown, json, csv, or pr-comment")


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


def _render_pr_comment(items: Iterable[CuratedSample], redact: bool) -> str:
    selected = list(items)
    reason_counts: Counter[str] = Counter()
    tag_counts: Counter[str] = Counter()
    for item in selected:
        reason_counts.update(item.reasons)
        tag_counts.update(item.sample.tags)

    lines = [
        "## Eval Review Packet",
        "",
        f"- Selected samples: **{len(selected)}**",
        f"- Reasons: {_format_counter(reason_counts)}",
        f"- Tags: {_format_counter(tag_counts)}",
        "",
    ]
    if not selected:
        lines.extend(
            [
                "No samples matched the current curation rules.",
                "",
            ]
        )
        return "\n".join(lines)

    lines.extend(
        [
            "| # | Sample | Priority | Reasons | Score | Passed | Model | Notes |",
            "| ---: | --- | ---: | --- | ---: | --- | --- | --- |",
        ]
    )
    for index, item in enumerate(selected[:10], start=1):
        sample = item.sample
        notes = _sample_note(item, redact)
        lines.append(
            "| {index} | `{sample_id}` | {priority:.2f} | {reasons} | {score} | {passed} | {model} | {notes} |".format(
                index=index,
                sample_id=_md(sample.id),
                priority=item.priority,
                reasons=_md(", ".join(item.reasons)),
                score=_md(_value(sample.score)),
                passed=_md(_value(sample.passed)),
                model=_md(sample.model or "-"),
                notes=_md(notes),
            )
        )
    if len(selected) > 10:
        lines.append("")
        lines.append(f"_Showing top 10 of {len(selected)} selected samples. See the full packet artifact for details._")
    lines.append("")
    return "\n".join(lines)


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


def _format_counter(counter: Counter[str]) -> str:
    if not counter:
        return "-"
    return ", ".join(f"`{_md(name)}` {count}" for name, count in sorted(counter.items()))


def _sample_note(item: CuratedSample, redact: bool) -> str:
    sample = item.sample
    pieces = []
    if "latency_ms" in item.evidence:
        pieces.append(f"latency {item.evidence['latency_ms']}ms")
    if "cost_usd" in item.evidence:
        pieces.append(f"cost ${item.evidence['cost_usd']}")
    if "models" in item.evidence:
        pieces.append("models " + ", ".join(str(model) for model in item.evidence["models"]))
    preview = _trim(_maybe_redact(sample.prompt or sample.output or sample.expected, redact), 90)
    if preview:
        pieces.append(preview)
    return "; ".join(pieces) or "-"


def _trim(value: str, limit: int) -> str:
    compact = " ".join(value.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 1].rstrip() + "…"


def _md(value: str) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")
