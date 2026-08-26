"""PII/secrets redaction at gateway and logging boundaries."""

from __future__ import annotations

import re
from typing import Any

EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
API_KEY_PATTERN = re.compile(r"\b(sk-[A-Za-z0-9]{20,}|AIza[A-Za-z0-9_-]{35})\b")
BEARER_PATTERN = re.compile(r"Bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE)


def redact_text(text: str) -> str:
    text = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", text)
    text = API_KEY_PATTERN.sub("[REDACTED_KEY]", text)
    text = BEARER_PATTERN.sub("Bearer [REDACTED]", text)
    return text


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = redact_text(value)
        elif isinstance(value, dict):
            result[key] = redact_dict(value)
        else:
            result[key] = value
    return result
