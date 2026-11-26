import io

from rich.console import Console

from skillaudit.models import Finding, Report
from skillaudit.report import print_report, to_markdown


def report_with(evidence: str, message: str = "m") -> Report:
    finding = Finding(file="a.py", line=1, rule="r", severity="HIGH", source="llm",
                      message=message, evidence=evidence)
    return Report(skill_name="x", source="test", files_scanned=1, score=75, verdict="REVIEW",
                  mode="PARTIAL", provider=None, findings=[finding], capabilities=[],
                  consistency_ok=True, unjustified=[], notes=[])


def test_terminal_output_strips_escape_codes():
    out = io.StringIO()
    print_report(report_with("\x1b[2J\x1b[1A erase screen"), Console(file=out, width=120))
    assert "\x1b" not in out.getvalue()
    assert "erase screen" in out.getvalue()


def test_terminal_output_does_not_render_markup_from_skills():
    out = io.StringIO()
    print_report(report_with("[bold red]fake[/bold red]"), Console(file=out, width=120))
    assert "[bold red]fake[/bold red]" in out.getvalue()


def test_markdown_escapes_links_images_and_pipes():
    md = to_markdown(report_with("a | b `c`", message="![img](https://tracker.example/p.png)"))
    assert "![img]" not in md
    assert "\\!\\[img\\]" in md
    assert "`a \\| b 'c'`" in md
