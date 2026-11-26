"""Work out what a skill is able to do, from static findings plus a few extra hints.

Capabilities used everywhere in the project (rules, consistency):
  network       makes network requests
  env           reads environment variables
  secret_files  reads credential/key files
  fs_write      writes or changes files outside its own folder (incl. shell config)
  shell         runs shell commands or dynamically built code

Only SKILL.md and code count. Reference docs are full of example commands
and data files never run, so neither says what the skill itself does.
"""

import re

from .filetypes import CODE, SKILL_MD, file_kind
from .models import Finding, SkillBundle
from .rules import RULES

CAPABILITIES = ("network", "env", "secret_files", "fs_write", "shell")

RULE_CAPABILITY = {rule.id: rule.capability for rule in RULES if rule.capability}

# Things that are not risky enough to be findings but still tell us what the
# skill does. A plain GET request is not a finding, but it is "network".
HINTS = {
    "network": re.compile(
        r"\b(requests|httpx|urllib\.request|aiohttp)\b|\bfetch\s*\(|\b(curl|wget)\s"
        r"|Invoke-(WebRequest|RestMethod)"),
    "shell": re.compile(r"\bsubprocess\b|\bos\.system\b|\bchild_process\b"),
}


def detect_capabilities(bundle: SkillBundle, findings: list[Finding]) -> set[str]:
    caps = {RULE_CAPABILITY[f.rule] for f in findings
            if f.rule in RULE_CAPABILITY and _counts(f.file)}
    for f in bundle.scannable_files():
        if not _counts(f.path):
            continue
        for capability, regex in HINTS.items():
            if regex.search(f.content):
                caps.add(capability)
    return caps


def _counts(path: str) -> bool:
    return file_kind(path) in (SKILL_MD, CODE)
