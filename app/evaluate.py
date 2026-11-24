"""Small offline evaluation for schema validity and grounding coverage."""

import argparse
import json
from pathlib import Path

try:
    from .agent1 import run
    from . import rag
except ImportError:
    from agent1 import run
    import rag


def evaluate(path: Path) -> dict[str, float]:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    valid = grounded = covered = generated = 0
    for row in rows:
        result = run(row["instruction"], rag.retrieve)
        valid += bool(result["parse_ok"] and isinstance(result["requirements"], list))
        grounded += bool(result["retrieved"])
        generated += len(result["requirements"])
        covered += sum(bool(item.get("evidence")) for item in result["requirements"])
    return {
        "examples": float(len(rows)),
        "schema_validity": valid / max(1, len(rows)),
        "retrieval_coverage": grounded / max(1, len(rows)),
        "requirement_evidence_coverage": covered / max(1, generated),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=Path, default=Path("data/training/test.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/evaluation.json"))
    args = parser.parse_args()
    result = evaluate(args.test)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
