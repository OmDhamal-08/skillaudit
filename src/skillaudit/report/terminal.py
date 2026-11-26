"""Coloured terminal report using rich."""

import re

from rich.console import Console
from rich.markup import escape
from rich.table import Table

from ..models import Report

SEVERITY_STYLE = {"HIGH": "bold red", "MED": "yellow", "LOW": "cyan"}
VERDICT_STYLE = {
    "DO_NOT_INSTALL": "bold white on red",
    "REVIEW": "bold black on yellow",
    "SAFE_ISH": "bold white on green",
}
VERDICT_LABEL = {"DO_NOT_INSTALL": "DO NOT INSTALL", "REVIEW": "REVIEW", "SAFE_ISH": "SAFE-ISH"}

# Everything except tab and newline. A skill could hide ANSI escape codes in a
# line to rewrite our output (for example erase the HIGH findings).
CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def safe(text: str) -> str:
    """Make untrusted text printable: no control codes, no rich markup."""
    return escape(CONTROL_CHARS.sub("?", text))


def print_report(report: Report, console: Console | None = None) -> None:
    console = console or Console()
    mode = report.mode + (f" ({report.provider})" if report.provider else "")
    console.print(f"[bold]skillaudit[/]  {safe(report.skill_name or '(unnamed skill)')}"
                  f"    mode: {mode}")
    console.print(f"[dim]{safe(report.source)}  |  {report.files_scanned} file(s) scanned[/]")
    console.rule()

    if report.findings:
        console.print(_findings_table(report))
    else:
        console.print("No findings.")

    if report.consistency_ok:
        console.print("Consistency: [green]OK[/]")
    else:
        console.print(f"Consistency: [red]FAIL[/], unjustified: {safe(', '.join(report.unjustified))}")
    if report.capabilities:
        console.print(f"[dim]Capabilities: {', '.join(report.capabilities)}[/]")
    for note in report.notes:
        console.print(f"[dim]note: {safe(note)}[/]")

    console.rule()
    style = VERDICT_STYLE[report.verdict]
    console.print(f"Score: [bold]{report.score}/100[/]   Verdict: "
                  f"[{style}] {VERDICT_LABEL[report.verdict]} [/]")


def _findings_table(report: Report) -> Table:
    table = Table(box=None, pad_edge=False, header_style="bold")
    for column in ("Sev", "Location", "Rule", "Finding", "Src"):
        table.add_column(column)
    for f in report.findings:
        evidence = f.evidence if len(f.evidence) <= 120 else f.evidence[:117] + "..."
        table.add_row(
            f"[{SEVERITY_STYLE[f.severity]}]{f.severity}[/]",
            safe(f"{f.file}:{f.line}"),
            safe(f.rule),
            f"{safe(f.message)}\n[dim]{safe(evidence)}[/]",
            f.source,
        )
    return table
