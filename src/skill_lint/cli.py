"""Command-line interface for skill-lint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from . import __version__
from .linter import Result, lint_paths
from .models import Severity


def _color(code: str, text: str, enable: bool) -> str:
    return f"\033[{code}m{text}\033[0m" if enable else text


def _supports_color(stream) -> bool:
    return bool(getattr(stream, "isatty", lambda: False)())


def _counts(results: List[Result]) -> Tuple[int, int, int]:
    errors = warnings = clean = 0
    for _skill, findings in results:
        if not findings:
            clean += 1
        for finding in findings:
            if finding.severity == Severity.ERROR:
                errors += 1
            else:
                warnings += 1
    return errors, warnings, clean


def format_text(results: List[Result], use_color: bool) -> str:
    lines: List[str] = []
    for skill, findings in results:
        if not findings:
            continue
        lines.append(_color("1", str(skill.path), use_color))
        for finding in findings:
            if finding.severity == Severity.ERROR:
                tag = _color("31", "error", use_color)
            else:
                tag = _color("33", "warning", use_color)
            loc = f" (line {finding.line})" if finding.line else ""
            lines.append(f"  {tag} [{finding.rule}] {finding.message}{loc}")
        lines.append("")

    errors, warnings, clean = _counts(results)
    summary = (
        f"Checked {len(results)} file(s): "
        f"{errors} error(s), {warnings} warning(s), {clean} clean."
    )
    if errors == 0 and warnings == 0:
        summary = _color("32", summary, use_color)
    elif errors:
        summary = _color("31", summary, use_color)
    lines.append(summary)
    return "\n".join(lines)


def format_json(results: List[Result]) -> str:
    errors, warnings, _clean = _counts(results)
    payload = {
        "files": [
            {
                "path": str(skill.path),
                "kind": skill.kind,
                "name": skill.name,
                "findings": [finding.to_dict() for finding in findings],
            }
            for skill, findings in results
        ],
        "summary": {"files": len(results), "errors": errors, "warnings": warnings},
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skill-lint",
        description="Lint agent Skills (SKILL.md) and AGENTS.md files.",
    )
    parser.add_argument("paths", nargs="*", help="files or directories to lint (default: .)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument(
        "--strict", action="store_true", help="treat warnings as errors (non-zero exit)"
    )
    parser.add_argument("--no-agents", action="store_true", help="skip AGENTS.md files")
    parser.add_argument("--no-color", action="store_true", help="disable colored output")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    paths = [Path(p) for p in (args.paths or ["."])]

    results = lint_paths(paths, include_agents=not args.no_agents)

    if not results:
        print("No SKILL.md or AGENTS.md files found.", file=sys.stderr)
        return 0

    if args.format == "json":
        print(format_json(results))
    else:
        use_color = not args.no_color and _supports_color(sys.stdout)
        print(format_text(results, use_color))

    errors, warnings, _clean = _counts(results)
    if errors or (args.strict and warnings):
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
