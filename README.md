# a-memo

A small memo CLI for saving notes, finding them later, reviewing old thoughts, linking related memos, and turning a memo into a PNG share image.

[![PyPI version](https://img.shields.io/pypi/v/a-memo)](https://pypi.org/project/a-memo/)
[![GitHub](https://img.shields.io/github/license/coderfee/a-memo)](https://github.com/coderfee/a-memo)

## Install

CLI:

```bash
brew install coderfee/tap/a-memo
```

Other options:

```bash
uv tool install a-memo
```

Agents skill:

```bash
npx skills add coderfee/a-memo
bunx skills add coderfee/a-memo
pnpx skills add coderfee/a-memo
```

Standalone binaries are available from the [latest release](https://github.com/coderfee/a-memo/releases/latest).

## Usage

```bash
memo add "read later #idea"
memo list
memo list "#idea"
memo show 1
memo search "later"
memo review
```

More commands:

```bash
memo tags
memo link 1 2
memo links 1
memo image 1 --style ink
memo backup
memo export --out memos.json
memo import memos.json
```

Use `memo --help` and `memo <command> --help` for the full command list.

## Development

Checks:

```bash
uv tool run ruff check .
uv tool run ruff format --check .
uv tool run ty check
uv run --extra dev pytest
uv build
```

Project docs:

- Agent instructions: [AGENTS.md](AGENTS.md)
- Memo command guidance: [skills/memo/SKILL.md](skills/memo/SKILL.md)
- Release workflow: [.agents/docs/release.md](.agents/docs/release.md)

## License

MIT
