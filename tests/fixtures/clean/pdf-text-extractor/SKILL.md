---
name: pdf-text-extractor
description: Extract plain text from PDF files and save it as a .txt file next to the PDF.
---

# PDF text extractor

Use this when the user wants the text content of a PDF.

1. Make sure the dependency is installed: `pip install pypdf==4.3.1`
2. Run `python scripts/extract.py <file.pdf>`
3. Tell the user where the `.txt` file was written and show the first few lines.

If the PDF is scanned (no text layer), say so instead of guessing.
