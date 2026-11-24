"""Exportable traceability and SDLC workflow artifacts."""

import csv
from pathlib import Path
from typing import Any


def write_traceability(requirements: list[dict[str, Any]], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["requirement_id", "statement", "module", "page", "evidence"])
        for requirement in requirements:
            for evidence in requirement.get("evidence", []):
                writer.writerow([
                    requirement.get("id"),
                    requirement.get("statement"),
                    evidence.get("module"),
                    evidence.get("page"),
                    evidence.get("source_text"),
                ])


def workflow_for(model: str) -> list[dict[str, Any]]:
    common = [
        ("Initiation", "scope, stakeholders, risk classification", "project manager"),
        ("Requirements", "elicit, validate, baseline, trace", "business analyst"),
        ("Design", "architecture and threat modelling", "architect/security"),
        ("Implementation", "code review and static security testing", "engineering"),
        ("Validation", "functional, security, resilience, and audit tests", "QA/security"),
        ("Approval", "compliance and production-readiness gate", "compliance/operations"),
        ("Operations", "monitor controls, incidents, and regulatory changes", "operations"),
    ]
    return [
        {"phase": phase, "activities": activities, "role": role, "model": model}
        for phase, activities, role in common
    ]
