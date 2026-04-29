"""show 子命令"""

import argparse
import json

from .. import fmt_time, linked_memos_for


def add_parser(sub):
    p = sub.add_parser("show", help="查看单条 memo")
    p.add_argument("id", type=positive_int)
    p.add_argument("--links", action="store_true", help="include linked memos")
    p.set_defaults(func=cmd_show)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_show(conn, args):
    row = conn.execute("SELECT * FROM memos WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise ValueError(f"memo #{args.id} not found")

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
    if args.links:
        entry["links"] = linked_memos_for(conn, args.id)

    print(json.dumps(entry, ensure_ascii=False, indent=2))
