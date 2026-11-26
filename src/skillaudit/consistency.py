"""Does the skill's declared purpose justify what its code can do?

A "PDF helper" that makes network calls and reads ~/.aws is the classic sign
of a trojan skill. The check is a keyword map from the description to the
capabilities each purpose can explain.
"""

import re
from dataclasses import dataclass, field

from .models import SkillBundle

# Keyword found in name/description -> capabilities it can explain.
PURPOSE_ALLOWS = {
    "pdf": {"fs_write"},
    "format": {"fs_write"},
    "convert": {"fs_write"},
    "lint": {"fs_write", "shell"},
    "git": {"shell", "network"},
    "github": {"shell", "network", "env"},
    "deploy": {"shell", "network", "env"},
    "docker": {"shell", "network"},
    "install": {"shell", "network"},
    "build": {"shell"},
    "test": {"shell"},
    "shell": {"shell"},
    "command": {"shell"},
    "api": {"network", "env"},
    "http": {"network"},
    "web": {"network"},
    "fetch": {"network"},
    "download": {"network", "fs_write"},
    "upload": {"network"},
    "scrape": {"network"},
    "slack": {"network", "env"},
    "webhook": {"network", "env"},
    "notify": {"network", "env"},
}

# No simple purpose explains reading SSH keys or cloud credentials.
ALWAYS_SUSPICIOUS = {"secret_files"}


@dataclass
class ConsistencyResult:
    ok: bool
    unjustified: list[str] = field(default_factory=list)
    reason: str = ""
    method: str = "rules"


def rule_based_check(bundle: SkillBundle, capabilities: set[str]) -> ConsistencyResult:
    purpose = f"{bundle.name or ''} {bundle.description or ''}".lower()
    allowed: set[str] = set()
    for keyword, caps in PURPOSE_ALLOWS.items():
        if re.search(rf"\b{re.escape(keyword)}", purpose):
            allowed |= caps

    unjustified = sorted((capabilities - allowed) | (capabilities & ALWAYS_SUSPICIOUS))
    if not unjustified:
        return ConsistencyResult(ok=True, reason="declared purpose covers detected capabilities")
    return ConsistencyResult(ok=False, unjustified=unjustified,
                             reason="description does not explain: " + ", ".join(unjustified))


def check_consistency(bundle: SkillBundle, capabilities: set[str]) -> ConsistencyResult:
    return rule_based_check(bundle, capabilities)
