from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .models import EvalSample, FieldMapping


class LoadError(ValueError):
    """Raised when an input file cannot be parsed into eval samples."""


def load_samples(path: str, fields: FieldMapping) -> List[EvalSample]:
    input_path = Path(path)
    if not input_path.exists():
        raise LoadError(f"input file does not exist: {input_path}")
    suffix = input_path.suffix.lower()
    if suffix == ".jsonl":
        rows = _read_jsonl(input_path)
    elif suffix == ".csv":
        rows = _read_csv(input_path)
    else:
        raise LoadError("input must be a .jsonl or .csv file")
    samples = [_row_to_sample(row, fields, index) for index, row in enumerate(rows, start=1)]
    if not samples:
        raise LoadError("input file contains no samples")
    return samples


def _read_jsonl(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                row = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise LoadError(f"invalid JSONL at line {line_no}: {exc}") from exc
            if not isinstance(row, dict):
                raise LoadError(f"JSONL line {line_no} is not an object")
            yield row


def _read_csv(path: Path) -> Iterable[Dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise LoadError("CSV input has no header row")
        yield from reader


def _row_to_sample(row: Dict[str, Any], fields: FieldMapping, index: int) -> EvalSample:
    sample_id = _as_text(row.get(fields.id)) or f"row-{index}"
    return EvalSample(
        id=sample_id,
        prompt=_as_text(row.get(fields.prompt)),
        output=_as_text(row.get(fields.output)),
        expected=_as_text(row.get(fields.expected)),
        score=_as_float(row.get(fields.score)),
        passed=_as_bool(row.get(fields.passed)),
        model=_as_text(row.get(fields.model)),
        latency_ms=_as_float(row.get(fields.latency_ms)),
        cost_usd=_as_float(row.get(fields.cost_usd)),
        tags=_as_tags(row.get(fields.tags)),
        raw=dict(row),
    )


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _as_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    text = str(value).strip().lower()
    if text in {"true", "t", "yes", "y", "1", "pass", "passed"}:
        return True
    if text in {"false", "f", "no", "n", "0", "fail", "failed"}:
        return False
    return None


def _as_tags(value: Any) -> List[str]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(item).strip() for item in parsed if str(item).strip()]
    return [part.strip() for part in text.replace(";", ",").split(",") if part.strip()]
