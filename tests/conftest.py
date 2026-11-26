from pathlib import Path

import pytest

from skillaudit.loaders.common import build_bundle, make_file

FIXTURES = Path(__file__).parent / "fixtures"


def make_bundle(files: dict[str, str], partial: bool = False):
    """Build a bundle from {path: content}."""
    skill_files = [make_file(path, content.encode("utf-8")) for path, content in files.items()]
    return build_bundle("test", skill_files, partial=partial)


@pytest.fixture(autouse=True)
def no_real_tokens(monkeypatch):
    # Tests must never use the developer's own GitHub token.
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
