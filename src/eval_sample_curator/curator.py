from __future__ import annotations

import math
from collections import Counter, defaultdict
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional, Tuple

from .dedupe import suppress_near_duplicates
from .models import CuratedSample, EvalSample, Rules


def curate_samples(samples: List[EvalSample], rules: Rules, limit: int) -> List[CuratedSample]:
    if limit <= 0:
        return []
    model_groups = _group_for_disagreement(samples)
    latency_stats = _stats(sample.latency_ms for sample in samples)
    cost_stats = _stats(sample.cost_usd for sample in samples)
    candidates = [
        _score_sample(sample, rules, model_groups, latency_stats, cost_stats)
        for sample in samples
    ]
    candidates = [candidate for candidate in candidates if candidate.reasons]
    candidates.sort(key=lambda item: (-item.priority, item.sample.id))
    candidates = _apply_tag_quotas(candidates, rules.tag_quotas)
    return suppress_near_duplicates(candidates, rules.near_duplicate_threshold)[:limit]


def _score_sample(
    sample: EvalSample,
    rules: Rules,
    model_groups: Dict[str, List[EvalSample]],
    latency_stats: Tuple[float, float],
    cost_stats: Tuple[float, float],
) -> CuratedSample:
    reasons: List[str] = []
    evidence = {}
    priority = 0.0

    if sample.passed is False:
        reasons.append("failure")
        evidence["passed"] = False
        priority += rules.failure_weight

    if _is_regression(sample):
        reasons.append("regression")
        evidence["regression"] = True
        priority += rules.regression_weight

    if _in_score_band(sample.score, rules.score_band, rules.include_passed_boundary):
        reasons.append("score_band")
        evidence["score"] = sample.score
        priority += rules.score_band_weight + _score_band_bonus(sample.score, rules.score_band)

    if _is_outlier(sample.latency_ms, latency_stats, rules.latency_outlier_z):
        reasons.append("latency_outlier")
        evidence["latency_ms"] = sample.latency_ms
        priority += rules.outlier_weight + _z_bonus(sample.latency_ms, latency_stats)

    if _is_outlier(sample.cost_usd, cost_stats, rules.cost_outlier_z):
        reasons.append("cost_outlier")
        evidence["cost_usd"] = sample.cost_usd
        priority += rules.outlier_weight + _z_bonus(sample.cost_usd, cost_stats)

    group_key = _disagreement_key(sample)
    group = model_groups.get(group_key, [])
    if len({item.passed for item in group if item.passed is not None}) > 1:
        reasons.append("model_disagreement")
        evidence["models"] = sorted({item.model for item in group if item.model})
        evidence["group_key"] = group_key
        priority += rules.disagreement_weight

    # Slightly prefer tagged samples when applying quotas later.
    priority += min(len(sample.tags), 3) * 0.5
    return CuratedSample(sample=sample, reasons=reasons, evidence=evidence, priority=priority)


def _apply_tag_quotas(
    candidates: List[CuratedSample], quotas: Dict[str, int]
) -> List[CuratedSample]:
    if not quotas:
        return candidates
    selected: List[CuratedSample] = []
    counts: Counter[str] = Counter()
    deferred: List[CuratedSample] = []
    for candidate in candidates:
        quota_tags = [tag for tag in candidate.sample.tags if tag in quotas]
        if not quota_tags:
            deferred.append(candidate)
            continue
        if all(counts[tag] < quotas[tag] for tag in quota_tags):
            selected.append(candidate)
            for tag in quota_tags:
                counts[tag] += 1
        else:
            deferred.append(candidate)
    return selected + deferred


def _group_for_disagreement(samples: Iterable[EvalSample]) -> Dict[str, List[EvalSample]]:
    groups: Dict[str, List[EvalSample]] = defaultdict(list)
    for sample in samples:
        key = _disagreement_key(sample)
        if sample.model and key:
            groups[key].append(sample)
    return groups


def _disagreement_key(sample: EvalSample) -> str:
    return sample.id or sample.prompt.strip().lower()


def _stats(values: Iterable[Optional[float]]) -> Tuple[float, float]:
    present = [value for value in values if value is not None]
    if not present:
        return (0.0, 0.0)
    if len(present) == 1:
        return (present[0], 0.0)
    return (mean(present), pstdev(present))


def _is_outlier(value: Optional[float], stats: Tuple[float, float], threshold: float) -> bool:
    if value is None:
        return False
    avg, std = stats
    if std <= 0:
        return False
    return value >= avg + threshold * std


def _z_bonus(value: Optional[float], stats: Tuple[float, float]) -> float:
    if value is None:
        return 0.0
    avg, std = stats
    if std <= 0:
        return 0.0
    return min(20.0, max(0.0, (value - avg) / std))


def _in_score_band(
    score: Optional[float], band: Optional[List[float]], include_passed_boundary: bool
) -> bool:
    if score is None or not band or len(band) != 2:
        return False
    lower, upper = sorted([float(band[0]), float(band[1])])
    if include_passed_boundary:
        return lower <= score <= upper
    return score < upper


def _score_band_bonus(score: Optional[float], band: Optional[List[float]]) -> float:
    if score is None or not band or len(band) != 2:
        return 0.0
    lower, upper = sorted([float(band[0]), float(band[1])])
    midpoint = (lower + upper) / 2
    width = max(upper - lower, 0.001)
    return max(0.0, 10.0 * (1.0 - math.fabs(score - midpoint) / width))


def _is_regression(sample: EvalSample) -> bool:
    tags = {tag.lower() for tag in sample.tags}
    if "regression" in tags or "regressed" in tags:
        return True
    raw = {str(key).lower(): value for key, value in sample.raw.items()}
    for key in ("regression", "regressed", "is_regression"):
        value = raw.get(key)
        if isinstance(value, bool):
            return value
        if value is not None and str(value).strip().lower() in {"true", "1", "yes", "y"}:
            return True
    return False
