# a-memo

A lightweight memo CLI for quick notes, tags, search, review, links, backup, import/export, and share images.

[![PyPI version](https://img.shields.io/pypi/v/a-memo)](https://pypi.org/project/a-memo/)
[![GitHub](https://img.shields.io/github/license/coderfee/a-memo)](https://github.com/coderfee/a-memo)

## Install

### macOS / Linux binary

Download the right archive from the [latest release](https://github.com/coderfee/a-memo/releases/latest):

- macOS Apple Silicon: `memo-macos-arm64.tar.gz`
- macOS Intel: `memo-macos-x86_64.tar.gz`
- Linux x86_64: `memo-linux-x86_64.tar.gz`

```bash
tar -xzf memo-macos-arm64.tar.gz
chmod +x memo
./memo --version
```

Install it into your PATH:

```bash
mkdir -p ~/.local/bin
mv memo ~/.local/bin/memo
memo --help
```

Add `~/.local/bin` to your PATH:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

### Windows binary

Download `memo-windows-x86_64.zip` from the [latest release](https://github.com/coderfee/a-memo/releases/latest), unzip it, then run:

```powershell
.\memo.exe --version
```

### uv

```bash
uv tool install a-memo
```

Upgrade:

```bash
uv tool upgrade a-memo
```

### pipx

```bash
pipx install a-memo
```

Upgrade:

```bash
pipx upgrade a-memo
```

### pip

```bash
pip install a-memo
```

Upgrade:

```bash
pip install --upgrade a-memo
```

## Share Images

Generate a vertical PNG share image:

```bash
memo image 1
memo image 1 --out share.png
```

Images use a 600px wide vertical card. Tags, text, timestamp, and memo count are rendered into
the PNG directly.

## Usage

```bash
memo add "read later #idea"
memo list
memo list '#idea'
memo search "later"
memo review
memo review --push
memo link 1 2
memo links 1
memo image 1
memo backup
memo export --out memos.json
memo import memos.json
memo flomo-import export.html
```

Show all commands:

```bash
memo --help
memo <command> --help
```

Show version:

```bash
memo --version
```

## Backup And Migration

Create a backup:

```bash
memo backup
memo backup --out ~/Desktop/memo.db
```

Export portable JSON:

```bash
memo export --out memos.json
```

Import JSON:

```bash
memo import memos.json
```

Replace current data with an export:

```bash
memo import memos.json --replace
```

Reset local data:

```bash
memo reset --force
```

## Data Location

`memo` stores local data under:

```text
~/.memo/
```

Use `memo backup` or `memo export` before moving data between machines.

## License

MIT
