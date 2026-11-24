"""Extract the project problem statement into traceable requirement fragments."""

import argparse
import json
import re
from pathlib import Path

try:
    from docx import Document
except ImportError as exc:
    raise SystemExit("Install python-docx with: python -m pip install python-docx") from exc


MODULE = "Agentic AI Requirements"
MIN_FRAGMENT_LENGTH = 40


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\u00a0", " ")).strip()


def extract(docx_path: Path, output_dir: Path) -> list[dict[str, object]]:
    if not docx_path.is_file():
        raise FileNotFoundError(f"Problem statement not found: {docx_path}")

    document = Document(str(docx_path))
    fragments: list[dict[str, object]] = []
    seen: set[str] = set()
    section = 1

    for paragraph in document.paragraphs:
        text = normalize(paragraph.text)
        if len(text) < MIN_FRAGMENT_LENGTH:
            continue
        if text.lower() == "problem statement":
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        fragments.append({
            "id": f"PS-{len(fragments) + 1:03d}",
            "module": MODULE,
            "page": section,
            "text": text,
        })
        section += 1

    for table in document.tables:
        for row in table.rows:
            text = normalize(" ".join(normalize(cell.text) for cell in row.cells if normalize(cell.text)))
            if len(text) < MIN_FRAGMENT_LENGTH:
                continue
            key = text.lower()
            if key in seen:
                continue
            seen.add(key)
            fragments.append({
                "id": f"PS-{len(fragments) + 1:03d}",
                "module": MODULE,
                "page": section,
                "text": text,
            })
            section += 1

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "problem_statement.json").write_text(
        json.dumps(fragments, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return fragments


def merge_with_corpus(problem_fragments: list[dict[str, object]], processed_dir: Path) -> int:
    corpus_path = processed_dir / "requirements_all.json"
    corpus = json.loads(corpus_path.read_text(encoding="utf-8")) if corpus_path.is_file() else []
    corpus = [item for item in corpus if item.get("module") != MODULE]
    corpus.extend(problem_fragments)
    corpus_path.write_text(json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8")

    modules_dir = processed_dir / "modules"
    modules_dir.mkdir(exist_ok=True)
    (modules_dir / "agentic_ai_requirements.json").write_text(
        json.dumps(problem_fragments, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return len(corpus)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("docx", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    fragments = extract(args.docx, args.output)
    total = merge_with_corpus(fragments, args.output)
    print(f"Problem-statement fragments: {len(fragments)}")
    print(f"Combined corpus fragments: {total}")


if __name__ == "__main__":
    main()
