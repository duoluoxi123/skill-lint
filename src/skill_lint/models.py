"""Core data structures shared across skill-lint."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"


@dataclass
class Finding:
    """A single lint result for a file."""

    rule: str
    severity: Severity
    message: str
    path: Path
    line: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "rule": self.rule,
            "severity": self.severity.value,
            "message": self.message,
            "path": str(self.path),
            "line": self.line,
        }


@dataclass
class Skill:
    """A parsed SKILL.md or AGENTS.md document."""

    path: Path
    directory: Path
    kind: str  # "skill" or "agents"
    raw: str
    body: str
    frontmatter: Optional[dict] = None
    frontmatter_error: Optional[str] = None
    body_start_line: int = 1

    @property
    def name(self) -> Optional[str]:
        if self.frontmatter:
            value = self.frontmatter.get("name")
            return value if isinstance(value, str) else None
        return None
