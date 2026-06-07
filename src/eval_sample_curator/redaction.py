from __future__ import annotations

import re


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CREDIT_CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")
IPV4_RE = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")


def redact_text(text: str) -> str:
    if not text:
        return ""
    redacted = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    redacted = SSN_RE.sub("[REDACTED_SSN]", redacted)
    redacted = CREDIT_CARD_RE.sub(_redact_card_like, redacted)
    redacted = PHONE_RE.sub("[REDACTED_PHONE]", redacted)
    redacted = IPV4_RE.sub("[REDACTED_IP]", redacted)
    return redacted


def _redact_card_like(match: re.Match[str]) -> str:
    digits = re.sub(r"\D", "", match.group(0))
    if 13 <= len(digits) <= 16:
        return "[REDACTED_CARD]"
    return match.group(0)

