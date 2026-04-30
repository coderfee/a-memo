# a-memo

A small memo CLI for saving notes, finding them later, reviewing old thoughts, linking related memos, and turning a memo into a PNG share image.

[![PyPI version](https://img.shields.io/pypi/v/a-memo)](https://pypi.org/project/a-memo/)
[![GitHub](https://img.shields.io/github/license/coderfee/a-memo)](https://github.com/coderfee/a-memo)

## For Humans

### Install

```bash
brew install coderfee/tap/a-memo
```

Other options:

```bash
uv tool install a-memo
```

Standalone binaries are available from the [latest release](https://github.com/coderfee/a-memo/releases/latest).

### Use

```bash
memo add "read later #idea"
memo list
memo show 1
memo search "later"
memo review
```

Tags:

```bash
memo list "#idea"
memo tags
memo tag 1 "#idea/reading"
```

Links:

```bash
memo link 1 2
memo links 1
memo show 1 --links
```

Share image:

```bash
memo image 1
memo image 1 --out share.png
memo image 1 --style ink
```

Backup and move data:

```bash
memo backup
memo export --out memos.json
memo import memos.json
```

Use `memo --help` and `memo <command> --help` for the full command list.

## For Agents

Use `memo` as durable local memory. Inspect first, write only with clear user intent, and verify every write.

Install the skill:

```bash
npx skills add coderfee/a-memo
bunx skills add coderfee/a-memo
pnpx skills add coderfee/a-memo
```

Safe read commands:

```bash
memo list --limit 20
memo search "keyword"
memo show <id>
memo tags
memo links <id>
memo review --count 5
memo backup
memo export --out memos.json
memo flomo-import export.html --dry-run
```

Write commands need explicit user intent:

```bash
memo add "content #tag"
memo update <id> "new content #tag"
memo tag <id> "#tag"
memo link <id1> <id2>
memo unlink <id1> <id2>
memo delete <id>
memo review --count 1 --push
memo import memos.json
```

High-risk commands need a backup and explicit confirmation:

```bash
memo import memos.json --replace
memo reset --force
```

Agent workflow:

1. Inspect with `list`, `search`, `show`, `tags`, or `links`.
2. Run the smallest authorized command.
3. Verify with a narrow read command.
4. Report memo ids, tags, file paths, backup paths, and verification results.

Detailed agent guidance lives in [skills/memo/SKILL.md](skills/memo/SKILL.md).

## License

MIT
