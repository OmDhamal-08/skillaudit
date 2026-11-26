"""Turn findings into a 0-100 score and a verdict."""

from .models import Finding

PENALTY = {"HIGH": 25, "MED": 10, "LOW": 3}
CONSISTENCY_PENALTY = 20

# Rules with no legitimate use in a skill. One HIGH hit is enough for
# DO_NOT_INSTALL, whatever the score. exfil-post is not here: a Slack or webhook
# skill has to POST, so we let the consistency check decide whether that is expected.
# A hard-fail rule that was lowered (for example "never run curl | sh" in a doc)
# is no longer HIGH, so it no longer blocks on its own.
HARD_FAIL = {
    "pipe-to-shell", "pipe-to-shell-ps", "secret-file", "persistence",
    "invisible-text", "inject-phrase",
}

SAFE_THRESHOLD = 80
REVIEW_THRESHOLD = 50


def compute_score(findings: list[Finding], consistency_ok: bool, mode: str) -> tuple[int, str]:
    # Each kind of risk costs points once per skill. We first deduped per
    # (rule, file), but then a skill with ten reference docs that all mention
    # process.env.PORT lost ten times the points of a one-file skill. The score
    # should reflect what a skill does, not how much documentation it has.
    worst: dict[str, str] = {}
    for f in findings:
        if f.rule not in worst or PENALTY[f.severity] > PENALTY[worst[f.rule]]:
            worst[f.rule] = f.severity
    total = sum(PENALTY[severity] for severity in worst.values())
    if not consistency_ok:
        total += CONSISTENCY_PENALTY
    score = max(0, 100 - total)

    hard_fail = any(f.severity == "HIGH" and f.rule in HARD_FAIL for f in findings)

    if hard_fail or score < REVIEW_THRESHOLD:
        verdict = "DO_NOT_INSTALL"
    elif score < SAFE_THRESHOLD:
        verdict = "REVIEW"
    else:
        # Without the full picture we never say "safe".
        verdict = "SAFE_ISH" if mode == "FULL" else "REVIEW"
    return score, verdict
