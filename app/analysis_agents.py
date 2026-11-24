"""Deterministic specialist agents for the full requirements-engineering flow.

These agents provide explainable checks and structured handoffs. Regulatory
interpretation is intentionally represented as a review task, never as legal
advice.
"""

import re
from typing import Any

try:
    from .traceability import workflow_for
except ImportError:
    from traceability import workflow_for


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


def conflict_check(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    findings = []
    for index, requirement in enumerate(requirements):
        statement = str(requirement.get("statement", "")).lower()
        for later in requirements[index + 1:]:
            later_statement = str(later.get("statement", "")).lower()
            overlap = set(re.findall(r"[a-z]{4,}", statement)) & set(re.findall(r"[a-z]{4,}", later_statement))
            if len(overlap) >= 4:
                findings.append({
                    "requirement_ids": [requirement.get("id"), later.get("id")],
                    "type": "possible_duplicate_or_conflict",
                    "status": "needs_clarification",
                    "shared_terms": sorted(overlap),
                })
    return findings


def generate_user_stories(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "requirement_id": requirement.get("id"),
        "story": f"As a banking stakeholder, I need {str(requirement.get('statement', '')).replace('The system shall ', '').lower().rstrip('.')}, so that the banking process is supported accurately.",
        "acceptance_criteria": requirement.get("acceptance_criteria", []),
    } for requirement in requirements]


def generate_use_cases(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [{
        "requirement_id": requirement.get("id"),
        "name": f"Use case for {requirement.get('id')}",
        "actor": "Authorised banking user",
        "preconditions": ["Relevant user role is authenticated.", "Required source data is available."],
        "main_flow": [requirement.get("statement", "")],
        "postconditions": ["Requirement outcome is recorded and traceable."],
        "acceptance_criteria": requirement.get("acceptance_criteria", []),
    } for requirement in requirements]


def clarification_questions(requirements: list[dict[str, Any]]) -> list[dict[str, Any]]:
    questions = []
    for requirement in requirements:
        statement = str(requirement.get("statement", "")).strip()
        if len(statement) < 25:
            questions.append({
                "requirement_id": requirement.get("id"),
                "question": "Please provide additional business context and measurable acceptance criteria.",
                "reason": "The requirement statement is incomplete.",
            })
        if not requirement.get("dependencies"):
            questions.append({
                "requirement_id": requirement.get("id"),
                "question": "Which legacy systems, interfaces, or prerequisite requirements does this requirement depend on?",
                "reason": "Dependencies are not identified.",
            })
    return questions


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
        "conflict_findings": conflict_check(classified),
        "user_stories": generate_user_stories(classified),
        "use_cases": generate_use_cases(classified),
        "assumptions_and_dependencies": [
            {
                "requirement_id": item.get("id"),
                "assumptions": item.get("assumptions", []),
                "dependencies": item.get("dependencies", []),
            }
            for item in classified
        ],
        "clarification_questions": clarification_questions(classified),
        "sdlc_workflow": workflow_for(str(sdlc["winner"])) if sdlc else [],
        "sdlc_factors": sdlc_factors(classified),
        "sdlc": sdlc,
        "open_issues": [
            finding for finding in quality_check(classified) if finding["status"] != "pass"
        ] + conflict_check(classified),
    }
