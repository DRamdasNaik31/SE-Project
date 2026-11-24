"""Transparent, deterministic SDLC decision rubric."""

from typing import Any

PROFILES = {
    "Agile": {"stability": 0.35, "risk": 0.55, "feedback": 1.0, "change": 1.0, "delivery": 0.9},
    "Waterfall": {"stability": 1.0, "risk": 0.65, "feedback": 0.25, "change": 0.1, "delivery": 0.25},
    "V-Model": {"stability": 0.9, "risk": 1.0, "feedback": 0.35, "change": 0.15, "delivery": 0.35},
    "Spiral": {"stability": 0.45, "risk": 1.0, "feedback": 0.7, "change": 0.7, "delivery": 0.45},
    "Iterative": {"stability": 0.55, "risk": 0.65, "feedback": 0.8, "change": 0.8, "delivery": 0.65},
    "RAD": {"stability": 0.3, "risk": 0.25, "feedback": 0.9, "change": 0.85, "delivery": 1.0},
    "Prototype": {"stability": 0.2, "risk": 0.3, "feedback": 1.0, "change": 0.9, "delivery": 0.8},
}


def score(requirements: list[dict[str, Any]], constraints: dict[str, str] | None = None) -> dict[str, Any]:
    constraints = constraints or {}
    risk = sum(
        1 for item in requirements
        if str(item.get("type", "")).lower() in {"security", "regulatory", "privacy"}
    ) / max(1, len(requirements))
    dimensions = {
        "stability": 1.0 if constraints.get("stability") == "stable" else 0.35 if constraints.get("stability") == "changing" else 0.6,
        "risk": max(0.35, risk),
        "feedback": 1.0 if constraints.get("stakeholder_feedback") == "high" else 0.3 if constraints.get("stakeholder_feedback") == "low" else 0.6,
        "change": 1.0 if constraints.get("stability") == "changing" else 0.3 if constraints.get("stability") == "stable" else 0.6,
        "delivery": 1.0 if constraints.get("delivery_pressure") == "high" else 0.3 if constraints.get("delivery_pressure") == "low" else 0.6,
    }
    weights = {"stability": 0.2, "risk": 0.25, "feedback": 0.2, "change": 0.2, "delivery": 0.15}
    raw = {
        model: sum(weights[key] * (profile[key] if dimensions[key] >= 0.5 else 1 - profile[key]) for key in weights)
        for model, profile in PROFILES.items()
    }
    total = sum(raw.values()) or 1
    scores = [{"model": model, "score": round(value / total * 100, 2), "raw": round(value, 4)}
              for model, value in raw.items()]
    scores.sort(key=lambda item: item["score"], reverse=True)
    scores[-1]["score"] = round(100.0 - sum(item["score"] for item in scores[:-1]), 2)
    return {
        "winner": scores[0]["model"],
        "approval_status": "pending_human_review",
        "scores": scores,
        "factors": dimensions,
        "explanation": f"{scores[0]['model']} ranks highest under the supplied factors; scores are normalized from the documented rubric.",
    }
