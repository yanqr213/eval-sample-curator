from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional

from .curator import curate_samples
from .loader import LoadError, load_samples
from .models import Rules
from .report import render_report


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        rules = load_rules(args.rules)
        samples = load_samples(args.input, rules.fields)
        curated = curate_samples(samples, rules, args.limit)
        if args.check:
            return 0 if curated else 1
        report = render_report(curated, args.format, redact=rules.redact_pii)
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
        else:
            sys.stdout.write(report)
        return 0
    except (LoadError, ValueError, OSError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"error: {exc}\n")
        return 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="curate",
        description="Curate a compact human-review packet from LLM eval results.",
    )
    parser.add_argument("input", help="JSONL or CSV eval result file")
    parser.add_argument(
        "--format",
        choices=["markdown", "json", "csv", "pr-comment"],
        default="markdown",
        help="review packet output format",
    )
    parser.add_argument("--rules", help="JSON rules file")
    parser.add_argument("--limit", type=int, default=20, help="maximum selected samples")
    parser.add_argument("--output", help="output file path")
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit 0 when at least one sample would be selected; write no output",
    )
    return parser


def load_rules(path: Optional[str]) -> Rules:
    if not path:
        return Rules()
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("rules file must contain a JSON object")
    return Rules.from_dict(data)


if __name__ == "__main__":
    raise SystemExit(main())
