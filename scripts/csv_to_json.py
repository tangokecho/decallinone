"""Small utility to convert `input/ideas.csv` into `input/ideas.json`.

Usage:
  python scripts/csv_to_json.py

This script is intentionally stdlib-only and safe for CI. It expects the CSV
to have columns `id,idea` and will write a JSON array of objects
`{"id": int, "title": str}` to `input/ideas.json`.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    csv_path = repo_root / "input" / "ideas.csv"
    json_path = repo_root / "input" / "ideas.json"

    if not csv_path.exists():
        raise SystemExit(f"CSV file not found at {csv_path}")

    ideas = []
    with csv_path.open("r", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        for row in reader:
            if not row:
                continue
            # Skip header rows that may repeat
            if row[0].strip().lower() == "id" or row[0].strip() == "":
                continue
            try:
                id_val = int(row[0].strip())
            except ValueError:
                # skip malformed lines
                continue
            title = row[1].strip() if len(row) > 1 else ""
            ideas.append({"id": id_val, "title": title})

    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(ideas, fh, indent=2, ensure_ascii=False)

    print(f"Wrote {len(ideas)} ideas to {json_path}")


if __name__ == "__main__":
    main()
