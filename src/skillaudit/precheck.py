"""Checks that are not simple regex rules: skipped files, invisible unicode,
hidden HTML comments and random-looking strings."""

import math
import re
import unicodedata
from collections import Counter

from .config import BINARY_ASSET_EXTENSIONS
from .filetypes import CODE, SKILL_MD, file_kind, is_instructions
from .models import Finding, SkillBundle, SkillFile

# Characters that render as nothing (or flip text direction) but are still read
# by an LLM. Most are unicode category "Cf" (format), which we also check, but
# listing them makes the intent obvious.
INVISIBLE_CHARS = {
    "\u200b", "\u200c", "\u200d", "\u200e", "\u200f",  # zero-width chars, LTR/RTL marks
    "\u2060", "\ufeff",                                # word joiner, BOM in the middle of text
    "\u202a", "\u202b", "\u202c", "\u202d", "\u202e",  # bidi embedding / override
    "\u2066", "\u2067", "\u2068", "\u2069",            # bidi isolates
    "\u3164", "\u2800",                                # hangul filler, braille blank (look empty)
}
ZWJ = "\u200d"

# Unicode "tag" characters (U+E0020..U+E007E) mirror printable ASCII and are
# invisible. They can smuggle a whole sentence into a file.
TAG_START, TAG_END = 0xE0020, 0xE007E

INLINE_CODE = re.compile(r"`[^`]*`")

# A whole token of 32-199 key-like characters. 200+ is already base64-blob.
TOKEN = re.compile(r"(?<![A-Za-z0-9+/=_-])[A-Za-z0-9+/=_-]{32,199}(?![A-Za-z0-9+/=_-])")
# Each piece between separators is judged on its own, so a readable path like
# "ISO-IEC29500-4_2016/shared-documentPropertiesExtended" is not one random blob.
SEPARATORS = re.compile(r"[/_.-]")
MIN_PIECE = 24
# Bits of randomness per character. Words and code names stay below 4,
# hex hashes reach about 4, random keys and base64 data go above 4.2.
ENTROPY_LIMIT = 4.2
# Subresource-integrity hashes in HTML (integrity="sha384-...") are random by design.
KNOWN_HASH_PREFIXES = ("sha256-", "sha384-", "sha512-")

SKIP_MESSAGES = {
    "too_large": ("MED", "file too large to scan; contents not checked"),
    "symlink": ("MED", "symbolic link; not followed, target not checked"),
}


def run_prechecks(bundle: SkillBundle) -> list[Finding]:
    findings = []
    for f in bundle.files:
        if f.skip_reason:
            findings.append(_skipped_finding(f))
            continue
        findings += invisible_findings(f)
        if is_instructions(f.path):
            findings += html_comment_findings(f)
        if file_kind(f.path) in (CODE, SKILL_MD):
            findings += entropy_findings(f)
    return findings


def shannon_entropy(text: str) -> float:
    """Average bits of information per character (0 = all the same, higher = more random)."""
    counts = Counter(text)
    return -sum(c / len(text) * math.log2(c / len(text)) for c in counts.values())


def looks_random(token: str) -> bool:
    if token.startswith(KNOWN_HASH_PREFIXES):
        return False
    for piece in SEPARATORS.split(token):
        has_letters_and_digits = any(c.isdigit() for c in piece) and any(c.isalpha() for c in piece)
        if len(piece) >= MIN_PIECE and has_letters_and_digits and shannon_entropy(piece) >= ENTROPY_LIMIT:
            return True
    return False


def entropy_findings(f: SkillFile) -> list[Finding]:
    out = []
    for n, line in enumerate(f.content.splitlines(), 1):
        for token in TOKEN.findall(line):
            if looks_random(token):
                out.append(Finding(file=f.path, line=n, rule="high-entropy", severity="MED",
                                   source="static",
                                   message="random-looking string (possible hardcoded key or hidden data)",
                                   evidence=token[:80]))
                break
    return out


def invisible_findings(f: SkillFile) -> list[Finding]:
    out = []
    for n, line in enumerate(f.content.splitlines(), 1):
        hits = [(col, ch) for col, ch in enumerate(line) if _is_hidden(line, col, ch)]
        if not hits:
            continue
        column = hits[0][0] + 1
        hidden_text = "".join(chr(ord(ch) - 0xE0000) for _, ch in hits
                              if TAG_START <= ord(ch) <= TAG_END)
        if hidden_text:
            # Show what the hidden sentence says; that is what a reviewer needs to see.
            evidence = f'hidden text: "{hidden_text[:150]}" (unicode tag characters, column {column})'
        else:
            codes = sorted({f"U+{ord(ch):04X}" for _, ch in hits})
            evidence = f"{', '.join(codes[:5])} at column {column}"
        out.append(Finding(file=f.path, line=n, rule="invisible-text", severity="HIGH",
                           source="static", message="invisible or bidi unicode characters",
                           evidence=evidence))
    return out


def html_comment_findings(f: SkillFile) -> list[Finding]:
    # Comments do not show up when markdown is rendered, but Claude reads the raw file.
    # Inside `code` or a ``` block a comment is shown as text, so it hides nothing.
    out = []
    in_fence = False
    for n, line in enumerate(f.content.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if "<!--" in INLINE_CODE.sub("", line):
            out.append(Finding(file=f.path, line=n, rule="html-comment", severity="MED",
                               source="static", message="hidden HTML comment in markdown",
                               evidence=line.strip()[:200]))
    return out


def _is_hidden(line: str, col: int, ch: str) -> bool:
    if ch == ZWJ and _is_emoji_join(line, col):
        return False
    return ch in INVISIBLE_CHARS or unicodedata.category(ch) == "Cf"


def _is_emoji_join(line: str, col: int) -> bool:
    # Many emoji (family, "man technologist", flags) are two emoji glued together
    # with a zero-width joiner. A ZWJ between two symbols is fine; between ASCII
    # letters it is hiding something.
    if col == 0 or col + 1 >= len(line):
        return False
    return _is_symbol(line[col - 1]) and _is_symbol(line[col + 1])


def _is_symbol(ch: str) -> bool:
    return ord(ch) > 0x2000 and unicodedata.category(ch) != "Cf"


def _skipped_finding(f: SkillFile) -> Finding:
    if f.skip_reason == "binary":
        if f.path.lower().endswith(BINARY_ASSET_EXTENSIONS):
            severity, message = "LOW", "binary asset (image/font/document); not scanned"
        else:
            severity, message = "MED", "binary file present; not scanned"
    else:
        severity, message = SKIP_MESSAGES.get(f.skip_reason, ("MED", "file not scanned"))
    return Finding(file=f.path, line=0, rule=f"skipped-{f.skip_reason}", severity=severity,
                   source="static", message=message, evidence=f.path)
