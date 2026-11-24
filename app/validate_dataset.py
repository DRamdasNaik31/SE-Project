"""Validate JSONL training/evaluation data before model training."""

import argparse
import json
from pathlib import Path


def validate(path: Path) -> int:
    errors = 0
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        try:
            row = json.loads(line)
            if not all(row.get(key) for key in ("instruction", "context", "response")):
                raise ValueError("missing instruction, context, or response")
            response = row["response"]
            if not isinstance(response, dict) or not response.get("requirements"):
                raise ValueError("response.requirements must be non-empty")
        except (json.JSONDecodeError, ValueError, TypeError) as exc:
            print(f"{path}:{number}: {exc}")
            errors += 1
    return errors


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    errors = sum(validate(path) for path in args.files)
    if errors:
        raise SystemExit(f"{errors} invalid rows")
    print("All rows valid")


if __name__ == "__main__":
    main()
