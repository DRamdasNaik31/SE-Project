"""Conversation orchestrator connecting retrieval, Agent 1, and Agent 2."""

import re
import time
from collections import Counter
from typing import Any

try:
    from . import agent2, rag
    from .agent1 import run as run_agent1
    from .analysis_agents import artifact_bundle, classify
except ImportError:
    import agent2
    import rag
    from agent1 import run as run_agent1
    from analysis_agents import artifact_bundle, classify

GREETING = re.compile(r"^\s*(hi|hello|hey|good morning|good afternoon|good evening)\b[!.?]*$", re.I)
HELP = re.compile(r"\b(help|what can you do|capabilit|who are you)\b", re.I)
SDLC = re.compile(r"\b(sdlc|life cycle|which .*model|recommend.*model|best model)\b", re.I)
REQUIREMENTS = re.compile(r"\b(requirements?|specifications?|srs|elicitation)\b", re.I)
BROAD_FINANCE = re.compile(r"\b(finance|financial|banking|core banking)\b", re.I)


class Session:
    def __init__(self, use_adapter: bool = False) -> None:
        self.requirements: list[dict[str, Any]] = []
        self.requirements_by_module: dict[str, list[dict[str, Any]]] = {}
        self.last_request: str | None = None
        self.last_module: str | None = None
        self.awaiting_module = False
        self.constraints: dict[str, str] = {}
        self.sdlc: dict[str, Any] | None = None
        self.history: list[tuple[str, str]] = []
        self.trace: list[dict[str, Any]] = []
        self.artifacts: dict[str, Any] | None = None
        self.use_adapter = use_adapter

    def log(self, step: str, detail: str, started: float | None = None) -> None:
        self.trace.append({"step": step, "detail": detail, "ms": int((time.time() - started) * 1000) if started else None})


def handle(session: Session, message: str) -> dict[str, Any]:
    session.history.append(("user", message))
    if GREETING.match(message):
        return {"text": "Hello! Ask for banking requirements or an SDLC recommendation.", "requirements": None, "evidence": None, "sdlc": None}
    if HELP.search(message):
        return {"text": "I retrieve source evidence, generate traceable requirements, and score SDLC models. Try: 'requirements for Loan Processing'.", "requirements": None, "evidence": None, "sdlc": None}
    if SDLC.search(message):
        if not session.requirements:
            return {
                "text": "Generate requirements first, then ask me to recommend an SDLC model.",
                "requirements": None,
                "evidence": None,
                "sdlc": None,
            }
        session.sdlc = agent2.score(session.requirements, session.constraints)
        session.artifacts = artifact_bundle(session.requirements, session.sdlc)
        session.log("Agent 2", f"winner={session.sdlc['winner']}")
        return {
            "text": f"Agent 2 — SDLC recommendation: {session.sdlc['explanation']}",
            "requirements": session.requirements,
            "evidence": None,
            "sdlc": session.sdlc,
        }
    started = time.time()
    module = rag.guess_module(message)
    if session.awaiting_module:
        if module is None:
            modules = [
                item for item in rag.available_modules()
                if item != "Agentic AI Requirements"
            ]
            return {
                "text": (
                    "I couldn't match that to a finance sub-branch. "
                    f"Choose one of these: {', '.join(modules)}."
                ),
                "requirements": None,
                "evidence": None,
                "sdlc": None,
            }
        session.awaiting_module = False
        message = f"Generate requirements for {module}"
    if module is None and REQUIREMENTS.search(message) and BROAD_FINANCE.search(message):
        modules = [
            item for item in rag.available_modules()
            if item != "Agentic AI Requirements"
        ]
        session.awaiting_module = True
        return {
            "text": (
                "Finance covers several areas, so let's scope this first. "
                "Which sub-branch should I generate requirements for? "
                f"Available areas: {', '.join(modules)}."
            ),
            "requirements": None,
            "evidence": None,
            "sdlc": None,
        }
    result = run_agent1(message, rag.retrieve, module=module, use_adapter=session.use_adapter)
    module_requirements = result["requirements"]
    classify(module_requirements)
    session.requirements_by_module[module or "General"] = module_requirements
    session.requirements = [
        requirement
        for branch_requirements in session.requirements_by_module.values()
        for requirement in branch_requirements
    ]
    session.sdlc = None
    session.artifacts = artifact_bundle(session.requirements)
    session.last_request, session.last_module = message, module
    session.log("Retrieval", f"{len(result['retrieved'])} passage(s)", started)
    session.log("Agent 1", f"{len(result['requirements'])} requirement(s)")
    return {
        "text": f"Agent 1 — Requirements for {module}: {result['summary']}" if module else f"Agent 1 — Requirements: {result['summary']}",
        "requirements": result["requirements"],
        "evidence": result["retrieved"],
        "sdlc": None,
    }
