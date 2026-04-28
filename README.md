# memo-cli

A lightweight memo CLI tool with SQLite + FTS5, supporting tags, links, review, and share image generation.

## Install

```bash
pip install memo-cli
```

Or with uv:

```bash
uv tool install memo-cli
```

## Usage

```bash
memo add "content" #tag           # add memo
memo list                            # list all memos
memo search "keyword"                # full-text search
memo review --push                    # spaced repetition review
memo image 1                         # generate share image (PNG)
memo link 1 2                        # link two memos
memo flomo-import export.html        # import from flomo
```

## Data

Data stored at `~/.memo/`:
- `memo.db` - SQLite database
- `images/` - share images
- `history/` - review history

## Options

```bash
memo --help              # show all commands
memo --version           # show version
memo list #tag            # filter by tag
memo list --limit 20      # limit results
```

## Share Images

Default format is PNG (requires Playwright + Chrome).
SVG is always available:

```bash
memo image 1 --format svg
```

## License

MIT