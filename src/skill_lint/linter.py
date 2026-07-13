"""Discovery and orchestration for skill-lint."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Tuple

from .models import Skill
from .frontmatter import parse_frontmatter
from .rules import run_rules

SKILL_FILENAME = "SKILL.MD"
AGENTS_FILENAME = "AGENTS.MD"
IGNORE_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
}

Result = Tuple[Skill, List]


def _wanted(include_agents: bool) -> set[str]:
    wanted = {SKILL_FILENAME}
    if include_agents:
        wanted.add(AGENTS_FILENAME)
    return wanted


def load_skill(path: Path) -> Skill:
    raw = path.read_text(encoding="utf-8", errors="replace")
    kind = "skill" if path.name.upper() == SKILL_FILENAME else "agents"
    frontmatter, body, body_start, error = parse_frontmatter(raw)
    return Skill(
        path=path,
        directory=path.parent,
        kind=kind,
        raw=raw,
        body=body,
        frontmatter=frontmatter,
        frontmatter_error=error,
        body_start_line=body_start,
    )


def discover(paths: Iterable[Path], include_agents: bool = True) -> List[Path]:
    wanted = _wanted(include_agents)
    found: List[Path] = []
    seen: set[Path] = set()

    for base in paths:
        base = Path(base)
        candidates: Iterable[Path]
        if base.is_file():
            candidates = [base] if base.name.upper() in wanted else []
        elif base.is_dir():
            candidates = (
                p
                for p in base.rglob("*.md")
                if p.name.upper() in wanted
                and not any(part in IGNORE_DIRS for part in p.parts)
            )
        else:
            candidates = []

        for candidate in candidates:
            resolved = candidate.resolve()
            if resolved not in seen:
                seen.add(resolved)
                found.append(candidate)

    found.sort(key=lambda p: str(p).lower())
    return found


def lint_paths(paths: Iterable[Path], include_agents: bool = True) -> List[Result]:
    results: List[Result] = []
    for file in discover(paths, include_agents=include_agents):
        skill = load_skill(file)
        results.append((skill, run_rules(skill)))
    return results
