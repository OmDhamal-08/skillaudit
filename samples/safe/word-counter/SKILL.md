---
name: word-counter
description: Count words, lines and characters in one or more text files and print a small table.
---

# Word counter

Run `python scripts/wordcount.py <file.txt> [more files...]`.

The script only reads the files you pass on the command line and prints the
counts to stdout. It makes no network calls, reads no secrets, and writes
nothing to disk. Report the table it prints back to the user.
