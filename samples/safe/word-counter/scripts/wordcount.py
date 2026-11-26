"""Count words, lines and characters in the files given on the command line."""

import sys
from pathlib import Path


def count(path: str) -> tuple[int, int, int]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    return len(text.split()), len(text.splitlines()), len(text)


def main(argv: list[str]) -> int:
    if not argv:
        print("usage: wordcount.py <file> [more files...]")
        return 1
    print(f"{'file':30} {'words':>8} {'lines':>8} {'chars':>8}")
    for path in argv:
        words, lines, chars = count(path)
        print(f"{path:30} {words:>8} {lines:>8} {chars:>8}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
