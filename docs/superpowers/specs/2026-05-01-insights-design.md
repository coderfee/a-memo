# memo insights design

## Goal

Add a read-only `memo insights` command that helps users understand recent memo activity,
tag structure, review health, and link structure.

The first version serves both human review workflows and agent workflows by keeping the
default output as structured JSON.

## CLI

```bash
memo insights
memo insights --days 7
memo insights --days 90
memo insights --days 0
memo insights --view tags
memo insights --view review
memo insights --view links
memo insights --limit 10
```

Arguments:

- `--view overview|tags|review|links`
  - Default: `overview`
- `--days N`
  - Default: `30`
  - `0` means all history
- `--limit N`
  - Default: `10`
  - Controls ranked lists and suggestion-sized result sets

All arguments use non-negative integer validation consistent with existing commands.

## Output

The command prints JSON to stdout. Errors use the existing CLI error path through
`RuntimeError` or `ValueError`, with messages printed to stderr by `memo.cli:main`.

Every response includes:

- `view`: selected view name
- `window`: selected time window

Example overview shape:

```json
{
  "view": "overview",
  "window": {
    "days": 30,
    "since": "2026/04/01 00:00:00",
    "until": "2026/05/01 00:00:00"
  },
  "totals": {
    "memos": 42,
    "tags": 12,
    "links": 8
  },
  "activity": {
    "created": 14,
    "updated": 3,
    "reviewed": 5
  },
  "top_tags": [
    {
      "tag": "#work/ai",
      "count": 6
    }
  ],
  "review": {
    "due": 9,
    "never_reviewed": 21,
    "stale": 4,
    "most_reviewed": [
      {
        "id": 3,
        "review_count": 5
      }
    ]
  },
  "links": {
    "linked_memos": 10,
    "unlinked_memos": 32,
    "top_linked": [
      {
        "id": 3,
        "link_count": 4
      }
    ]
  }
}
```

## Time Window Rules

Windowed metrics use the selected `--days` range:

- Memos created in the window
- Memos updated in the window
- Memos reviewed in the window
- Top tags among memos created in the window

Global structure metrics are calculated across the full database and should be named or
grouped so their scope is explicit:

- Total memo count
- Total unique tag count
- Total link count
- Linked and unlinked memo counts
- Global top tags in the `tags` view
- Review backlog counts

For `--days 0`, the window covers all history and `since` is `null`.

## Views

### overview

Default view. It provides a compact cross-section of the database:

- `totals`: global counts for memos, unique tags, and links
- `activity`: created, updated, and reviewed counts in the window
- `top_tags`: most common tags among memos created in the window
- `review`: due, never reviewed, stale, and most reviewed counts or ranked entries
- `links`: linked memo count, unlinked memo count, and top linked memos

### tags

Tag-focused view:

- Window top tags
- Global top tags
- Dormant tags with no memos created in the selected window
- Unique tag count

Tags are parsed from the existing JSON `memos.tags` field. Malformed tag JSON is skipped
with the existing warning style if encountered.

### review

Review-focused view:

- Due memo count based on the existing review eligibility rule
- Never reviewed memo count
- Stale memo count
- Most reviewed memos

Review due behavior should align with existing `review` command semantics:

- A memo is due when `COALESCE(last_review_at, created_at)` is older than 7 days.
- Stale means older than 180 days by the same timestamp.

### links

Link-focused view:

- Total links
- Linked memo count
- Unlinked memo count
- Top linked memos
- Relation type distribution

Link counts include all rows in `memo_links`.

## Implementation Shape

Add a new command module:

```text
memo/commands/insights.py
```

Register `insights` in `memo/cli.py`:

- Add it to `COMMANDS`
- Add help text to `_print_help_and_exit`

Suggested internal functions:

```python
parse_days_window(days)
build_overview(conn, days, limit)
build_tag_insights(conn, days, limit)
build_review_insights(conn, days, limit)
build_link_insights(conn, days, limit)
```

The implementation should stay read-only:

- No history writes
- No `review_count` updates
- No schema migration
- No writes to user memo data

## Testing

Use behavior-level tests through `memo.cli:main`, matching the current test style.

Coverage:

- `memo insights` returns `overview` JSON with default 30-day window
- `memo insights --days 0` returns all-history window with `since: null`
- `memo insights --view tags`
- `memo insights --view review`
- `memo insights --view links`
- Empty database returns valid JSON with zero counts and empty lists
- Invalid `--view` exits through argparse
- Invalid negative `--days` and `--limit` exit through argparse

Manual checks should use a temporary `MEMO_DATA_DIR`.

## Documentation

Update user-facing docs:

- Add `memo insights` to README usage examples
- Add `memo insights` guidance to `skills/memo/SKILL.md`

README text should stay short and user-focused.
