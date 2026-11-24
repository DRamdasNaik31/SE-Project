"""Create and split curated training examples from corpus fragments."""

import argparse
import json
import random
from pathlib import Path


def make_examples(corpus: list[dict[str, object]]) -> list[dict[str, object]]:
    examples = []
    for item in corpus:
        module = str(item["module"])
        example = {
            "instruction": f"Convert this {module} banking requirement into a software requirement.",
            "context": str(item["text"]),
            "response": {
                "requirements": [{
                    "id": str(item["id"]),
                    "statement": f"The system shall {str(item['text']).rstrip('.')}.",
                    "type": "functional",
                    "priority": "medium",
                    "rationale": f"This supports the {module} capability.",
                    "evidence": [{
                        "module": module,
                        "page": int(item["page"]),
                        "source_text": str(item["text"]),
                    }],
                }],
                "summary": f"Requirement derived from {module}.",
                "grounding": {"evidence_coverage": 1.0, "unsupported_claims": 0},
            },
        }
        examples.append(example)
    return examples


def write_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def split(corpus_path: Path, output_dir: Path, seed: int = 42) -> dict[str, int]:
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    examples = make_examples(corpus)
    random.Random(seed).shuffle(examples)
    n = len(examples)
    splits = {
        "train": examples[: max(1, int(n * 0.8))],
        "validation": examples[max(1, int(n * 0.8)): max(2, int(n * 0.9))],
        "test": examples[max(2, int(n * 0.9)):],
    }
    for name, rows in splits.items():
        write_jsonl(output_dir / f"{name}.jsonl", rows)
    return {name: len(rows) for name, rows in splits.items()}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=Path("data/processed/requirements_all.json"))
    parser.add_argument("--output", type=Path, default=Path("data/training"))
    args = parser.parse_args()
    print(split(args.corpus, args.output))


if __name__ == "__main__":
    main()
