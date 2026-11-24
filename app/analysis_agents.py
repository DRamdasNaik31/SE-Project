"""Deterministic specialist agents for the full requirements-engineering flow.

These agents provide explainable checks and structured handoffs. Regulatory
interpretation is intentionally represented as a review task, never as legal
advice.
"""

import re
from typing import Any


REQUIREMENT_TYPES = {
    "security": ("security", "authentication", "authoriz", "encryption", "threat"),
    "privacy": ("privacy", "personal data", "consent", "retention", "kyc"),
    "regulatory": ("rbi", "regulatory", "compliance", "statutory", "audit"),
    "performance": ("performance", "response time", "throughput", "volume"),
    "availability": ("availability", "recovery", "continuity", "uptime", "backup"),
    "integration": ("api", "interface", "integration", "legacy", "external"),
    "data-management": ("data", "record", "database", "history", "report"),
}

AGENT_REGISTRY = {
    "orchestrator": "routes requests and controls handoffs",
    "interaction": "collects stakeholder inputs and follow-up questions",
    "retrieval": "retrieves allowlisted evidence with provenance",
    "requirements_engineer": "converts evidence into structured requirements",
    "classification": "assigns multi-label requirement categories",
    "quality": "detects ambiguity, incompleteness, duplicates, and testability issues",
    "compliance": "maps requirements to reviewable controls",
    "security": "masks sensitive data and detects prompt injection",
    "risk": "creates risk entries and mitigations",
    "traceability": "links requirements to evidence and artifacts",
    "sdlc_factors": "derives SDLC decision factors",
    "sdlc_decision": "scores and explains candidate SDLC models",
    "governance": "enforces approval gates and auditability",
}


def classify(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for requirement in requirements:
        text = str(requirement.get("statement", "")).lower()
        labels = ["functional"]
        for label, terms in REQUIREMENT_TYPES.items():
            if any(term in text for term in terms):
                labels.append(label)
        requirement["categories"] = sorted(set(labels))
    return requirements


def quality_check(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    seen: set[str] = set()
    for requirement in requirements:
        statement = str(requirement.get("statement", "")).strip()
        normalized = re.sub(r"\W+", " ", statement.lower()).strip()
        issues = []
        if len(statement) < 25:
            issues.append("incomplete_or_too_short")
        if not statement.lower().startswith("the system shall"):
            issues.append("not_testable_requirement_form")
        if normalized in seen:
            issues.append("duplicate")
        seen.add(normalized)
        if not requirement.get("evidence"):
            issues.append("missing_source_evidence")
        findings.append({"requirement_id": requirement.get("id"), "issues": issues, "status": "needs_clarification" if issues else "pass"})
    return findings


def compliance_map(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    mappings = []
    for requirement in requirements:
        categories = set(requirement.get("categories", []))
        controls = []
        if "security" in categories:
            controls.append("access-control-and-authentication-review")
        if "privacy" in categories:
            controls.append("data-protection-and-retention-review")
        if "regulatory" in categories:
            controls.append("compliance-officer-interpretation-required")
        if "audit" in str(requirement.get("statement", "")).lower():
            controls.append("audit-evidence-and-reporting")
        mappings.append({
            "requirement_id": requirement.get("id"),
            "jurisdiction": "India (to be confirmed by compliance)",
            "controls": controls,
            "evidence": requirement.get("evidence", []),
            "approval_status": "pending_compliance_review",
        })
    return mappings


def risk_register(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    risks = []
    for requirement in requirements:
        categories = set(requirement.get("categories", []))
        level = "high" if categories & {"security", "privacy", "regulatory"} else "medium"
        risks.append({
            "requirement_id": requirement.get("id"),
            "risk_level": level,
            "risk": "Incorrect or incomplete implementation of this requirement",
            "mitigation": "Human review, traceable acceptance criteria, and validation testing",
            "owner": "security/compliance/project team" if level == "high" else "project team",
        })
    return risks


def sdlc_factors(requirements: list[dict[str, Any]], constraints: dict[str, str] | None = None) -> dict[str, Any]:
    constraints = constraints or {}
    categories = {category for item in requirements for category in item.get("categories", [])}
    return {
        "requirement_stability": constraints.get("stability", "unknown"),
        "regulatory_criticality": "high" if "regulatory" in categories else "unknown",
        "security_risk": "high" if "security" in categories else "unknown",
        "project_complexity": "high" if len(requirements) >= 10 else "medium",
        "change_frequency": "high" if constraints.get("stability") == "changing" else "unknown",
        "stakeholder_feedback": constraints.get("stakeholder_feedback", "unknown"),
    }


def artifact_bundle(requirements: list[dict[str, Any]], sdlc: dict[str, Any] | None = None) -> dict[str, Any]:
    classified = classify(requirements)
    return {
        "srs": {"title": "Finance Requirements Specification", "requirements": classified},
        "quality_findings": quality_check(classified),
        "compliance_control_matrix": compliance_map(classified),
        "risk_register": risk_register(classified),
        "traceability": [
            {"requirement_id": item.get("id"), "evidence": item.get("evidence", [])}
            for item in classified
        ],
        "sdlc_factors": sdlc_factors(classified),
        "sdlc": sdlc,
        "open_issues": [
            finding for finding in quality_check(classified) if finding["status"] != "pass"
        ],
    }
