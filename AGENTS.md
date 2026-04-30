# AGENTS.md

This file is project context for AI coding agents working on `a-memo`.

## Communication

- Use Chinese when talking with the user.
- Lead with the result, then add only the context needed for the next action.
- Keep README focused on users.
- Keep changes small, complete, and consistent with the existing structure.

## Project

`a-memo` is a local memo CLI for notes, tags, search, review, links, backup, import/export, and PNG share images.

- Package: `a-memo`
- Command: `memo`
- Python: `>=3.11`
- Build backend: `hatchling`
- CLI entry: `memo.cli:main`
- Data directory: `~/.memo` by default, override with `MEMO_DATA_DIR`

## Checks

```bash
uv tool run ruff check .
uv tool run ruff format --check .
uv tool run ty check
uv run --extra dev pytest
uv build
```

## Editing Guidelines

- Command modules live in `memo/commands/`.
- Prefer testing behavior through `memo.cli:main`.
- Use `MEMO_DATA_DIR` for tests and manual checks to avoid real user data.
- Update tests when command behavior changes.
- Release instructions live in `.agents/docs/release.md`.

## Data Safety

Treat user memo data as long-lived personal data. Tests and manual checks must use a temporary `MEMO_DATA_DIR`. Writes, imports, deletes, and resets against real data need clear user intent. Bulk or destructive operations need a backup and explicit confirmation.

## References

- User docs: `README.md`
- Command usage: `skills/memo/SKILL.md`
- Release workflow: `.agents/docs/release.md`
