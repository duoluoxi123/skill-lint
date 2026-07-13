# skill-lint

[![CI](https://github.com/duoluoxi123/skill-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/duoluoxi123/skill-lint/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/skill-lint.svg)](https://pypi.org/project/skill-lint/)
[![Python](https://img.shields.io/pypi/pyversions/skill-lint.svg)](https://pypi.org/project/skill-lint/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A fast, dependency-light linter and validator for **agent Skills** (`SKILL.md`)
and **`AGENTS.md`** files.

As Codex, Claude, Cursor and other coding agents converge on the
[agent skills](https://developers.openai.com/codex/skills) and `AGENTS.md`
conventions, teams accumulate dozens of skill folders. A malformed frontmatter,
a missing `description`, a skill that will never trigger, or a broken
`references/` link silently degrades agent behaviour. `skill-lint` catches these
problems in your editor and in CI — before they cost you an agent run.

## Install

```bash
pip install skill-lint
```

## Usage

Lint the current directory (recursively finds every `SKILL.md` and `AGENTS.md`):

```bash
skill-lint
```

Lint specific paths, emit JSON, or fail CI on warnings:

```bash
skill-lint .agents/skills
skill-lint --format json
skill-lint --strict          # warnings become non-zero exit
skill-lint --no-agents       # only SKILL.md files
```

Example output:

```
.agents/skills/deploy/SKILL.md
  error [description] frontmatter is missing required field: description
  warning [name-matches-dir] name 'deployer' does not match its directory 'deploy'

Checked 12 file(s): 1 error(s), 1 warning(s), 10 clean.
```

`skill-lint` exits `1` when any error is found (or any warning with `--strict`),
so it drops straight into a pre-commit hook or CI job.

## Rules

| Rule | Severity | What it checks |
| --- | --- | --- |
| `frontmatter` | error | `SKILL.md` has a valid YAML frontmatter block |
| `name` | error | frontmatter has a `name` |
| `name-format` | warning | `name` is `lowercase-hyphenated` |
| `name-matches-dir` | warning | `name` matches the skill's directory |
| `description` | error | frontmatter has a `description` |
| `description-length` | warning | `description` is neither too short nor too long |
| `description-triggers` | warning | `description` includes a trigger cue (agents route on it) |
| `title` | warning | body has an H1 title |
| `body-size` | warning | body stays small (keep detail in `references/`) |
| `broken-reference` | error | relative links resolve to real files |
| `agents-empty` | warning | `AGENTS.md` is not empty/thin |

## Use in CI

```yaml
# .github/workflows/skills.yml
name: skills
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install skill-lint
      - run: skill-lint .
```

## Development

```bash
pip install -e ".[dev]"
pytest
skill-lint .          # skill-lint lints its own AGENTS.md
```

## Contributing

Issues and PRs are welcome. Adding a rule is intentionally small: write a
`rule_*` function in `src/skill_lint/rules.py`, register it in `ALL_RULES`, and
add a test. See [AGENTS.md](AGENTS.md) for the repo map and conventions.

## License

[MIT](LICENSE)
