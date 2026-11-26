"""Run every rule against every line of every scannable file."""

import re

from ..filetypes import CODE, DOC, SKILL_MD, file_kind
from ..models import Finding, SkillBundle
from .patterns import RULES

# Compile once at import time instead of once per line.
COMPILED = [(rule, re.compile(rule.pattern, re.IGNORECASE if rule.ignore_case else 0))
            for rule in RULES]

ONE_LEVEL_LOWER = {"HIGH": "MED", "MED": "LOW", "LOW": "LOW"}

# "Never run ...", "do not use ...": the text is warning against the thing, not asking for it.
# The verb has to follow directly, so "don't forget to run" and "never mind, run" do not count.
NEGATION = re.compile(
    r"\b(never|do\s+not|don['\u2019]?t|avoid|must\s+not|should\s+not|shouldn['\u2019]?t)\s+"
    r"(run|running|execute|executing|use|using|pipe|piping|call|copy|paste|read|reading"
    r"|install|installing|add|adding|open|opening|touch)\b",
    re.IGNORECASE,
)
SENTENCE_BREAK = re.compile(r"[.!?:;](\s|$)")


def run_rules(bundle: SkillBundle) -> list[Finding]:
    findings = []
    for f in bundle.scannable_files():
        findings += scan_text(f.path, f.content, file_kind(f.path))
    return findings


def scan_text(path: str, text: str, kind: str) -> list[Finding]:
    """All rule matches in one text. Also used on decoded payloads (see decoding.py)."""
    findings = []
    for n, line in logical_lines(text, path):
        matched_ids = set()      # two regexes can share an id; report it once per line
        for rule, regex in COMPILED:
            if rule.code_only and kind != CODE:
                continue
            if rule.id in matched_ids:
                continue
            match = regex.search(line)
            if not match:
                continue
            matched_ids.add(rule.id)

            severity, message = rule.severity, rule.message
            if rule.downgrade_in_docs and kind == DOC:
                severity = "LOW"
            if rule.negatable and kind in (SKILL_MD, DOC) and is_negated(line, match.start()):
                severity = ONE_LEVEL_LOWER[severity]
                message += " (mentioned as something not to do)"
            findings.append(Finding(
                file=path, line=n, rule=rule.id, severity=severity, source="static",
                message=message, evidence=_evidence(line, match.start()),
            ))
    return findings


def logical_lines(text: str, path: str = "") -> list[tuple[int, str]]:
    """(line number, text) with continued lines joined into one.

    A command split with a trailing backslash (shell, Python) or a trailing
    backtick (PowerShell) is one command, so the rules have to see it whole.
    """
    continuation = ("\\", "`") if path.lower().endswith((".ps1", ".psm1")) else ("\\",)
    lines = text.splitlines()
    result = []
    i = 0
    while i < len(lines):
        start, parts = i, [lines[i]]
        while parts[-1].rstrip().endswith(continuation) and i + 1 < len(lines):
            parts[-1] = parts[-1].rstrip()[:-1]
            i += 1
            parts.append(lines[i].strip())
        result.append((start + 1, " ".join(parts)))
        i += 1
    return result


def is_negated(line: str, start: int) -> bool:
    """True if the same sentence says "never run ..." (or similar) before the match."""
    before = line[:start]
    cut = max((m.end() for m in SENTENCE_BREAK.finditer(before)), default=0)
    return bool(NEGATION.search(before[cut:]))


def _evidence(line: str, start: int, width: int = 200) -> str:
    """The matched line. For long (minified) lines, a window around the match."""
    if len(line) <= width:
        return line.strip()
    begin = max(0, start - 40)
    return line[begin:begin + width].strip()
