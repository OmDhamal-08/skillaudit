"""Machine-readable output. The shape is exactly the Report model."""

from ..models import Report


def to_json(report: Report) -> str:
    return report.model_dump_json(indent=2)
