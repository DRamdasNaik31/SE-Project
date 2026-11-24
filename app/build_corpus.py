"""Build stable, page-traceable requirement fragments from pages.json."""

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

MODULES = {
    "Agentic AI Requirements": "PS",
    "Account Opening": "ACC",
    "Customer Information": "CUST",
    "Cheque Book Facility": "CHQ",
    "Service Branches and Clearing": "CLR",
    "Cash Department at Branch": "CASH",
    "Cash Credit and Overdraft": "CCOD",
    "Loan Processing": "LOAN",
    "Bills": "BILL",
    "Remittances": "REM",
    "Interest and Fee Calculation": "INT",
    "Transaction Posting": "TXN",
    "Safe Custody Facility": "SAFE",
    "Tax Calculation": "TAX",
    "Lockers": "LOCK",
    "General Ledger": "GL",
    "Regulatory Requirements": "REG",
    "Head Office": "HO",
    "Reports": "RPT",
}
BULLET = re.compile(r"^\s*(?:[•●▪\-*]|\(?\d+(?:\.\d+)*[.)]|\(?[a-z][.)]|\(?[ivx]+\))\s+", re.I)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value)
    value = value.replace("’", "'").replace("“", '"').replace("”", '"')
    return re.sub(r"\s+", " ", value).strip()


def build(pages_path: Path, output_dir: Path, first_content_page: int = 1) -> list[dict[str, object]]:
    pages = json.loads(pages_path.read_text(encoding="utf-8"))
    repeated = Counter(
        normalize(line)
        for page in pages
        for line in set(str(page["text"]).splitlines())
        if line.strip()
    )
    junk = {line for line, count in repeated.items() if count >= max(5, len(pages) // 4)}
    headings = {normalize(name).lower(): name for name in MODULES}
    fragments: list[dict[str, object]] = []
    current: str | None = None
    buffer: list[str] = []
    page_number: int | None = None

    def flush() -> None:
        nonlocal buffer, page_number
        text = normalize(" ".join(buffer))
        if current and page_number is not None and len(text) >= 25:
            fragments.append({"module": current, "page": page_number, "text": text})
        buffer, page_number = [], None

    for page in pages:
        page_no = int(page["page"])
        if page_no < first_content_page:
            continue
        for raw in str(page["text"]).splitlines():
            line = normalize(raw)
            if not line or line in junk or re.fullmatch(r"(page )?\d+", line, re.I):
                continue
            heading_candidate = re.sub(r"^\d+\.\s*", "", line)
            if heading_candidate.lower() in headings:
                flush()
                current = headings[heading_candidate.lower()]
                continue
            if BULLET.match(raw) and buffer:
                flush()
            if page_number is None:
                page_number = page_no
            buffer.append(BULLET.sub("", raw, count=1) if BULLET.match(raw) else raw)
    flush()

    seen: set[tuple[str, str]] = set()
    counters: Counter[str] = Counter()
    clean: list[dict[str, object]] = []
    for fragment in fragments:
        key = (str(fragment["module"]), str(fragment["text"]).lower())
        if key in seen:
            continue
        seen.add(key)
        prefix = MODULES[str(fragment["module"])]
        counters[prefix] += 1
        clean.append({"id": f"{prefix}-{counters[prefix]:03d}", **fragment})

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "requirements_all.json").write_text(
        json.dumps(clean, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    modules_dir = output_dir / "modules"
    modules_dir.mkdir(exist_ok=True)
    for module in MODULES:
        selected = [item for item in clean if item["module"] == module]
        filename = re.sub(r"\W+", "_", module).lower() + ".json"
        (modules_dir / filename).write_text(json.dumps(selected, indent=2), encoding="utf-8")
    return clean


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pages", type=Path, default=Path("data/processed/pages.json"))
    parser.add_argument("--output", type=Path, default=Path("data/processed"))
    parser.add_argument("--first-content-page", type=int, default=1)
    args = parser.parse_args()
    corpus = build(args.pages, args.output, args.first_content_page)
    print(f"Corpus fragments: {len(corpus)}")


if __name__ == "__main__":
    main()
