"""Command line entry point: `skillaudit <target> [options]`."""

import sys
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.markup import escape

from . import __version__
from .auditor import audit
from .loaders import LoaderError, load_target
from .report import print_report, to_json, to_markdown

app = typer.Typer(add_completion=False,
                  help="Audit a Claude skill for risky behaviour before installing it.")
stderr = Console(stderr=True)


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"skillaudit {__version__}")
        raise typer.Exit()


@app.command()
def main(
    target: Annotated[str, typer.Argument(
        help="Skill folder, SKILL.md file, GitHub URL, or '-' to read from stdin.")],
    as_json: Annotated[bool, typer.Option("--json", help="Print the report as JSON.")] = False,
    as_markdown: Annotated[bool, typer.Option(
        "--markdown", help="Print the report as markdown (for PR comments).")] = False,
    fail_under: Annotated[Optional[int], typer.Option(
        "--fail-under", help="Exit with code 1 if the score is below this, or the verdict is DO_NOT_INSTALL.")] = None,
    stdin_name: Annotated[Optional[str], typer.Option(
        "--stdin-name", help="File name for stdin input, e.g. setup.sh. Default: guessed.")] = None,
    version: Annotated[bool, typer.Option(
        "--version", callback=_show_version, is_eager=True, help="Show the version and exit.")] = False,
) -> None:
    """Audit a Claude skill before installing it."""
    if as_json and as_markdown:
        _fail("Use either --json or --markdown, not both.")

    stdin_text = _read_stdin() if target == "-" else None
    try:
        bundle = load_target(target, stdin_text, stdin_name)
    except LoaderError as exc:
        _fail(str(exc))

    report = audit(bundle)

    if as_json:
        typer.echo(to_json(report))
    elif as_markdown:
        typer.echo(to_markdown(report))
    else:
        print_report(report)

    # A hard-fail finding can leave the score above the threshold, so the
    # verdict has to fail the build on its own too.
    if fail_under is not None and (report.score < fail_under or report.verdict == "DO_NOT_INSTALL"):
        raise typer.Exit(code=1)


def _read_stdin() -> str:
    # Read bytes and decode ourselves: on Windows a piped stdin is not always UTF-8.
    return sys.stdin.buffer.read().decode("utf-8-sig", errors="replace")


def _fail(message: str) -> None:
    stderr.print(f"[red]error:[/] {escape(message)}")
    raise typer.Exit(code=2)
