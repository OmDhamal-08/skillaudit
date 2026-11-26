"""Load text that was pasted or piped in on stdin."""

from ..models import SkillBundle
from .common import build_bundle, make_file

PARTIAL_NOTE = "Only this one text was scanned; any scripts the skill ships were not provided."


def guess_name(text: str) -> str:
    # Frontmatter means it is almost certainly a SKILL.md. Anything else is
    # treated as code: no extension means code in filetypes.file_kind(), so all
    # code rules run and the LLM reviews it as a script. (Not ".txt": that is a doc.)
    return "SKILL.md" if text.lstrip().startswith("---") else "pasted-code"


def load_paste(text: str, filename: str | None = None) -> SkillBundle:
    name = filename or guess_name(text)
    skill_file = make_file(name, text.encode("utf-8"))
    return build_bundle("paste", [skill_file], partial=True, notes=[PARTIAL_NOTE])
