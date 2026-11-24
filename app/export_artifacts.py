"""Generate reviewable project artifacts from the processed real corpus."""

import json
from pathlib import Path

try:
    from .analysis_agents import artifact_bundle
    from .agent2 import score
except ImportError:
    from analysis_agents import artifact_bundle
    from agent2 import score


def main() -> None:
    corpus_path = Path("data/processed/requirements_all.json")
    if not corpus_path.is_file():
        raise SystemExit("Run app\\extract_pdf.py and app\\build_corpus.py first.")
    corpus = json.loads(corpus_path.read_text(encoding="utf-8"))
    requirements = [{
        "id": item["id"],
        "statement": f"The system shall {str(item['text']).rstrip('.')}.",
        "type": "functional",
        "priority": "medium",
        "evidence": [{
            "module": item["module"],
            "page": item["page"],
            "source_text": item["text"],
        }],
    } for item in corpus]
    sdlc = score(requirements)
    bundle = artifact_bundle(requirements, sdlc)
    output = Path("reports")
    output.mkdir(exist_ok=True)
    for name, value in bundle.items():
        (output / f"{name}.json").write_text(
            json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    print(f"Generated {len(bundle)} review artifacts from {len(requirements)} requirements.")


if __name__ == "__main__":
    main()
