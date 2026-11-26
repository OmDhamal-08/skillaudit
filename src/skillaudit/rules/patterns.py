"""The static rule table.

Each rule is one regex that is matched line by line. To add a rule, append a
Rule here and add a positive and a negative example to tests/test_rules.py.
"""

import re
from dataclasses import dataclass
from typing import Optional

from ..config import ALLOWED_HOSTS


@dataclass(frozen=True)
class Rule:
    id: str
    pattern: str
    severity: str                     # LOW | MED | HIGH
    message: str
    capability: Optional[str] = None  # what a match tells us the skill can do
    ignore_case: bool = True
    code_only: bool = False           # only check code files, not docs or data
    downgrade_in_docs: bool = False   # LOW in reference docs, where it is usually an example
    negatable: bool = True            # one level lower after "never run ..." in markdown


_allowed = "|".join(re.escape(host) for host in ALLOWED_HOSTS)

# Shared with dataflow.py, which looks for these paths inside Python strings.
SECRET_FILE_PATTERN = (
    r"\.ssh[/\\]|\bid_(rsa|ed25519|ecdsa|dsa)\b|\.aws[/\\]credentials|\.npmrc|\.netrc|\.pypirc"
    r"|\.kube[/\\]config|\.gnupg|\.docker[/\\]config\.json|\.git-credentials|\.claude[/\\]\.credentials"
)

RULES = [
    # ---- downloading and running code -------------------------------------
    # curl needs at least one argument, so prose like "never run `curl | sh` lines" is not a hit.
    Rule("pipe-to-shell",
         r"\b(curl|wget)\s+[^\n|]+\|\s*(sudo\s+)?(ba|z|da)?sh\b",
         "HIGH", "pipes downloaded content into a shell", capability="shell"),
    Rule("pipe-to-shell-ps",
         r"\b(iex|Invoke-Expression)\s*\(*\s*(iwr|irm|Invoke-WebRequest|Invoke-RestMethod|New-Object)\b"
         r"|\b(iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b[^\n|]*\|\s*(iex|Invoke-Expression)\b",
         "HIGH", "executes downloaded PowerShell", capability="shell"),

    # ---- secrets ----------------------------------------------------------
    Rule("secret-file", SECRET_FILE_PATTERN,
         "HIGH", "accesses key or credential files", capability="secret_files"),
    # (?<![\w.]) stops "process.env" from matching; .env.example is fine.
    Rule("dotenv-file",
         r"(?<![\w.])\.env\b(?!\.(example|sample|template))",
         "MED", "reads a .env file (usually holds secrets)", capability="env",
         downgrade_in_docs=True),
    # Case-sensitive so "$monkey" does not look like "$...KEY".
    Rule("env-read",
         r"\bos\.environ\b|\bos\.getenv\b|\bprocess\.env\b|\$[Ee]nv:|\bprintenv\b"
         r"|\$\{?[A-Z_]*(KEY|TOKEN|SECRET|PASSWORD|PASSWD)[A-Z_]*\}?",
         "MED", "reads environment variables or secrets", capability="env", ignore_case=False,
         downgrade_in_docs=True),

    # ---- data leaving the machine -----------------------------------------
    # Case-sensitive on purpose: with ignore-case, curl's harmless -f flag matched -F (form upload).
    Rule("exfil-post",
         r"\b(requests|httpx|session|client)\.(post|put)\s*\(|method\s*:\s*['\"](POST|PUT)['\"]"
         r"|\burlopen\([^)]*data\s*="
         r"|\bcurl\b[^\n]*\s(-d|--data[\w-]*|-F|--form|-T|--upload-file)\b"
         r"|\bInvoke-(WebRequest|RestMethod)\b[^\n]*-Method\s+(Post|POST|post)",
         "HIGH", "sends data over the network", capability="network", ignore_case=False,
         downgrade_in_docs=True),
    Rule("netcat",
         r"\b(nc|ncat|netcat)\s+(-\S+\s+)*\S+\s+\d{2,5}\b|/dev/(tcp|udp)/",
         "HIGH", "raw network connection (netcat or /dev/tcp)", capability="network"),

    # ---- dynamic code -----------------------------------------------------
    # (?<![.\w]) skips method calls like regex.exec(...) in JavaScript.
    # No space allowed before "(": code never writes "eval (x)", prose does ("run the eval (or...").
    Rule("eval-exec",
         r"(?<![.\w])(eval|exec)\(|\bnew\s+Function\s*\(",
         "HIGH", "dynamic code execution", capability="shell", ignore_case=False),
    Rule("shell-exec",
         r"\bos\.system\s*\(|\bos\.popen\s*\(|\bshell\s*=\s*True\b|\bchild_process\b",
         "MED", "runs shell commands from code", capability="shell", ignore_case=False, code_only=True),
    Rule("obfuscation",
         r"getattr\(\s*__builtins__|__import__\s*\(|\bbytes\.fromhex\s*\(|codecs\.decode\([^)]*rot.?13"
         r"|(\\x[0-9a-f]{2}){10,}|String\.fromCharCode\s*\(",
         "MED", "common obfuscation technique", code_only=True),
    Rule("base64-decode",
         r"\bb64decode\b|\batob\s*\(|\bbase64\s+(-d|--decode)\b|FromBase64String",
         "MED", "decodes base64 (possible obfuscation)", downgrade_in_docs=True),
    Rule("base64-blob",
         r"[A-Za-z0-9+/]{200,}={0,2}",
         "MED", "large encoded blob"),

    # ---- filesystem -------------------------------------------------------
    # Case-sensitive so doc URLs like ".../3/library/os.html" do not match /Library/.
    # (?<!#!) ignores shebang lines such as #!/usr/bin/env python.
    Rule("write-outside",
         r"~[/\\]|\$HOME\b|%(USERPROFILE|APPDATA|LOCALAPPDATA)%"
         r"|(?<!#!)/(etc|usr|var|opt|Library)/|[Cc]:[\\/]+(Windows|Users)",
         "MED", "references a path outside the skill folder", capability="fs_write", ignore_case=False,
         downgrade_in_docs=True),
    # "../" in code is relative to an unknown working directory, so it can point
    # anywhere. In markdown or XML it is almost always a link between files.
    Rule("write-outside",
         r"\.\.[/\\]",
         "MED", "relative path that climbs out of the current folder", capability="fs_write",
         code_only=True),
    Rule("persistence",
         r"(?<![\w.])\.(bashrc|zshrc|bash_profile|zprofile|profile)\b|\bcrontab\b|\blaunchctl\b|LaunchAgents"
         r"|\bsystemctl\s+(--user\s+)?enable\b|\.git[/\\]hooks|\bschtasks\b|CurrentVersion\\+Run",
         "HIGH", "persistence mechanism (runs again later without asking)", capability="fs_write"),
    # Code only: docs about Claude mention these files all the time. An *instruction*
    # to edit them is the LLM layer's job (INSTRUCTION_SCAN asks for exactly that).
    Rule("agent-config",
         r"\.claude[/\\](settings[\w.-]*\.json|hooks|agents|commands)|\.mcp\.json",
         "HIGH", "touches Claude Code settings, hooks or agent config", capability="fs_write",
         code_only=True),
    Rule("destructive",
         r"\brm\s+-(rf|fr)\s+(/\s|/$|/\*|~|\$HOME|\*)|\bchmod\s+(-R\s+)?777\b|\bmkfs\b|\bdd\s+if=",
         "HIGH", "destructive command", capability="fs_write"),
    Rule("sudo",
         r"\bsudo\b",
         "MED", "privilege escalation (sudo)", capability="shell", ignore_case=False,
         downgrade_in_docs=True),
    Rule("unpinned-install",
         r"\bpip3?\s+install\s+(?!-r\b|-e\b|\.)(?![^\n#]*==)",
         "LOW", "pip install without a pinned version"),
    Rule("unpinned-install",
         r"\bnpm\s+(i|install|add)\s+(?![^\n#]*@\d)|\bnpx\s+(-y\s+)?(?![^\n]*@\d)\S",
         "LOW", "npm/npx package without a pinned version"),

    # ---- instructions aimed at the model ----------------------------------
    # Not negatable: these phrases *start* with "do not", so negation would cancel them.
    Rule("inject-phrase",
         r"\b(ignore|disregard|forget)\s+(all\s+|any\s+)?(the\s+|your\s+)?(previous|prior|above|earlier)\s+(instructions|rules|messages)"
         r"|\bdo\s+not\s+(tell|mention|inform|alert|notify)\b[^\n]{0,40}\buser\b"
         r"|\bdon['\u2019]?t\s+(tell|mention|inform|reveal|disclose)\b[^\n]{0,40}\b(user|anyone)\b"
         r"|\bwithout\s+(telling|informing|notifying|alerting)\s+(the\s+)?user\b"
         r"|\b(silently|secretly|quietly|covertly)\s+(send|upload|post|copy|read|collect|exfiltrate|delete|run|execute|install|modify|forward)\b"
         r"|\bdo\s+not\s+ask\s+(the\s+user\s+)?for\s+(permission|confirmation|approval)",
         "HIGH", "prompt-injection or concealment phrase", negatable=False),

    # ---- links ------------------------------------------------------------
    # A host only counts as allowed if it ends right after the name, so
    # github.com.evil.io is still reported. Subdomains (api.github.com) are allowed.
    Rule("url-unknown",
         rf"https?://(?!([\w-]+\.)*({_allowed})(?=[/:?#\s\"'`)\]>]|$))[\w.-]+",
         "LOW", "URL to a host that is not on the allowlist"),
]
