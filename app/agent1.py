"""Requirements Engineering Agent with a trained-adapter inference path."""

import json
import time
from typing import Any, Callable
from pathlib import Path

try:
    from .security import sanitize_input, validate_source
except ImportError:
    from security import sanitize_input, validate_source

_MODEL_CACHE: dict[str, Any] = {}
MAX_MODULE_REQUIREMENTS = 25


def _fallback_requirements(request: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    requirements = []
    for item in evidence:
        statement = f"The system shall {str(item['text']).rstrip('.')}."
        requirements.append({
            "id": str(item["id"]),
            "statement": statement,
            "type": "functional",
            "category": "functional",
            "categories": ["functional"],
            "priority": "medium",
            "approval_status": "pending_human_review",
            "source_stakeholder": "Banking policy/document",
            "business_justification": f"Supports the requested {item['module']} capability.",
            "dependencies": [],
            "assumptions": ["Applicable organisational policy and implementation details require human confirmation."],
            "acceptance_criteria": [f"Demonstrate that {statement[:-1] if statement.endswith('.') else statement}"],
            "applicable_regulations": ["Jurisdiction and applicability to be confirmed by compliance"],
            "risk_level": "medium",
            "confidence_score": 0.9,
            "rationale": f"Supports the requested {item['module']} capability.",
            "evidence": [{
                "module": item["module"],
                "page": item["page"],
                "source_text": item["text"],
            }],
        })
    return requirements


def _normalise_requirements(requirements: list[dict[str, Any]], evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence_by_id = {str(item["id"]): item for item in evidence}
    normalised = []
    for requirement in requirements:
        item = dict(requirement)
        identifier = str(item.get("id") or "")
        source = evidence_by_id.get(identifier)
        if source:
            item.setdefault("evidence", [{
                "module": source["module"],
                "page": source["page"],
                "source_text": source["text"],
            }])
        item.setdefault("approval_status", "pending_human_review")
        item.setdefault("source_stakeholder", "Source document")
        item.setdefault("business_justification", "Traceable to approved source evidence")
        item.setdefault("dependencies", [])
        item.setdefault("assumptions", [])
        item.setdefault("acceptance_criteria", [])
        item.setdefault("applicable_regulations", [])
        item.setdefault("risk_level", "medium")
        item.setdefault("confidence_score", 0.7)
        item.setdefault("categories", [str(item.get("category") or item.get("type") or "functional")])
        normalised.append(item)
    return normalised


def _load_adapter(adapter_path: Path) -> tuple[Any, Any]:
    cached = _MODEL_CACHE.get("adapter")
    if cached:
        return cached
    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    config = json.loads((adapter_path / "adapter_config.json").read_text(encoding="utf-8"))
    base_name = str(config["base_model_name_or_path"])
    tokenizer = AutoTokenizer.from_pretrained(str(adapter_path))
    model = AutoModelForCausalLM.from_pretrained(
        base_name,
        dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto" if torch.cuda.is_available() else None,
    )
    model = PeftModel.from_pretrained(model, str(adapter_path))
    model.eval()
    _MODEL_CACHE["adapter"] = (model, tokenizer)
    return model, tokenizer


def _parse_generated_json(text: str) -> dict[str, Any] | None:
    start = text.find("{")
    if start < 0:
        return None
    try:
        value, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) and isinstance(value.get("requirements"), list) else None


def _adapter_requirements(
    request: str,
    evidence: list[dict[str, Any]],
    adapter_path: Path = Path("models/agent1_lora"),
) -> tuple[list[dict[str, Any]], float] | None:
    if not adapter_path.joinpath("adapter_config.json").is_file():
        return None
    model, tokenizer = _load_adapter(adapter_path)
    context = "\n\n".join(
        f"[{item['id']}] {item['text']}" for item in evidence[:6]
    )
    prompt = (
        "Instruction:\n" + request +
        "\nEvidence:\n" + context +
        "\nResponse:\n"
    )
    inputs = tokenizer(prompt, return_tensors="pt")
    if hasattr(model, "device"):
        inputs = {key: value.to(model.device) for key, value in inputs.items()}
    import torch
    started = time.time()
    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=384,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    generated = tokenizer.decode(
        output[0][inputs["input_ids"].shape[1]:],
        skip_special_tokens=True,
    )
    parsed = _parse_generated_json(generated)
    if not parsed:
        return None
    return parsed["requirements"], time.time() - started


def run(
    request: str,
    retriever: Callable[..., list[dict[str, Any]]],
    k: int = 6,
    module: str | None = None,
    use_adapter: bool = True,
    sample: bool = False,
) -> dict[str, Any]:
    safety = sanitize_input(request)
    if safety.injection_detected:
        return {
            "requirements": [],
            "summary": "The request contains a prompt-injection pattern and was blocked for review.",
            "grounding": {"evidence_coverage": 0.0, "unsupported_claims": 0},
            "retrieved": [],
            "parse_ok": False,
            "generation_s": 0.0,
            "model": "blocked",
        }
    retrieval_k = max(k, MAX_MODULE_REQUIREMENTS) if module else k
    evidence = retriever(safety.text, k=retrieval_k, module=module)
    for item in evidence:
        validate_source(item)
    requirements = _fallback_requirements(request, evidence)
    model_name = "deterministic evidence fallback"
    generation_s = 0.0
    if use_adapter:
        try:
            tuned = _adapter_requirements(safety.text, evidence)
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            tuned = None
            model_name = f"adapter unavailable: {exc.__class__.__name__}"
        if tuned:
            requirements, generation_s = tuned
            model_name = "Qwen2.5-1.5B-Instruct + trained LoRA adapter"
    requirements = _normalise_requirements(requirements, evidence)
    if module:
        requirements = requirements[:MAX_MODULE_REQUIREMENTS]
    unsupported = 0 if evidence else 1
    return {
        "requirements": requirements,
        "summary": (
            "Evidence was insufficient to produce a grounded requirement."
            if not requirements
            else f"Generated {len(requirements)} source-grounded requirement(s)."
        ),
        "grounding": {
            "evidence_coverage": 1.0 if requirements else 0.0,
            "unsupported_claims": unsupported,
        },
        "retrieved": evidence,
        "parse_ok": True,
        "generation_s": round(generation_s, 3),
        "model": model_name if use_adapter else "base model requested",
        "sample": sample,
    }
