"""Human approval gates and append-only audit records for generated artifacts."""

import json
import time
from pathlib import Path
from typing import Any

APPROVAL_GATES = {
    "requirement_baseline",
    "regulatory_interpretation",
    "high_risk_security",
    "conflicting_stakeholders",
    "architecture_critical",
    "sdlc_selection",
    "approved_requirement_change",
    "production_readiness",
}


class GovernanceLog:
    def __init__(self, path: Path = Path("reports/audit_log.jsonl")):
        self.path = path

    def record(self, event: str, actor: str, payload: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        row = {"timestamp": time.time(), "event": event, "actor": actor, "payload": payload}
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def require_approval(gate: str, approved_by: str | None = None) -> None:
    if gate not in APPROVAL_GATES:
        raise ValueError(f"Unknown approval gate: {gate}")
    if not approved_by:
        raise PermissionError(f"Human approval is required for gate: {gate}")
