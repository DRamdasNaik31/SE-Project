"""Compare an available baseline Agent 1 path with a tuned-adapter path.

When no trained adapter exists, the result explicitly records that comparison
as unavailable instead of inventing tuned-model metrics.
"""

import json
from pathlib import Path
from typing import Any

try:
    from .agent1 import run
    from . import rag
except ImportError:
    from agent1 import run
    import rag


def evaluate(test_path: Path, adapter_path: Path = Path("models/agent1_lora")) -> dict[str, Any]:
    rows = [json.loads(line) for line in test_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    baseline_valid = 0
    baseline_grounded = 0
    for row in rows:
        result = run(row["instruction"], rag.retrieve, use_adapter=False)
        baseline_valid += int(result["parse_ok"])
        baseline_grounded += int(bool(result["retrieved"]))
    result: dict[str, Any] = {
        "test_examples": len(rows),
        "baseline": {
            "schema_validity": baseline_valid / max(1, len(rows)),
            "retrieval_coverage": baseline_grounded / max(1, len(rows)),
        },
        "fine_tuned": None,
        "status": "fine-tuned adapter not found; run app/train_agent1.py first",
    }
    if adapter_path.is_dir() and any(adapter_path.iterdir()):
        tuned_valid = 0
        tuned_grounded = 0
        tuned_parsed = 0
        total_generation_seconds = 0.0
        for index, row in enumerate(rows, start=1):
            tuned_result = run(row["instruction"], rag.retrieve, use_adapter=True)
            tuned_valid += int(tuned_result["parse_ok"])
            tuned_grounded += int(bool(tuned_result["retrieved"]))
            tuned_parsed += int(tuned_result["model"].startswith("Qwen2.5"))
            total_generation_seconds += float(tuned_result["generation_s"])
            if index % 10 == 0:
                print(f"tuned evaluation: {index}/{len(rows)}")
        result["fine_tuned"] = {
            "adapter_path": str(adapter_path),
            "schema_validity": tuned_valid / max(1, len(rows)),
            "retrieval_coverage": tuned_grounded / max(1, len(rows)),
            "adapter_inference_used": tuned_parsed / max(1, len(rows)),
            "total_generation_seconds": round(total_generation_seconds, 2),
        }
        result["status"] = "base-vs-fine-tuned held-out comparison completed"
    return result


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=Path, default=Path("data/training/test.jsonl"))
    parser.add_argument("--output", type=Path, default=Path("reports/model_comparison.json"))
    args = parser.parse_args()
    result = evaluate(args.test)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
