# skillaudit

A security scanner for [Claude skills](https://docs.anthropic.com/). Point it at a skill folder, a
`SKILL.md`, or a GitHub URL, and it tells you whether the skill does things its description
doesn't explain: piping downloads into a shell, reading SSH keys, hiding instructions from you,
and so on.

```
skillaudit https://github.com/someone/skills/tree/main/pdf-helper
```

Everything runs locally. No API key, no account.

## Why

A skill is a folder of instructions (`SKILL.md`) plus optional scripts. When you install one,
Claude follows those instructions and runs those scripts **with your permissions**. That makes
skills a supply-chain risk, the same way an npm package or a browser extension is, with one
extra twist: the instructions themselves can be an attack (prompt injection, "don't tell the
user", invisible unicode text).

Most people install skills by reading the README and hoping. skillaudit is the check you run first.

## What it checks

| Layer | What it catches |
|---|---|
| Pre-checks | invisible/bidi unicode, hidden text in unicode tag characters (decoded), hidden HTML comments, random-looking strings, binaries, symlinks, oversized files |
| Static rules | 20 regex rules: `curl \| sh`, credential files, env/secret reads, data being POSTed out, reverse shells, `eval`/`exec`, obfuscation, persistence (`.bashrc`, cron, git hooks), Claude config tampering, destructive commands, injection phrases, unknown URLs |
| Purpose check | does the declared purpose explain what the code can do? A "PDF helper" that needs the network and `~/.aws` is the classic trojan |

## Install

Python 3.10+.

```bash
git clone https://github.com/OmDhamal-08/skillaudit.git
cd skillaudit
pip install -e .
```

## Usage

```bash
skillaudit ./my-skill/                    # a skill folder
skillaudit ./my-skill/SKILL.md            # one file (result is PARTIAL)
skillaudit https://github.com/user/repo/tree/main/skills/pdf-helper
cat SKILL.md | skillaudit -               # stdin
skillaudit ./my-skill --json              # machine-readable
skillaudit ./my-skill --markdown          # for a PR comment
skillaudit ./my-skill --fail-under 70     # exit 1 if score < 70 or verdict is DO_NOT_INSTALL
```

For private repos or to avoid GitHub's 60 requests/hour limit, set `GITHUB_TOKEN`.

Exit codes: `0` ok, `1` failed `--fail-under`, `2` bad input.

## How it works

1. **Loaders** turn any input into a `SkillBundle` (list of files + name/description from the
   frontmatter). Files are read as text and never executed. Symlinks are never followed.
2. **File kinds.** Every file is `SKILL.md`, a reference doc, code, or data. The kind decides which
   rules apply and how serious a match is: `../` in a Python script is suspicious, `../` in a
   markdown link is just a link.
3. **Pre-checks and rules** run line by line and produce findings with file, line and evidence.
   Lines continued with `\` are joined first, and "never run ..." in a doc lowers a match.
4. **Purpose check** compares what the skill *says* it does with what it *can* do.
5. **Scorer** turns it all into a score and a verdict.

## Scoring

Start at 100. Each **kind** of finding costs points once per skill (HIGH 25, MED 10, LOW 3), plus
20 if the purpose check fails.

| Verdict | When |
|---|---|
| `DO_NOT_INSTALL` | score < 50, or a HIGH finding from a hard-fail rule (`pipe-to-shell`, `pipe-to-shell-ps`, `secret-file`, `persistence`, `invisible-text`, `inject-phrase`) |
| `REVIEW` | everything else for now |

Pattern rules cannot judge intent, so a scan never says "safe" yet. A `SAFE_ISH` verdict needs a
semantic review on top, which is the next thing to build.

## Results

10 malicious skills (one attack each) and 10 realistic clean skills, in `tests/fixtures/`.
Reproduce with `python scripts/evaluate.py`.

| Metric | Result |
|---|---|
| Malicious skills blocked (`DO_NOT_INSTALL`) | **9 / 10** |
| Malicious skills flagged `REVIEW` only | 1 / 10 |
| Clean skills blocked (false positives) | **0 / 10** |
| Clean skills with any HIGH finding | 1 / 10 (a Slack notifier that has to POST) |

The one miss is `path-traversal-write`: a "meeting notes" skill that appends text to other
skills' `SKILL.md` via `../`. With line rules that is one MED finding plus a failed purpose check
(score 70, `REVIEW`).

## Project layout

```
src/skillaudit/
  cli.py            typer entry point (thin: parse args, call audit(), print)
  auditor.py        the pipeline: audit(bundle) -> Report
  models.py         pydantic models: SkillFile, SkillBundle, Finding, Report
  config.py         limits, allowlisted hosts, file extensions
  filetypes.py      skill_md / doc / code / data
  loaders/          paste, local path, GitHub
  precheck.py       unicode, HTML comments, random strings, skipped files
  rules/            rule table (patterns.py) + engine (joined lines, negation)
  capabilities.py   what the skill can do (network, env, secret_files, fs_write, shell)
  consistency.py    purpose vs capabilities
  scoring.py        score + verdict
  report/           terminal (rich), JSON, markdown
tests/              fixtures in tests/fixtures/
scripts/evaluate.py results table for the fixtures or any folder of skills
```

## Development

```bash
python -m venv .venv
.venv/Scripts/activate            # Windows; on Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/evaluate.py
```

## Limitations

- Line rules see one line at a time (continued lines are joined), so a value read on one line and
  sent on another is two separate findings.
- Negation is understood only in simple wording ("never run ..." in the same sentence).
- The purpose check is a keyword map.
- At most 50 files and 1 MB per file are scanned. Anything past that makes the result PARTIAL.
- A clean report is not a guarantee. It means none of these checks found anything.

## Security of the scanner itself

The skill being scanned is hostile by assumption, so the scanner:

- never executes or imports anything from it, and never follows symlinks;
- strips terminal control codes before printing and escapes markdown in PR comments;
- caps file count and size before downloading anything.

## License

MIT
