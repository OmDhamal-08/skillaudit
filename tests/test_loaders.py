import os

import pytest

from skillaudit.filetypes import CODE, file_kind
from skillaudit.loaders import LoaderError, load_paste, load_path, load_target
from skillaudit.loaders.common import make_file, parse_frontmatter
from tests.conftest import FIXTURES


def test_frontmatter_is_parsed():
    meta = parse_frontmatter("---\nname: pdf\ndescription: Read PDFs\n---\n# Body")
    assert meta == {"name": "pdf", "description": "Read PDFs"}


@pytest.mark.parametrize("text", [
    "# no frontmatter",
    "---\nname: [unclosed\n---\n",      # broken YAML
    "---\njust a string\n---\n",        # valid YAML but not a mapping
    "---\nname: x\n",                   # never closed
])
def test_bad_frontmatter_returns_empty(text):
    assert parse_frontmatter(text) == {}


def test_make_file_handles_binary_size_and_encoding():
    assert make_file("a.bin", b"\x00\x01\x02").skip_reason == "binary"
    assert make_file("a.txt", b"\xff\xfe\xfa").skip_reason == "binary"    # not valid UTF-8
    assert make_file("a.txt", b"x" * 11, max_bytes=10).skip_reason == "too_large"
    assert make_file("a.txt", "héllo".encode()).content == "héllo"


def test_load_folder():
    bundle = load_path(str(FIXTURES / "clean" / "pdf-text-extractor"))
    assert bundle.name == "pdf-text-extractor"
    assert bundle.description.startswith("Extract plain text")
    assert bundle.partial_input is False
    assert [f.path for f in bundle.files] == ["SKILL.md", "scripts/extract.py"]


def test_single_file_is_partial():
    bundle = load_path(str(FIXTURES / "clean" / "pdf-text-extractor" / "SKILL.md"))
    assert bundle.partial_input is True
    assert any("Only one file" in note for note in bundle.notes)


def test_missing_path_raises():
    with pytest.raises(LoaderError):
        load_path("does/not/exist")


def test_file_cap_makes_result_partial(tmp_path):
    (tmp_path / "SKILL.md").write_text("---\nname: x\ndescription: y\n---\n")
    for i in range(5):
        (tmp_path / f"f{i}.py").write_text("print(1)")
    bundle = load_path(str(tmp_path), max_files=3)
    assert len(bundle.files) == 3
    assert bundle.files[0].path == "SKILL.md"           # SKILL.md always survives the cap
    assert bundle.partial_input is True


def test_git_folder_is_skipped(tmp_path):
    (tmp_path / "SKILL.md").write_text("hi")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x")
    assert [f.path for f in load_path(str(tmp_path)).files] == ["SKILL.md"]


def test_symlinks_are_not_followed(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("TOP SECRET")
    skill = tmp_path / "skill"
    skill.mkdir()
    (skill / "SKILL.md").write_text("hi")
    try:
        os.symlink(secret, skill / "notes.txt")
    except (OSError, NotImplementedError):
        pytest.skip("creating symlinks needs extra permissions on this system")

    files = {f.path: f for f in load_path(str(skill)).files}
    assert files["notes.txt"].skip_reason == "symlink"
    assert "TOP SECRET" not in files["notes.txt"].content


def test_paste_with_frontmatter_is_skill_md():
    bundle = load_paste("---\nname: x\ndescription: does x\n---\nbody")
    assert bundle.files[0].path == "SKILL.md"
    assert bundle.description == "does x"
    assert bundle.partial_input is True


def test_paste_without_frontmatter_is_treated_as_code():
    path = load_paste("import os").files[0].path
    assert file_kind(path) == CODE
    assert load_paste("echo hi", filename="run.sh").files[0].path == "run.sh"


def test_load_target_dash_reads_stdin_text():
    bundle = load_target("-", stdin_text="---\nname: piped\n---\n")
    assert bundle.source == "paste"
    assert bundle.name == "piped"
