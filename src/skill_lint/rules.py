"""Lint rules for skill files.

Each rule is a callable ``(skill, findings) -> None`` that appends
:class:`~skill_lint.models.Finding` objects. Keeping rules independent makes
them easy to test and extend.
"""

from __future__ import annotations

import re
from typing import List

from .models import Finding, Severity, Skill

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
H1_RE = re.compile(r"^#\s+\S", re.MULTILINE)

DESCRIPTION_MIN = 20
DESCRIPTION_MAX = 1024
BODY_MAX_LINES = 500
# Cues that signal *when* a skill should trigger. Agents route on the
# description, so a description without any of these is likely to misfire.
# Kept multilingual because skill libraries are frequently non-English.
TRIGGER_HINTS = (
    # English
    "use when",
    "use this",
    "use for",
    "when the user",
    "when you",
    "trigger",
    "helps you",
    # Chinese
    "使用",
    "当需要",
    "当用户",
    "触发",
    "用于",
    "用来",
)


def _add(
    findings: List[Finding],
    rule: str,
    severity: Severity,
    message: str,
    skill: Skill,
    line: int | None = None,
) -> None:
    findings.append(
        Finding(rule=rule, severity=severity, message=message, path=skill.path, line=line)
    )


def rule_frontmatter(skill: Skill, findings: List[Finding]) -> None:
    if skill.kind != "skill":
        return
    if skill.frontmatter_error:
        _add(findings, "frontmatter", Severity.ERROR, skill.frontmatter_error, skill, 1)
        return
    if skill.frontmatter is None:
        _add(
            findings,
            "frontmatter",
            Severity.ERROR,
            "SKILL.md is missing a YAML frontmatter block (--- ... ---) at the top",
            skill,
            1,
        )


def rule_name(skill: Skill, findings: List[Finding]) -> None:
    if skill.kind != "skill" or not skill.frontmatter:
        return
    name = skill.frontmatter.get("name")
    if not name:
        _add(findings, "name", Severity.ERROR, "frontmatter is missing required field: name", skill, 1)
        return
    if not isinstance(name, str) or not NAME_RE.match(name):
        _add(
            findings,
            "name-format",
            Severity.WARNING,
            f"name '{name}' should be lowercase words separated by hyphens (e.g. my-skill)",
            skill,
            1,
        )
        return
    dirname = skill.directory.name
    if dirname and name != dirname:
        _add(
            findings,
            "name-matches-dir",
            Severity.WARNING,
            f"name '{name}' does not match its directory '{dirname}'",
            skill,
            1,
        )


def rule_description(skill: Skill, findings: List[Finding]) -> None:
    if skill.kind != "skill" or not skill.frontmatter:
        return
    desc = skill.frontmatter.get("description")
    if not desc:
        _add(
            findings,
            "description",
            Severity.ERROR,
            "frontmatter is missing required field: description",
            skill,
            1,
        )
        return
    if not isinstance(desc, str):
        _add(findings, "description", Severity.ERROR, "description must be a string", skill, 1)
        return

    length = len(desc.strip())
    if length < DESCRIPTION_MIN:
        _add(
            findings,
            "description-length",
            Severity.WARNING,
            f"description is very short ({length} chars); say what it does and when to use it",
            skill,
            1,
        )
    elif length > DESCRIPTION_MAX:
        _add(
            findings,
            "description-length",
            Severity.WARNING,
            f"description is very long ({length} chars > {DESCRIPTION_MAX}); consider trimming",
            skill,
            1,
        )

    if not any(hint in desc.lower() for hint in TRIGGER_HINTS):
        _add(
            findings,
            "description-triggers",
            Severity.WARNING,
            "description has no clear trigger cue (e.g. 'Use when ...'); agents route on the description",
            skill,
            1,
        )


def rule_title(skill: Skill, findings: List[Finding]) -> None:
    if skill.kind != "skill":
        return
    if not H1_RE.search(skill.body):
        _add(
            findings,
            "title",
            Severity.WARNING,
            "body has no H1 title (e.g. '# My Skill')",
            skill,
            skill.body_start_line,
        )


def rule_body_size(skill: Skill, findings: List[Finding]) -> None:
    if not skill.body.strip():
        return
    lines = skill.body.count("\n") + 1
    if lines > BODY_MAX_LINES:
        _add(
            findings,
            "body-size",
            Severity.WARNING,
            f"body is large ({lines} lines > {BODY_MAX_LINES}); move detail into references/",
            skill,
        )


def rule_broken_references(skill: Skill, findings: List[Finding]) -> None:
    base = skill.directory
    seen: set[str] = set()
    for match in LINK_RE.finditer(skill.raw):
        target = match.group(1).strip()
        if not target or target.startswith(("http://", "https://", "#", "mailto:", "tel:", "<")):
            continue
        target_path = target.split("#", 1)[0].split("?", 1)[0].strip()
        if not target_path or target_path in seen:
            continue
        seen.add(target_path)
        if not (base / target_path).exists():
            _add(
                findings,
                "broken-reference",
                Severity.ERROR,
                f"referenced file not found: {target_path}",
                skill,
            )


def rule_agents_nonempty(skill: Skill, findings: List[Finding]) -> None:
    if skill.kind != "agents":
        return
    if len(skill.raw.strip()) < 40:
        _add(
            findings,
            "agents-empty",
            Severity.WARNING,
            "AGENTS.md looks thin; add a repo map, build/test commands, and conventions",
            skill,
            1,
        )


ALL_RULES = (
    rule_frontmatter,
    rule_name,
    rule_description,
    rule_title,
    rule_body_size,
    rule_broken_references,
    rule_agents_nonempty,
)


def run_rules(skill: Skill) -> List[Finding]:
    findings: List[Finding] = []
    for rule in ALL_RULES:
        rule(skill, findings)
    findings.sort(key=lambda f: (f.line or 0, f.rule))
    return findings
