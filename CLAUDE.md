# a-memo

Lightweight memo CLI tool for quick notes, tags, search, review, links, backup,
import/export, and PNG share images.

## Install

```bash
uv tool install -e .    # dev mode
uv tool install .       # install
```

## Data

- Default: `~/.memo/memo.db`
- `MEMO_DB_PATH=...` overrides db path
- `MEMO_DATA_DIR=...` overrides data directory

## Commands

```bash
memo add "content" #tag
memo list
memo search "keyword"
memo review --push
memo image 1
memo flomo-import export.html
memo --help
```

## Share Images

`memo image <id>` generates a vertical PNG share card. The base install includes image
generation.
