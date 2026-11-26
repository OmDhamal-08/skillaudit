"""Helpers used by all loaders: decoding files and reading SKILL.md metadata."""

import yaml

from ..config import MAX_FILE_BYTES
from ..models import SkillBundle, SkillFile


class LoaderError(Exception):
    """Raised when a target cannot be loaded (bad path, bad URL, API error)."""


def make_file(path: str, raw: bytes, max_bytes: int = MAX_FILE_BYTES) -> SkillFile:
    """Turn raw bytes into a SkillFile. Binary or oversized files keep no content."""
    if len(raw) > max_bytes:
        return SkillFile(path=path, skip_reason="too_large")
    if b"\x00" in raw[:8192]:
        return SkillFile(path=path, skip_reason="binary")
    try:
        # utf-8-sig drops a leading BOM, which editors on Windows add a lot.
        # Without this every such file would trip the invisible-text check.
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return SkillFile(path=path, skip_reason="binary")
    return SkillFile(path=path, content=text)


def parse_frontmatter(text: str) -> dict:
    """Read the YAML block between the first two '---' lines. Returns {} if missing or broken."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    try:
        data = yaml.safe_load(text[3:end])  # safe_load: never build arbitrary Python objects
    except yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def find_skill_md(files: list[SkillFile]) -> SkillFile | None:
    """The SKILL.md closest to the root wins."""
    candidates = [f for f in files if f.path.rsplit("/", 1)[-1].lower() == "skill.md"]
    if not candidates:
        return None
    return min(candidates, key=lambda f: f.path.count("/"))


def build_bundle(source: str, files: list[SkillFile], partial: bool = False,
                 notes: list[str] | None = None) -> SkillBundle:
    notes = list(notes or [])
    name = description = None

    skill_md = find_skill_md(files)
    if skill_md is None:
        notes.append("No SKILL.md found; the declared purpose of the skill is unknown.")
    else:
        meta = parse_frontmatter(skill_md.content)
        name = _as_text(meta.get("name"))
        description = _as_text(meta.get("description"))
        if not description:
            notes.append("SKILL.md has no description in its frontmatter.")

    return SkillBundle(source=source, files=files, partial_input=partial,
                       name=name, description=description, notes=notes)


def _as_text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip() or None
