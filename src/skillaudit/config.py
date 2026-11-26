"""Limits and lists that control a scan. Change behaviour here, not inside the modules."""

# Input caps. A skill bigger than this is unusual, and stopping early keeps
# a hostile repo from making us download or send thousands of files.
MAX_FILES = 50
MAX_FILE_BYTES = 1_000_000

# Folders that are never part of a skill. node_modules is NOT skipped on
# purpose: a skill could ship malicious code inside it.
SKIP_DIRS = {".git", "__pycache__"}

# How files are classified (see filetypes.py). Anything not listed is treated as code.
INSTRUCTION_EXTENSIONS = (".md", ".markdown", ".txt")
DATA_EXTENSIONS = (
    ".json", ".jsonl", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    ".xml", ".xsd", ".csv", ".tsv", ".css", ".svg", ".lock",
)

# Binary files with these extensions are normal assets (LOW).
# Any other binary file is suspicious (MED).
BINARY_ASSET_EXTENSIONS = (
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".webp",
    ".pdf", ".ttf", ".otf", ".woff", ".woff2", ".docx", ".xlsx", ".pptx",
)

# URLs to these hosts are not reported by the url-unknown rule.
ALLOWED_HOSTS = (
    "github.com",
    "raw.githubusercontent.com",
    "pypi.org",
    "npmjs.com",
    "docs.anthropic.com",
)
