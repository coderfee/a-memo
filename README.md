# a-memo

A small memo CLI for saving notes, finding them later, reviewing old thoughts, and turning a memo into a share image.

[![PyPI version](https://img.shields.io/pypi/v/a-memo)](https://pypi.org/project/a-memo/)
[![GitHub](https://img.shields.io/github/license/coderfee/a-memo)](https://github.com/coderfee/a-memo)

## For Humans

### Install

Download a standalone binary from the [latest release](https://github.com/coderfee/a-memo/releases/latest).

- macOS Apple Silicon: `memo-macos-arm64.tar.gz`
- macOS Intel: `memo-macos-x86_64.tar.gz`
- Linux x86_64: `memo-linux-x86_64.tar.gz`
- Windows x86_64: `memo-windows-x86_64.zip`

macOS / Linux:

```bash
tar -xzf memo-macos-arm64.tar.gz
chmod +x memo
./memo --version
```

Install into your PATH:

```bash
mkdir -p ~/.local/bin
mv memo ~/.local/bin/memo
memo --help
```

Windows:

```powershell
.\memo.exe --version
```

Python install:

```bash
uv tool install a-memo
```

Other options:

```bash
pipx install a-memo
pip install a-memo
```

### Daily Use

```bash
memo add "read later #idea"
memo show 1
memo list
memo list "#idea"
memo search "later"
memo review
memo review --push
```

### Share Images

```bash
memo image 1
memo image 1 --out share.png
memo image 1 --style ink
```

Styles:

- `paper`: warm reading card, default
- `clean`: minimal white note
- `ink`: stronger blue ink frame

### Backup And Move Data

```bash
memo backup
memo export --out memos.json
memo import memos.json
memo import memos.json --replace
```

Use `memo --help` and `memo <command> --help` for the full command list.

## For Agents

Use `memo` as the user's local memory tool. Treat it as a durable store: inspect first, write only with clear user intent, and verify every write.

Safe read-only commands:

```bash
memo list --limit 20
memo search "keyword"
memo show <id>
memo tags
memo links <id>
memo review --count 5
memo image <id>
memo flomo-import export.html --dry-run
```

Write commands require explicit user intent:

```bash
memo add "content #tag"
memo update <id> "new content #tag"
memo tag <id> "#tag"
memo link <id1> <id2>
memo unlink <id1> <id2>
memo delete <id>
memo review --push
memo import memos.json
```

Risky commands require a backup and explicit confirmation:

```bash
memo import memos.json --replace
memo reset --force
```

Agent workflow:

1. Classify the user request: search, save, edit, tag, link, review, import, export, image, or recovery.
2. Inspect current context with `list`, `search`, `tags`, or `links`.
3. Run the smallest authorized command.
4. Verify the result with a narrow read command.
5. Report memo ids, tags, backup paths, and verification results.

Share image style choice:

- Use `paper` by default.
- Use `clean` when the user wants a plain note.
- Use `ink` when the user wants stronger visual identity.

More detailed agent guidance lives in [skills/memo/SKILL.md](skills/memo/SKILL.md).

Install the Codex skill:

```bash
npx skills add coderfee/a-memo
bunx skills add coderfee/a-memo
pnpx skills add coderfee/a-memo
```

## License

MIT
