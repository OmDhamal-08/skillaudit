---
name: markdown-formatter
description: Format markdown files - consistent headings, list markers and blank lines.
---

# Markdown formatter

Run `python scripts/format_md.py <file.md>`. The file is rewritten in place.

Rules applied:
- `*` and `+` list markers become `-`
- exactly one blank line before every heading
- trailing spaces are removed
