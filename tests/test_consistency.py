from skillaudit.consistency import rule_based_check
from tests.conftest import make_bundle


def skill(description: str, name: str = "x"):
    return make_bundle({"SKILL.md": f"---\nname: {name}\ndescription: {description}\n---\n"})


def test_pdf_tool_with_network_is_unjustified():
    result = rule_based_check(skill("Extract text from PDF files"), {"network", "fs_write"})
    assert not result.ok
    assert result.unjustified == ["network"]


def test_api_tool_may_use_network_and_env():
    assert rule_based_check(skill("Get weather from the OpenWeather API"), {"network", "env"}).ok


def test_secret_files_are_never_justified():
    result = rule_based_check(skill("Deploy the app to the cloud"), {"secret_files", "network"})
    assert result.unjustified == ["secret_files"]


def test_keywords_match_whole_words_only():
    # "rapid" contains "api" but should not allow network access
    assert not rule_based_check(skill("Rapid note taking"), {"network"}).ok


def test_name_counts_as_part_of_the_purpose():
    assert rule_based_check(skill("Post status updates", name="slack-notifier"), {"network"}).ok


def test_missing_description_justifies_nothing():
    bundle = make_bundle({"run.py": "print(1)"})
    assert rule_based_check(bundle, {"shell"}).unjustified == ["shell"]
    assert rule_based_check(bundle, set()).ok
