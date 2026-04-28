---
name: memo
description: >
  Manage the local a-memo CLI for AI agents. Use when the user asks to save or
  retrieve memos, search past notes, organize tags, link related memos, run review,
  generate share images, import Flomo exports, backup/export/import data, or recover
  memo data safely.
---

# memo

Use `memo` to manage the user's local knowledge store safely. The success path is:
understand intent, inspect existing context, make authorized changes, verify the result,
and preserve recoverability for risky operations.

## Safety Rules

- Treat conversation as context. Write only when the user explicitly asks to save, update,
  delete, tag, link, import, review-push, or reset memo data.
- Query commands can run directly: `init`, `list`, `search`, `tags`, `review`, `links`,
  `backup`, `export`, `image --format svg`, `flomo-import --dry-run`, `rebuild-fts`.
- Write commands require explicit user intent: `add`, `update`, `delete`, `tag`, `link`,
  `unlink`, `review --push`, `import`, formal `flomo-import`.
- Destructive commands require explicit user intent and a backup: `reset --force`,
  `import --replace`, batch delete, batch update.
- After each write, verify with the narrowest useful command and report the concrete result.
- If an operation fails after a backup, include the backup path in the response.

## Core Commands

```bash
memo init
memo add "content #tag"
memo list --limit 20
memo list "#tag"
memo search "keyword"
memo tags
memo tag <id> "#tag"
memo update <id> "new content #tag"
memo delete <id>
memo link <id1> <id2> --type related --note "why"
memo links <id>
memo unlink <id1> <id2>
memo review --count 5
memo review --count 1 --push
memo image <id> --format svg
memo image <id> --format png
memo backup
memo export --out memos.json
memo import memos.json
memo import memos.json --replace
memo flomo-import export.html --dry-run
memo flomo-import export.html
memo rebuild-fts
memo reset --force
```

## Standard Workflow

1. Classify the request: query, save, edit, tag, link, review, import, export, recover, reset.
2. Inspect context:
   - Find a memo: `memo search "keyword"` or `memo list --limit 20`
   - Check tags: `memo tags`
   - Check relationships: `memo links <id>`
3. Execute only the authorized command.
4. Verify:
   - Add/update/delete: `memo list --limit 3` or `memo search "keyword"`
   - Tag: `memo list "#tag"` or `memo tags`
   - Link/unlink: `memo links <id>`
   - Import/export/restore: `memo list --limit 3`, `memo tags`, targeted `memo search`
5. Report ids, tags, backup path, and verification result.

## Add And Update

Use `add` only when the user asks to record/save a memo:

```bash
memo add "memo text #area/topic"
memo list --limit 1
```

Tags inside content are extracted and lowercased. Body text is stored without the tag text.

Use `update` when the user names an existing memo:

```bash
memo update <id> "new content"
memo update <id> "new content #newtag"
```

`update` keeps existing tags when no tags are supplied. It replaces tags when tags are supplied.

## Search And Listing

Use `search` for semantic or keyword lookup:

```bash
memo search "keyword"
```

Use `list` for recent items or tag-filtered views:

```bash
memo list --limit 20
memo list "#area/topic"
```

When a user gives an id, verify it before destructive edits:

```bash
memo list --limit 20
memo search "distinct phrase"
```

## Tags

Use existing tag structure before inventing new labels:

```bash
memo tags
memo tag <id> "#area/topic"
```

`tag` appends tags and deduplicates. For careful tagging:

1. Run `memo tags`.
2. Prefer existing hierarchy.
3. Check related memos with `memo links <id>`.
4. For batch tagging, show the plan and wait for user confirmation.

## Links

Relations are logically bidirectional:

```bash
memo link <id1> <id2>
memo link <id1> <id2> --type supports --note "evidence"
memo link <id1> <id2> --type contrasts --note "opposing case"
memo links <id1>
memo unlink <id1> <id2>
```

Relation types:

- `related`: general connection
- `supports`: one memo supports another
- `contrasts`: two memos form a contrast

Before linking, confirm both ids exist and choose the relation type. After linking, run
`memo links <id>`.

## Review

```bash
memo review --count 5
memo review --count 1 --push
```

`review` reads candidates. `review --push` records the review, increments `review_count`,
updates `last_review_at`, and appends to `~/.memo/history/`.

Use `--push` when the user asks to perform a real review session. Format review output for the
user:

```markdown
### Memo 回顾 · #ID

#tag1 #tag2

content

YYYY/MM/DD HH:mm:ss · 回顾 N 次

相关 memo：
- #ID relation_type：#tag content
```

Omit the related memo section when no links exist.

## Backup, Export, Import, Recovery

Use backups before risky work:

```bash
memo backup
memo export --out memos.json
memo import memos.json
memo import memos.json --replace
```

Guidance:

- `backup` creates a SQLite backup.
- `export` creates portable JSON.
- `import` appends data and remaps links.
- `import --replace` replaces current data and creates an automatic backup.
- After import or recovery, verify with `list`, `tags`, and a targeted `search`.

Migration to another machine:

```bash
memo export --out memos.json
# copy memos.json to the new machine
memo import memos.json --replace
```

## Images

SVG is the reliable fallback:

```bash
memo image <id> --format svg
```

PNG requires the optional dependency and a browser:

```bash
uv tool install --force "a-memo[png]"
uv tool run playwright install chromium
memo image <id> --format png
```

If PNG fails, report the actionable install command from the error and generate SVG.

## Flomo Import

Always preview first:

```bash
memo flomo-import export.html --dry-run
```

When the user confirms:

```bash
memo backup
memo flomo-import export.html
memo list --limit 5
memo tags
```

Report parsed/imported/skipped/failed counts.

## Maintenance

Search index issue:

```bash
memo rebuild-fts
memo search "keyword"
```

Full reset:

```bash
memo reset --force
```

Use reset only when the user asks to delete all memo data. The command creates an automatic
backup when a database exists. Report the backup path.

## Response Templates

Write completed:

```markdown
已完成：<action>
- memo：#ID
- 标签：#tag
- 验证：<command/result>
```

Backup/import/recovery completed:

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
