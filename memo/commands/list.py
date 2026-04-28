"""list 子命令"""

import argparse
import json

from .. import fmt_time


def add_parser(sub):
    p = sub.add_parser("list", help="列出 memos")
    p.add_argument("tag", nargs="?")
    p.add_argument("--limit", type=positive_int, default=30)
    p.add_argument("--offset", type=positive_int, default=0)
    p.set_defaults(func=cmd_list)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_list(conn, args):
    tag = args.tag.lower() if args.tag else None
    if tag:
        rows = conn.execute(
            """
            SELECT * FROM memos
            WHERE tags LIKE ? OR tags LIKE ?
            ORDER BY created_at DESC LIMIT ? OFFSET ?
            """,
            (
                f'%"#{tag.lstrip("#")}"%',
                f'%"#{tag.lstrip("#")}/%',
                args.limit,
                args.offset,
            ),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM memos ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (args.limit, args.offset),
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
