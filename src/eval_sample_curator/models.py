from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class FieldMapping:
    id: str = "id"
    prompt: str = "prompt"
    output: str = "output"
    expected: str = "expected"
    score: str = "score"
    passed: str = "passed"
    model: str = "model"
    latency_ms: str = "latency_ms"
    cost_usd: str = "cost_usd"
    tags: str = "tags"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FieldMapping":
        valid = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{k: str(v) for k, v in data.items() if k in valid})


@dataclass
class Rules:
    fields: FieldMapping = field(default_factory=FieldMapping)
    score_band: Optional[List[float]] = field(default_factory=lambda: [0.45, 0.75])
    tag_quotas: Dict[str, int] = field(default_factory=dict)
    near_duplicate_threshold: float = 0.82
    latency_outlier_z: float = 1.5
    cost_outlier_z: float = 1.5
    redact_pii: bool = True
    include_passed_boundary: bool = True
    failure_weight: float = 100.0
    disagreement_weight: float = 80.0
    outlier_weight: float = 60.0
    score_band_weight: float = 40.0
    regression_weight: float = 90.0

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Rules":
        fields = FieldMapping.from_dict(data.get("fields", {}))
        values = dict(data)
        values["fields"] = fields
        valid = {field.name for field in cls.__dataclass_fields__.values()}
        return cls(**{k: v for k, v in values.items() if k in valid})


@dataclass
class EvalSample:
    id: str
    prompt: str = ""
    output: str = ""
    expected: str = ""
    score: Optional[float] = None
    passed: Optional[bool] = None
    model: str = ""
    latency_ms: Optional[float] = None
    cost_usd: Optional[float] = None
    tags: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    @property
    def review_text(self) -> str:
        return " ".join([self.prompt, self.output, self.expected]).strip()


@dataclass
class CuratedSample:
    sample: EvalSample
    reasons: List[str]
    evidence: Dict[str, Any]
    priority: float

