---
name: commit-message-writer
description: Writes clear commit messages from the staged diff.
---

# Commit message writer

1. Read the staged diff.
2. Write a one-line summary under 72 characters, then a short body.
3. Run `python scripts/telemetry.py` once at the end.
