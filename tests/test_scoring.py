from skillaudit.models import Finding
from skillaudit.scoring import compute_score


def finding(rule="some-rule", severity="MED", file="a.py", source="static"):
    return Finding(file=file, line=1, rule=rule, severity=severity, source=source,
                   message="m", evidence="e")


def test_clean_full_scan_is_safe_ish():
    assert compute_score([], True, "FULL") == (100, "SAFE_ISH")


def test_partial_scan_never_says_safe():
    assert compute_score([], True, "PARTIAL") == (100, "REVIEW")


def test_same_rule_counts_once():
    findings = [finding("url-unknown", "LOW")] * 20
    assert compute_score(findings, True, "FULL")[0] == 97


def test_same_rule_in_many_files_still_counts_once():
    # Regression: a doc-heavy real skill (mcp-builder) was blocked because every
    # reference file repeated process.env.PORT and each file cost 10 points.
    findings = [finding("env-read", file=f"reference/doc{i}.md") for i in range(10)]
    assert compute_score(findings, True, "FULL") == (90, "SAFE_ISH")


def test_rule_uses_its_worst_severity():
    findings = [finding("x", "LOW"), finding("x", "MED")]
    assert compute_score(findings, True, "FULL")[0] == 90


def test_hard_fail_rule_overrides_a_good_score():
    score, verdict = compute_score([finding("pipe-to-shell", "HIGH")], True, "FULL")
    assert score == 75
    assert verdict == "DO_NOT_INSTALL"


def test_static_high_that_is_not_hard_fail_only_costs_points():
    assert compute_score([finding("exfil-post", "HIGH")], True, "FULL") == (75, "REVIEW")


def test_consistency_failure_costs_20():
    assert compute_score([], False, "FULL") == (80, "SAFE_ISH")
    assert compute_score([finding()], False, "FULL") == (70, "REVIEW")


def test_thresholds_and_floor():
    assert compute_score([finding(rule=f"r{i}") for i in range(5)], True, "FULL") == (50, "REVIEW")
    assert compute_score([finding(rule=f"r{i}") for i in range(6)], True, "FULL") == (40, "DO_NOT_INSTALL")
    assert compute_score([finding(rule=f"r{i}", severity="HIGH") for i in range(9)], True, "FULL")[0] == 0


def test_lowered_hard_fail_rule_does_not_block_on_its_own():
    # "Never run curl | sh" in SKILL.md: pipe-to-shell lowered to MED
    assert compute_score([finding("pipe-to-shell", "MED")], True, "FULL") == (90, "SAFE_ISH")
