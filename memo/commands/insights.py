"""insights 子命令"""

import argparse
import json
import time
from collections import Counter

from .. import fmt_time, warn

VIEWS = ("overview", "tags", "review", "links")
SECONDS_PER_DAY = 86400


def add_parser(sub):
    p = sub.add_parser("insights", help="查看 memo 洞察")
    p.add_argument("--view", choices=VIEWS, default="overview")
    p.add_argument("--days", type=positive_int, default=30)
    p.add_argument("--limit", type=positive_int, default=10)
    p.set_defaults(func=cmd_insights)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_insights(conn, args):
    builders = {
        "overview": build_overview,
        "tags": build_tag_insights,
        "review": build_review_insights,
        "links": build_link_insights,
    }
    payload = builders[args.view](conn, args.days, args.limit)
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def parse_days_window(days):
    until_ts = time.time()
    since_ts = None if days == 0 else until_ts - days * SECONDS_PER_DAY
    window = {
        "days": days,
        "since": fmt_time(since_ts) if since_ts is not None else None,
        "until": fmt_time(until_ts),
    }
    return window, since_ts, until_ts


def load_memo_rows(conn):
    return conn.execute(
        """
        SELECT id, content, tags, created_at, updated_at, review_count, last_review_at
        FROM memos
        ORDER BY id
        """
    ).fetchall()


def row_tags(row):
    if not row["tags"]:
        return []
    try:
        return json.loads(row["tags"])
    except json.JSONDecodeError:
        warn(f"skipped malformed tags: {row['tags']}")
        return []


def in_window(value, since_ts, until_ts):
    if value is None:
        return False
    if since_ts is not None and value < since_ts:
        return False
    return value <= until_ts


def ranked_counter(counter, limit, key_name):
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [{key_name: key, "count": count} for key, count in ranked[:limit]]


def tag_counts(rows):
    counter = Counter()
    for row in rows:
        counter.update(row_tags(row))
    return counter


def memo_entry(row, **extra):
    entry = {
        "id": row["id"],
        "content": row["content"].strip(),
        "tags": row_tags(row),
    }
    entry.update(extra)
    return entry


def build_overview(conn, days, limit):
    window, since_ts, until_ts = parse_days_window(days)
    rows = load_memo_rows(conn)
    window_rows = [row for row in rows if in_window(row["created_at"], since_ts, until_ts)]

    return {
        "view": "overview",
        "window": window,
        "totals": build_totals(conn, rows),
        "activity": build_activity(rows, since_ts, until_ts),
        "top_tags": ranked_counter(tag_counts(window_rows), limit, "tag"),
        "review": build_review_summary(rows, limit),
        "links": build_link_summary(conn, rows, limit),
    }


def build_tag_insights(conn, days, limit):
    window, since_ts, until_ts = parse_days_window(days)
    rows = load_memo_rows(conn)
    window_rows = [row for row in rows if in_window(row["created_at"], since_ts, until_ts)]
    global_counts = tag_counts(rows)
    window_counts = tag_counts(window_rows)
    dormant_tags = sorted(tag for tag in global_counts if tag not in window_counts)

    return {
        "view": "tags",
        "window": window,
        "unique_tags": len(global_counts),
        "window_top_tags": ranked_counter(window_counts, limit, "tag"),
        "global_top_tags": ranked_counter(global_counts, limit, "tag"),
        "dormant_tags": dormant_tags[:limit],
    }


def build_review_insights(conn, days, limit):
    window, _, _ = parse_days_window(days)
    rows = load_memo_rows(conn)
    summary = build_review_summary(rows, limit)
    return {
        "view": "review",
        "window": window,
        **summary,
    }


def build_link_insights(conn, days, limit):
    window, _, _ = parse_days_window(days)
    rows = load_memo_rows(conn)
    summary = build_link_summary(conn, rows, limit)
    return {
        "view": "links",
        "window": window,
        "total_links": summary["total_links"],
        "linked_memos": summary["linked_memos"],
        "unlinked_memos": summary["unlinked_memos"],
        "top_linked": summary["top_linked"],
        "relation_types": relation_type_distribution(conn, limit),
    }


def build_totals(conn, rows):
    total_links = conn.execute("SELECT COUNT(*) FROM memo_links").fetchone()[0]
    return {
        "memos": len(rows),
        "tags": len(tag_counts(rows)),
        "links": total_links,
    }


def build_activity(rows, since_ts, until_ts):
    return {
        "created": sum(1 for row in rows if in_window(row["created_at"], since_ts, until_ts)),
        "updated": sum(1 for row in rows if in_window(row["updated_at"], since_ts, until_ts)),
        "reviewed": sum(1 for row in rows if in_window(row["last_review_at"], since_ts, until_ts)),
    }


def build_review_summary(rows, limit):
    now = time.time()
    due_rows = [
        row
        for row in rows
        if now - (row["last_review_at"] or row["created_at"]) >= 7 * SECONDS_PER_DAY
    ]
    stale_rows = [
        row
        for row in rows
        if now - (row["last_review_at"] or row["created_at"]) >= 180 * SECONDS_PER_DAY
    ]
    most_reviewed_rows = sorted(
        (row for row in rows if (row["review_count"] or 0) > 0),
        key=lambda row: (-(row["review_count"] or 0), row["id"]),
    )
    return {
        "due": len(due_rows),
        "never_reviewed": sum(1 for row in rows if row["last_review_at"] is None),
        "stale": len(stale_rows),
        "most_reviewed": [
            memo_entry(row, review_count=row["review_count"] or 0)
            for row in most_reviewed_rows[:limit]
        ],
    }


def build_link_summary(conn, rows, limit):
    total_links = conn.execute("SELECT COUNT(*) FROM memo_links").fetchone()[0]
    linked_ids = linked_memo_ids(conn)
    return {
        "total_links": total_links,
        "linked_memos": len(linked_ids),
        "unlinked_memos": max(len(rows) - len(linked_ids), 0),
        "top_linked": top_linked_memos(conn, limit),
    }


def linked_memo_ids(conn):
    rows = conn.execute(
        """
        SELECT from_memo_id AS memo_id FROM memo_links
        UNION
        SELECT to_memo_id AS memo_id FROM memo_links
        """
    ).fetchall()
    return {row["memo_id"] for row in rows}


def top_linked_memos(conn, limit):
    rows = conn.execute(
        """
        WITH endpoints AS (
          SELECT from_memo_id AS memo_id FROM memo_links
          UNION ALL
          SELECT to_memo_id AS memo_id FROM memo_links
        ),
        ranked AS (
          SELECT memo_id, COUNT(*) AS link_count
          FROM endpoints
          GROUP BY memo_id
        )
        SELECT m.id, m.content, m.tags, ranked.link_count
        FROM ranked
        JOIN memos m ON m.id = ranked.memo_id
        ORDER BY ranked.link_count DESC, m.id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [memo_entry(row, link_count=row["link_count"]) for row in rows]


def relation_type_distribution(conn, limit):
    rows = conn.execute(
        """
        SELECT relation_type, COUNT(*) AS count
        FROM memo_links
        GROUP BY relation_type
        ORDER BY count DESC, relation_type ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [{"relation_type": row["relation_type"], "count": row["count"]} for row in rows]
