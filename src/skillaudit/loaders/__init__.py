"""Loaders turn the three kinds of input (paste, local path, GitHub URL) into a SkillBundle."""

from ..models import SkillBundle
from .common import LoaderError
from .file import load_path
from .github import load_github
from .paste import load_paste


def load_target(target: str, stdin_text: str | None = None,
                stdin_name: str | None = None) -> SkillBundle:
    """Pick the right loader for a CLI target. '-' means read from stdin."""
    if target == "-":
        return load_paste(stdin_text or "", stdin_name)
    if target.startswith(("https://github.com/", "http://github.com/")):
        return load_github(target.replace("http://", "https://", 1))
    return load_path(target)


__all__ = ["LoaderError", "load_github", "load_paste", "load_path", "load_target"]
