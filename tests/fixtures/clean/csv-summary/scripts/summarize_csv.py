import csv
import statistics
import sys


def summarize(path):
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    summary = {"rows": len(rows), "columns": {}}
    for column in (rows[0].keys() if rows else []):
        values = [r[column] for r in rows]
        numbers = []
        for v in values:
            try:
                numbers.append(float(v))
            except ValueError:
                pass
        info = {"empty": sum(1 for v in values if not v)}
        if numbers:
            info.update(min=min(numbers), max=max(numbers), mean=round(statistics.mean(numbers), 3))
        summary["columns"][column] = info
    return summary


if __name__ == "__main__":
    print(summarize(sys.argv[1]))
