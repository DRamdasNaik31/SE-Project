"""Extract page-preserving text from the source requirements PDF."""

import argparse
import json
from pathlib import Path

from pypdf import PdfReader


def extract(pdf_path: Path, output_dir: Path) -> list[dict[str, object]]:
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Source PDF not found: {pdf_path}")
    output_dir.mkdir(parents=True, exist_ok=True)
    pages = [
        {"page": index, "text": page.extract_text() or ""}
        for index, page in enumerate(PdfReader(str(pdf_path)).pages, start=1)
    ]
    (output_dir / "pages.json").write_text(
        json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    with (output_dir / "requirements_text.txt").open("w", encoding="utf-8") as file:
        for page in pages:
            file.write(f"\n\n===== PAGE {page['page']} =====\n{page['text']}")
    return pages


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    args = parser.parse_args()
    pages = extract(args.pdf, args.output)
    empty = [p["page"] for p in pages if len(str(p["text"]).strip()) < 20]
    print(f"Pages: {len(pages)}")
    print(f"Characters: {sum(len(str(p['text'])) for p in pages)}")
    print(f"Pages with almost no text: {empty}")


if __name__ == "__main__":
    main()
