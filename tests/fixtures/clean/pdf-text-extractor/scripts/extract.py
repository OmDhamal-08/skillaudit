import sys
from pathlib import Path

from pypdf import PdfReader


def extract(pdf_path: Path) -> Path:
    reader = PdfReader(pdf_path)
    text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    out = pdf_path.with_suffix(".txt")
    out.write_text(text, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(extract(Path(sys.argv[1])))
