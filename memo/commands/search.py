"""search 子命令"""

import argparse
import json

from .. import fmt_time, fts_query, warn


def add_parser(sub):
    p = sub.add_parser("search", help="搜索 memos")
    p.add_argument("query", nargs="+")
    p.add_argument("--limit", type=positive_int, default=20)
    p.set_defaults(func=cmd_search)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_search(conn, args):
    query = " ".join(args.query).strip()
    if not query:
        raise ValueError("query required")

    rows = []
    q = fts_query(query)
    if q:
        try:
            rows = conn.execute(
                """
                SELECT m.* FROM memos m
                JOIN memos_fts f ON m.id = f.rowid
                WHERE memos_fts MATCH ?
                ORDER BY rank LIMIT ?
            """,
                (q, args.limit),
            ).fetchall()
        except Exception as exc:
            warn(f"fts search failed, falling back to like: {exc}")

    if not rows:
        rows = conn.execute(
            "SELECT * FROM memos WHERE content LIKE ? ORDER BY created_at DESC LIMIT ?",
            (f"%{query}%", args.limit),
        ).fetchall()

    result = []
    for row in rows:
        entry = {
            "id": row["id"],
            "content": row["content"].strip(),
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": fmt_time(row["created_at"]),
            "review_count": row["review_count"] or 0,
        }
        if row["updated_at"]:
            entry["updated_at"] = fmt_time(row["updated_at"])
        if row["last_review_at"]:
            entry["last_review_at"] = fmt_time(row["last_review_at"])
        result.append(entry)

    print(json.dumps(result, ensure_ascii=False, indent=2))
