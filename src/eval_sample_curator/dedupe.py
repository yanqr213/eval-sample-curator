from __future__ import annotations

import re
from typing import Iterable, List, Set

from .models import CuratedSample


TOKEN_RE = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


def tokens(text: str) -> Set[str]:
    return {match.group(0).lower() for match in TOKEN_RE.finditer(text or "")}


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    if not left_set or not right_set:
        return 0.0
    return len(left_set & right_set) / len(left_set | right_set)


def suppress_near_duplicates(
    candidates: Iterable[CuratedSample], threshold: float
) -> List[CuratedSample]:
    selected: List[CuratedSample] = []
    selected_tokens: List[Set[str]] = []
    for candidate in candidates:
        candidate_tokens = tokens(candidate.sample.review_text)
        if not candidate_tokens:
            selected.append(candidate)
            continue
        if any(jaccard(candidate_tokens, existing) >= threshold for existing in selected_tokens):
            continue
        selected.append(candidate)
        selected_tokens.append(candidate_tokens)
    return selected
