"""Profile a CSV file with the standard library: print a JSON summary."""

import csv
import json
import sys


def main(path: str) -> None:
    with open(path, newline="", encoding="utf-8", errors="replace") as handle:
        reader = csv.DictReader(handle)
        columns = reader.fieldnames or []
        stats = {c: {"missing": 0, "distinct": set()} for c in columns}
        rows = 0
        for row in reader:
            rows += 1
            for column in columns:
                value = (row.get(column) or "").strip()
                if not value:
                    stats[column]["missing"] += 1
                elif len(stats[column]["distinct"]) <= 1000:
                    stats[column]["distinct"].add(value)
    summary = {
        "rows": rows,
        "columns": {
            c: {"missing": s["missing"], "distinct_up_to_1000": len(s["distinct"])}
            for c, s in stats.items()
        },
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1])
