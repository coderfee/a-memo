# a-memo

A lightweight memo CLI tool for AI agents with SQLite + FTS5, supporting tags, links, review, and share image generation.

[![PyPI version](https://img.shields.io/pypi/v/a-memo)](https://pypi.org/project/a-memo/)
[![GitHub](https://img.shields.io/github/license/coderfee/a-memo)](https://github.com/coderfee/a-memo)

## Install

```bash
uv tool install a-memo
```

PNG share images need the optional Playwright dependency:

```bash
uv tool install "a-memo[png]"
uv tool run playwright install chromium
```

If `a-memo` is already installed without the PNG extra:

```bash
uv tool install --force "a-memo[png]"
```

pip also works:

```bash
pip install a-memo
pip install "a-memo[png]"
```

## Usage

```bash
memo add "content" #tag           # add memo
memo list                            # list all memos
memo search "keyword"                # full-text search
memo review --push                    # spaced repetition review
memo image 1                         # generate share image (PNG)
memo link 1 2                        # link two memos
memo backup                          # backup SQLite database
memo export --out memos.json         # export JSON
memo import memos.json               # import JSON
memo flomo-import export.html        # import from flomo
```

## Data

Data stored at `~/.memo/`:

- `memo.db` - SQLite database
- `images/` - share images
- `history/` - review history
- `backups/` - manual backups

The database uses SQLite `PRAGMA user_version` migrations. New versions upgrade the schema
automatically when `memo` opens the database.

## Backup And Portability

Create a SQLite backup:

```bash
memo backup
memo backup --out ~/Desktop/memo.db
```

Export portable JSON:

```bash
memo export --out memos.json
```

Import JSON into the current database:

```bash
memo import memos.json
```

Replace the current database content with an export. A backup is created first:

```bash
memo import memos.json --replace
```

Reset deletes the data directory and creates a database backup first:

```bash
memo reset --force
```

## Options

```bash
memo --help              # show all commands
memo --version           # show version
memo list #tag            # filter by tag
memo list --limit 20      # limit results
```

## Share Images

SVG is always available:

```bash
memo image 1 --format svg
```

PNG requires the `png` extra and a Chromium-compatible browser:

```bash
uv tool install "a-memo[png]"
uv tool run playwright install chromium
memo image 1 --format png
```

If Chrome or Chromium is already installed on the system, `memo image` can use it directly.

## Development

```bash
uv sync --extra dev
uv run --extra dev pytest
uv tool run ruff check .
uv tool run ruff format --check .
uv tool run ty check
```

PNG development needs the optional dependency:

```bash
uv sync --extra dev --extra png
uv run playwright install chromium
uv run memo image 1 --format png
```

Before committing, run the same checks as the git hook:

```bash
.githooks/pre-commit
```

## License

MIT
