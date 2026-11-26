"""Run skillaudit over the test fixtures (or any folder of skills) and print a results table.

    python scripts/evaluate.py                               # the fixtures
    python scripts/evaluate.py --skills-dir path/to/skills   # every sub-folder with a SKILL.md

For the fixtures: "caught" means a malicious skill got DO_NOT_INSTALL, and a
"false positive" means a clean skill got DO_NOT_INSTALL.
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from skillaudit.auditor import audit  # noqa: E402
from skillaudit.loaders import load_path  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"


def row(label: str, folder: Path):
    report = audit(load_path(str(folder)))
    rules = sorted({f.rule for f in report.findings if f.severity != "LOW"})
    line = f"| {label} | {folder.name} | {report.score} | {report.verdict} | {', '.join(rules) or '-'} |"
    return report, line


def evaluate_fixtures() -> None:
    lines, caught, review, false_pos, clean_with_high = [], 0, 0, 0, 0
    for kind in ("malicious", "clean"):
        for folder in sorted(p for p in (FIXTURES / kind).iterdir() if p.is_dir()):
            report, line = row(kind, folder)
            lines.append(line)
            if kind == "malicious":
                caught += report.verdict == "DO_NOT_INSTALL"
                review += report.verdict == "REVIEW"
            else:
                false_pos += report.verdict == "DO_NOT_INSTALL"
                clean_with_high += any(f.severity == "HIGH" for f in report.findings)

    print_table(lines)
    print(f"- Malicious caught (DO_NOT_INSTALL): {caught}/10")
    print(f"- Malicious flagged for REVIEW only: {review}/10")
    print(f"- Clean skills blocked (false positives): {false_pos}/10")
    print(f"- Clean skills with at least one HIGH finding: {clean_with_high}/10")


def evaluate_folder(skills_dir: Path) -> None:
    folders = sorted(p.parent for p in skills_dir.glob("*/SKILL.md"))
    lines, verdicts = [], Counter()
    for folder in folders:
        report, line = row("skill", folder)
        lines.append(line)
        verdicts[report.verdict] += 1
    print_table(lines)
    print(f"- {len(folders)} skills: " + ", ".join(f"{v} {k}" for k, v in sorted(verdicts.items())))


def print_table(lines: list[str]) -> None:
    print("| Set | Skill | Score | Verdict | MED/HIGH rules |")
    print("|---|---|---|---|---|")
    print("\n".join(lines))
    print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills-dir", type=Path, help="evaluate every <dir>/*/SKILL.md instead of the fixtures")
    args = parser.parse_args()

    print("## Results: static checks\n")
    if args.skills_dir:
        evaluate_folder(args.skills_dir)
    else:
        evaluate_fixtures()


if __name__ == "__main__":
    main()
