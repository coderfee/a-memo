"""tag 子命令"""
import argparse
import json
import time

from .. import connect, parse_tags, render_memo_text


def add_parser(sub):
    p = sub.add_parser("tag", help="给 memo 加标签")
    p.add_argument("id", type=positive_int)
    p.add_argument("tags", nargs="+")
    p.set_defaults(func=cmd_tag)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_tag(conn, args):
    row = conn.execute("SELECT content, tags FROM memos WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise ValueError(f"memo #{args.id} not found")

    new = parse_tags(" ".join(args.tags))
    if not new:
        raise ValueError("at least one #tag required")

    existing = json.loads(row["tags"]) if row["tags"] else []
    merged = list(dict.fromkeys(existing + new))

    with conn:
        conn.execute(
            "UPDATE memos SET tags=?, updated_at=? WHERE id=?",
            (json.dumps(merged, ensure_ascii=False), time.time(), args.id),
        )
        conn.execute(
            "INSERT OR REPLACE INTO memos_fts(rowid, content) VALUES (?, ?)",
            (args.id, render_memo_text(merged, row["content"])),
        )
    print(f"tagged #{args.id}: {' '.join('#'+t.lstrip('#') for t in merged)}")