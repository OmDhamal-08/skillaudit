"""Static-only results on the fixture set. These lock in the baseline numbers in the README."""

import pytest

from skillaudit.auditor import audit
from skillaudit.loaders import load_path
from skillaudit.scoring import HARD_FAIL
from tests.conftest import FIXTURES

MALICIOUS = sorted(p.name for p in (FIXTURES / "malicious").iterdir() if p.is_dir())
CLEAN = sorted(p.name for p in (FIXTURES / "clean").iterdir() if p.is_dir())

# Known gap: writing to "../other-skill/SKILL.md" only matches a MED rule, so
# line rules alone flag it for REVIEW but do not block it.
STATIC_REVIEW_ONLY = {"path-traversal-write"}


def test_fixture_counts():
    assert len(MALICIOUS) == 10
    assert len(CLEAN) == 10


@pytest.mark.parametrize("name", MALICIOUS)
def test_malicious_fixture_is_caught(name):
    report = audit(load_path(str(FIXTURES / "malicious" / name)))
    expected = "REVIEW" if name in STATIC_REVIEW_ONLY else "DO_NOT_INSTALL"
    assert report.verdict == expected, [f.rule for f in report.findings]


@pytest.mark.parametrize("name", CLEAN)
def test_clean_fixture_is_not_blocked(name):
    report = audit(load_path(str(FIXTURES / "clean" / name)))
    assert report.verdict != "DO_NOT_INSTALL", [f.rule for f in report.findings]
    assert not any(f.rule in HARD_FAIL for f in report.findings)
