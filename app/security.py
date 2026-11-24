"""Security helpers for handling sensitive stakeholder input and prompts."""

import re
from dataclasses import dataclass

SENSITIVE_PATTERNS = (
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[REDACTED_PAYMENT_CARD]"),
    (re.compile(r"\b\d{9,18}\b"), "[REDACTED_ACCOUNT_OR_ID]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:api[_ -]?key|secret|password|token)\s*[:=]\s*\S+", re.I), "[REDACTED_SECRET]"),
)
INJECTION_PATTERNS = (
    re.compile(r"ignore\s+(?:(?:all|any|the)\s+)?(?:previous|prior|above)\s+instructions?", re.I),
    re.compile(r"system\s+message\s*:", re.I),
    re.compile(r"reveal\s+(?:the\s+)?(?:prompt|hidden instructions?)", re.I),
)


def mask_sensitive(text: str) -> str:
    """Mask common secrets and financial identifiers before model submission."""
    for pattern, replacement in SENSITIVE_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def detect_prompt_injection(text: str) -> list[str]:
    return [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(text)]


def validate_source(source: dict[str, object], allowed_modules: set[str] | None = None) -> None:
    """Reject evidence that lacks provenance or is outside an allowlist."""
    required = ("module", "page", "source_text")
    missing = [key for key in required if not source.get(key)]
    if missing:
        raise ValueError(f"Evidence is missing provenance fields: {', '.join(missing)}")
    if allowed_modules and str(source["module"]) not in allowed_modules:
        raise ValueError(f"Evidence module is not allowlisted: {source['module']}")


@dataclass(frozen=True)
class SafetyResult:
    text: str
    injection_detected: bool
    redactions: int


def sanitize_input(text: str) -> SafetyResult:
    masked = mask_sensitive(text)
    injections = detect_prompt_injection(masked)
    return SafetyResult(masked, bool(injections), sum(masked.count(token) for _, token in SENSITIVE_PATTERNS))
