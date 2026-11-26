"""Data models shared by every layer of the scanner."""

from typing import Literal, Optional

from pydantic import BaseModel, Field

Severity = Literal["LOW", "MED", "HIGH"]
Verdict = Literal["SAFE_ISH", "REVIEW", "DO_NOT_INSTALL"]
Mode = Literal["FULL", "PARTIAL"]

SEVERITY_ORDER = {"HIGH": 0, "MED": 1, "LOW": 2}


class SkillFile(BaseModel):
    path: str                          # relative to the skill root, always with "/"
    content: str = ""
    skip_reason: Optional[str] = None  # "binary" or "too_large"; content is empty then

    @property
    def scannable(self) -> bool:
        return self.skip_reason is None


class SkillBundle(BaseModel):
    """Everything we know about one skill after loading it."""

    source: str                        # "paste" | "file:<path>" | "github:<url>"
    files: list[SkillFile]
    partial_input: bool = False        # True when we know we did not see the whole skill
    name: Optional[str] = None         # from SKILL.md frontmatter
    description: Optional[str] = None  # from SKILL.md frontmatter
    notes: list[str] = Field(default_factory=list)

    def scannable_files(self) -> list[SkillFile]:
        return [f for f in self.files if f.scannable]


class Finding(BaseModel):
    file: str
    line: int
    rule: str
    severity: Severity
    source: Literal["static", "llm"]
    message: str
    evidence: str


class Report(BaseModel):
    skill_name: Optional[str]
    source: str
    files_scanned: int
    score: int
    verdict: Verdict
    mode: Mode
    provider: Optional[str]
    findings: list[Finding]
    capabilities: list[str]
    consistency_ok: bool
    unjustified: list[str]
    notes: list[str]
