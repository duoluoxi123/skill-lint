"""Tests for skill-lint."""

from __future__ import annotations

from pathlib import Path

from skill_lint.cli import format_json, main
from skill_lint.frontmatter import parse_frontmatter
from skill_lint.linter import lint_paths
from skill_lint.models import Severity

GOOD_SKILL = """---
name: my-skill
description: Use this skill when the user wants to do X. It does X reliably and returns Y.
---

# My Skill

Body content here.
"""


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _rules(findings) -> set:
    return {finding.rule for finding in findings}


def _errors(findings) -> list:
    return [f for f in findings if f.severity == Severity.ERROR]


def test_good_skill_has_no_errors(tmp_path: Path) -> None:
    _write(tmp_path / "my-skill" / "SKILL.md", GOOD_SKILL)
    results = lint_paths([tmp_path])
    assert len(results) == 1
    _skill, findings = results[0]
    assert _errors(findings) == []


def test_missing_frontmatter_is_error(tmp_path: Path) -> None:
    _write(tmp_path / "bad" / "SKILL.md", "# no frontmatter\n")
    _skill, findings = lint_paths([tmp_path])[0]
    assert "frontmatter" in _rules(findings)


def test_missing_description_is_error(tmp_path: Path) -> None:
    _write(tmp_path / "nodesc" / "SKILL.md", "---\nname: nodesc\n---\n# Title\n")
    _skill, findings = lint_paths([tmp_path])[0]
    assert "description" in _rules(findings)
    assert _errors(findings)


def test_name_directory_mismatch_warns(tmp_path: Path) -> None:
    body = (
        "---\nname: other-name\n"
        "description: use when you want to verify the name/dir mismatch rule works here\n"
        "---\n# Title\n"
    )
    _write(tmp_path / "folder-a" / "SKILL.md", body)
    _skill, findings = lint_paths([tmp_path])[0]
    assert "name-matches-dir" in _rules(findings)


def test_broken_reference_is_error(tmp_path: Path) -> None:
    body = (
        "---\nname: refs\n"
        "description: use when you want to verify broken relative references are detected here\n"
        "---\n# Title\n\nSee [helper](scripts/missing.py).\n"
    )
    _write(tmp_path / "refs" / "SKILL.md", body)
    _skill, findings = lint_paths([tmp_path])[0]
    assert "broken-reference" in _rules(findings)


def test_existing_reference_ok(tmp_path: Path) -> None:
    skill_dir = tmp_path / "refs2"
    _write(skill_dir / "scripts" / "run.py", "print('ok')\n")
    body = (
        "---\nname: refs2\n"
        "description: use when you want to verify existing references pass the linter here\n"
        "---\n# Title\n\nSee [helper](scripts/run.py).\n"
    )
    _write(skill_dir / "SKILL.md", body)
    _skill, findings = lint_paths([tmp_path])[0]
    assert "broken-reference" not in _rules(findings)


def test_thin_agents_warns(tmp_path: Path) -> None:
    _write(tmp_path / "AGENTS.md", "# hi\n")
    _skill, findings = lint_paths([tmp_path])[0]
    assert "agents-empty" in _rules(findings)


def test_frontmatter_parsing() -> None:
    data, body, start, error = parse_frontmatter(GOOD_SKILL)
    assert error is None
    assert data["name"] == "my-skill"
    assert body.strip().startswith("# My Skill")
    assert start > 1


def test_json_output_shape(tmp_path: Path) -> None:
    _write(tmp_path / "my-skill" / "SKILL.md", GOOD_SKILL)
    results = lint_paths([tmp_path])
    import json

    payload = json.loads(format_json(results))
    assert payload["summary"]["files"] == 1
    assert payload["files"][0]["name"] == "my-skill"


def test_cli_returns_error_code_on_errors(tmp_path: Path) -> None:
    _write(tmp_path / "bad" / "SKILL.md", "# no frontmatter\n")
    assert main([str(tmp_path)]) == 1


def test_cli_returns_zero_on_clean(tmp_path: Path) -> None:
    _write(tmp_path / "my-skill" / "SKILL.md", GOOD_SKILL)
    assert main([str(tmp_path), "--no-color"]) == 0
