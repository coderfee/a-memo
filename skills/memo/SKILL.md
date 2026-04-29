---
name: memo
description: >
  Manage the local a-memo CLI for AI agents. Use when the user asks to save,
  retrieve, search, organize, link, review, import, export, back up, recover, or
  generate share images from memo data.
---

# memo

Use `memo` as the user's durable local memory. Work carefully: inspect first, write only
with clear intent, verify every write, and protect data before risky operations.

## Decision Rules

- Read directly when the user asks to find, list, search, review, inspect tags, inspect links,
  export, back up, dry-run an import, or generate an image.
- Write only when the user asks to save, update, delete, tag, link, unlink, import, push review
  state, or reset data.
- Back up before destructive or bulk operations.
- Prefer existing tag structure. Run `memo tags` before introducing new tag hierarchies.
- Verify with the narrowest useful command after every write.
- Report concrete ids, tags, file paths, backup paths, and verification results.

## Command Safety

Safe read-oriented commands:

```bash
memo init
memo list --limit 20
memo list "#tag"
memo search "keyword"
memo tags
memo links <id>
memo review --count 5
memo backup
memo export --out memos.json
memo image <id>
memo flomo-import export.html --dry-run
memo rebuild-fts
```

Intent-required write commands:

```bash
memo add "content #tag"
memo update <id> "new content #tag"
memo tag <id> "#tag"
memo link <id1> <id2> --type related --note "why"
memo unlink <id1> <id2>
memo delete <id>
memo review --count 1 --push
memo import memos.json
memo flomo-import export.html
```

High-risk commands:

```bash
memo import memos.json --replace
memo reset --force
```

Before high-risk commands:

```bash
memo backup
memo export --out memos-before-change.json
```

## Standard Workflow

1. Classify the request: search, save, edit, tag, link, review, image, import, export, backup,
   recovery, maintenance, or reset.
2. Inspect context:

```bash
memo list --limit 20
memo search "distinct phrase"
memo tags
memo links <id>
```

3. Execute the smallest authorized command.
4. Verify:

```bash
memo list --limit 3
memo search "keyword"
memo list "#tag"
memo links <id>
memo tags
```

5. Respond with the result and verification.

## Common Tasks

Add a memo:

```bash
memo add "memo text #area/topic"
memo list --limit 1
```

Update a memo:

```bash
memo update <id> "new content"
memo update <id> "new content #newtag"
memo search "distinct phrase"
```

Search:

```bash
memo search "keyword"
memo list "#tag"
```

Tag:

```bash
memo tags
memo tag <id> "#area/topic"
memo list "#area/topic"
```

Link:

```bash
memo link <id1> <id2>
memo link <id1> <id2> --type supports --note "evidence"
memo link <id1> <id2> --type contrasts --note "opposing case"
memo links <id1>
```

Review:

```bash
memo review --count 5
memo review --count 1 --push
```

Use `review --push` only for a real review session, because it records review state.

Import:

```bash
memo flomo-import export.html --dry-run
memo backup
memo flomo-import export.html
memo list --limit 5
memo tags
```

Recovery or migration:

```bash
memo backup
memo export --out memos.json
memo import memos.json --replace
memo list --limit 5
memo tags
```

## Share Images

Generate a PNG share card:

```bash
memo image <id>
memo image <id> --out share.png
memo image <id> --style ink
```

Style guidance:

- `paper`: default warm reading card
- `clean`: minimal white note
- `ink`: stronger blue ink frame

## Review Output Format

When presenting review results to the user, use this shape:

```markdown
### Memo 回顾 · #ID

#tag1 #tag2

content

YYYY/MM/DD HH:mm:ss · 回顾 N 次

相关 memo：
- #ID relation_type：#tag content
```

Omit the related memo section when no links exist.

## Response Templates

Write completed:

```markdown
已完成：<action>
- memo：#ID
- 标签：#tag
- 验证：<command/result>
```

Backup, import, or recovery completed:

```markdown
已完成：<action>
- 备份：<path>
- 数据：N 条 memo
- 验证：list/search/tags 正常
```

Failed safely:

```markdown
操作未完成：<reason>
数据保护：<backup path or status>
建议下一步：<specific command>
```
