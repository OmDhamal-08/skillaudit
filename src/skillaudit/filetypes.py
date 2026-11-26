"""Every file in a skill gets a kind. The kind decides which rules apply,
how serious a match is, and which prompt the LLM uses.

  skill_md  SKILL.md: the instructions Claude actually follows
  doc       other .md/.txt files: reference material, usually full of examples
  code      anything that can run (unknown extensions count as code, to be safe)
  data      json/xml/yaml/csv/css...: never executed
"""

from .config import DATA_EXTENSIONS, INSTRUCTION_EXTENSIONS

SKILL_MD = "skill_md"
DOC = "doc"
CODE = "code"
DATA = "data"


def file_kind(path: str) -> str:
    name = path.rsplit("/", 1)[-1].lower()
    if name == "skill.md":
        return SKILL_MD
    if name.endswith(INSTRUCTION_EXTENSIONS):
        return DOC
    if name.endswith(DATA_EXTENSIONS):
        return DATA
    return CODE


def is_instructions(path: str) -> bool:
    """Text Claude reads as instructions (SKILL.md or another doc)."""
    return file_kind(path) in (SKILL_MD, DOC)
