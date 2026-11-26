"""Markdown report, used as a GitHub PR comment by the Action."""

import re

from ..models import Report
from .terminal import VERDICT_LABEL

# Everything that could turn untrusted text into a link, image, HTML or a
# broken table. An attacker controls skill content and, indirectly, LLM messages.
MD_SPECIAL = re.compile(r"([\\`*_\[\]<>|!#~])")


def escape_md(text: str) -> str:
    return MD_SPECIAL.sub(r"\\\1", " ".join(text.split()))


def code(text: str) -> str:
    # Inside a code span nothing is rendered, but a backtick would end it early.
    return "`" + " ".join(text.split()).replace("`", "'").replace("|", "\\|") + "`"


def to_markdown(report: Report) -> str:
    name = escape_md(report.skill_name or "unnamed skill")
    mode = report.mode + (f" ({report.provider})" if report.provider else "")
    out = [
        f"### skillaudit: {name} - **{VERDICT_LABEL[report.verdict]}** ({report.score}/100)",
        "",
        f"Mode: {mode} | Files scanned: {report.files_scanned} | Source: {code(report.source)}",
        "",
    ]

    if report.findings:
        out += ["| Severity | Location | Rule | Finding | Evidence | Source |",
                "|---|---|---|---|---|---|"]
        for f in report.findings:
            out.append(f"| {f.severity} | {code(f'{f.file}:{f.line}')} | {code(f.rule)} "
                       f"| {escape_md(f.message)} | {code(f.evidence[:120])} | {f.source} |")
    else:
        out.append("No findings.")
    out.append("")

    if report.consistency_ok:
        out.append("**Consistency:** OK")
    else:
        out.append(f"**Consistency:** FAIL, unjustified: {escape_md(', '.join(report.unjustified))}")

    if report.notes:
        out += ["", "<details><summary>Notes</summary>", ""]
        out += [f"- {escape_md(note)}" for note in report.notes]
        out += ["", "</details>"]
    out.append("")
    return "\n".join(out)
