---
name: git-commit-helper
description: Write conventional commit messages from the staged git diff.
---

# Git commit helper

1. Run `python scripts/staged_diff.py` to get the staged changes.
2. Pick a type: feat, fix, docs, refactor, test or chore.
3. Write `type(scope): summary` in under 72 characters, then a short body.
4. Show the message to the user and ask before running `git commit`.
