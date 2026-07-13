# AGENTS.md

Guidance for coding agents (Codex, Claude, Cursor, ...) working in this repo.

## What this project is

`skill-lint` is a CLI that validates agent `SKILL.md` and `AGENTS.md` files. It
is small, dependency-light (only `PyYAML`), and pure Python.

## Repo map

- `src/skill_lint/frontmatter.py` — splits and parses YAML frontmatter.
- `src/skill_lint/models.py` — `Skill`, `Finding`, `Severity` data types.
- `src/skill_lint/rules.py` — one `rule_*` function per check; registered in `ALL_RULES`.
- `src/skill_lint/linter.py` — file discovery + orchestration.
- `src/skill_lint/cli.py` — argument parsing and `text` / `json` reporters.
- `tests/` — pytest suite; every rule has a test.

## Build, run, and test

```bash
pip install -e ".[dev]"   # install with dev extras
pytest                    # run the test suite
skill-lint .              # dogfood: lint this repo
```

## Conventions

- Read a file before editing it; keep changes minimal and focused.
- **Every new rule needs a test.** A rule is a `rule_*(skill, findings)`
  function that appends `Finding` objects and is added to `ALL_RULES`.
- Prefer `warning` for style/quality; reserve `error` for things that break an
  agent run (missing frontmatter/name/description, broken references).
- Keep runtime dependencies to a minimum. Do not add heavy deps.
- Public behaviour changes must update `README.md` (the rules table) too.

## Verification checklist (run before finishing)

1. `pytest` passes.
2. `skill-lint .` reports no new errors on this repo.
3. `README.md` rules table matches `ALL_RULES`.
