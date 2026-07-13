"""YAML frontmatter parsing for Markdown skill files."""

from __future__ import annotations

from typing import Optional, Tuple

import yaml

_DELIMITERS = {"---", "..."}


def split_frontmatter(text: str) -> Tuple[Optional[str], str, int]:
    """Split ``text`` into (frontmatter_text, body, body_start_line).

    ``frontmatter_text`` is ``None`` when no valid frontmatter block is found.
    ``body_start_line`` is the 1-based line where the body begins.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 1

    for i in range(1, len(lines)):
        if lines[i].strip() in _DELIMITERS:
            fm = "\n".join(lines[1:i])
            body = "\n".join(lines[i + 1 :])
            return fm, body, i + 2

    # Opening delimiter without a closing one -> treat as no frontmatter.
    return None, text, 1


def parse_frontmatter(
    text: str,
) -> Tuple[Optional[dict], str, int, Optional[str]]:
    """Parse frontmatter, returning (data, body, body_start_line, error).

    ``data`` is ``None`` when no frontmatter block exists. On YAML errors,
    ``data`` is an empty dict and ``error`` describes the problem.
    """
    fm_text, body, body_start = split_frontmatter(text)
    if fm_text is None:
        return None, body, body_start, None

    try:
        data = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:  # pragma: no cover - message varies by input
        return {}, body, body_start, f"invalid YAML frontmatter: {exc}"

    if data is None:
        return {}, body, body_start, None
    if not isinstance(data, dict):
        return {}, body, body_start, "frontmatter must be a YAML mapping"
    return data, body, body_start, None
