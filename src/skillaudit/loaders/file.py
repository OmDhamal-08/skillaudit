"""Load a skill from a local folder or a single file."""

import os
from pathlib import Path

from ..config import MAX_FILE_BYTES, MAX_FILES, SKIP_DIRS
from ..models import SkillBundle, SkillFile
from .common import LoaderError, build_bundle, make_file

SINGLE_FILE_NOTE = "Only one file was given; scripts the skill may ship were not scanned."


def load_path(target: str, max_files: int = MAX_FILES,
              max_bytes: int = MAX_FILE_BYTES) -> SkillBundle:
    path = Path(target)
    if not path.exists():
        raise LoaderError(f"Path not found: {target}")

    if path.is_file():
        skill_file = make_file(path.name, path.read_bytes(), max_bytes)
        return build_bundle(f"file:{target}", [skill_file], partial=True,
                            notes=[SINGLE_FILE_NOTE])

    all_paths = _list_files(path)
    files, notes = [], []
    for file_path in all_paths[:max_files]:
        rel = file_path.relative_to(path).as_posix()
        if file_path.is_symlink():
            # Never follow links: a link to ~/.ssh/id_rsa would make us read the
            # user's key and, in FULL mode, send it to the LLM provider.
            files.append(SkillFile(path=rel, skip_reason="symlink"))
        else:
            files.append(make_file(rel, file_path.read_bytes(), max_bytes))

    partial = len(all_paths) > max_files
    if partial:
        notes.append(f"Stopped after {max_files} of {len(all_paths)} files; the rest were not scanned.")
    if not files:
        raise LoaderError(f"No files found in {target}")
    return build_bundle(f"file:{target}", files, partial=partial, notes=notes)


def _list_files(root: Path) -> list[Path]:
    paths = []
    # os.walk does not descend into symlinked folders unless followlinks=True.
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            paths.append(Path(dirpath) / name)
        # Symlinked folders show up in dirnames but are not walked; still report them.
        for name in dirnames:
            if (Path(dirpath) / name).is_symlink():
                paths.append(Path(dirpath) / name)
    # Shallow files first, so SKILL.md and top-level scripts survive the file cap.
    return sorted(paths, key=lambda p: (len(p.relative_to(root).parts), p.as_posix()))
