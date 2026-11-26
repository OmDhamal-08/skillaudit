import re
import sys
from pathlib import Path


def format_markdown(text: str) -> str:
    lines = [line.rstrip() for line in text.splitlines()]
    out = []
    for line in lines:
        line = re.sub(r"^(\s*)[*+] ", r"\1- ", line)
        if line.startswith("#") and out and out[-1] != "":
            out.append("")
        out.append(line)
    return "\n".join(out).strip() + "\n"


if __name__ == "__main__":
    path = Path(sys.argv[1])
    path.write_text(format_markdown(path.read_text(encoding="utf-8")), encoding="utf-8")
