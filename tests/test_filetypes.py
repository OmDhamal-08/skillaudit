import pytest

from skillaudit.capabilities import detect_capabilities
from skillaudit.filetypes import CODE, DATA, DOC, SKILL_MD, file_kind
from skillaudit.rules import run_rules
from tests.conftest import make_bundle


@pytest.mark.parametrize("path, kind", [
    ("SKILL.md", SKILL_MD),
    ("sub/skill.md", SKILL_MD),
    ("reference/api.md", DOC),
    ("notes.txt", DOC),
    ("scripts/run.py", CODE),
    ("viewer.html", CODE),
    ("install", CODE),                 # no extension: assume it can run
    ("schemas/wml.xsd", DATA),
    ("config.json", DATA),
    ("style.css", DATA),
])
def test_file_kind(path, kind):
    assert file_kind(path) == kind


def severity_of(rule_id: str, files: dict[str, str]) -> dict[str, str]:
    return {f.file: f.severity for f in run_rules(make_bundle(files)) if f.rule == rule_id}


def test_example_commands_are_low_in_reference_docs_only():
    line = "sudo apt install jq"
    severities = severity_of("sudo", {"SKILL.md": line, "reference/setup.md": line, "run.sh": line})
    assert severities == {"SKILL.md": "MED", "reference/setup.md": "LOW", "run.sh": "MED"}


def test_parent_path_only_counts_in_code():
    # Found on real skills: markdown links and XSD schemaLocation use "../" all the time.
    files = {
        "reference/a.md": "See [shared](../shared/tool-use.md)",
        "schemas/wml.xsd": '<xsd:import schemaLocation="../mce/mc.xsd"/>',
        "scripts/sync.py": 'open("../other-skill/SKILL.md", "a")',
    }
    assert set(severity_of("write-outside", files)) == {"scripts/sync.py"}


def test_reference_docs_do_not_add_capabilities():
    doc_only = make_bundle({"SKILL.md": "hi", "reference/api.md": "key = os.environ['API_KEY']"})
    in_code = make_bundle({"SKILL.md": "hi", "run.py": "key = os.environ['API_KEY']"})
    assert "env" not in detect_capabilities(doc_only, run_rules(doc_only))
    assert "env" in detect_capabilities(in_code, run_rules(in_code))
