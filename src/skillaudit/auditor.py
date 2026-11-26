"""The pipeline: bundle in, report out. The CLI and the tests both call audit()."""

from .capabilities import detect_capabilities
from .consistency import check_consistency
from .models import SEVERITY_ORDER, Report, SkillBundle
from .precheck import run_prechecks
from .rules import run_rules
from .scoring import compute_score


def audit(bundle: SkillBundle) -> Report:
    notes = list(bundle.notes)

    # Static checks: always run, need no key, cost nothing.
    findings = run_prechecks(bundle) + run_rules(bundle)
    capabilities = detect_capabilities(bundle, findings)

    # Does the declared purpose explain what the code does?
    consistency = check_consistency(bundle, capabilities)

    # Pattern checks alone cannot judge intent, so this is never a FULL scan yet.
    mode = "PARTIAL"
    score, verdict = compute_score(findings, consistency.ok, mode)

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line))
    return Report(
        skill_name=bundle.name,
        source=bundle.source,
        files_scanned=len(bundle.scannable_files()),
        score=score,
        verdict=verdict,
        mode=mode,
        provider=None,
        findings=findings,
        capabilities=sorted(capabilities),
        consistency_ok=consistency.ok,
        unjustified=consistency.unjustified,
        notes=notes,
    )
