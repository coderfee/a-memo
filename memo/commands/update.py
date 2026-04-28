"""update 子命令"""
import argparse
import json
import time

from .. import connect, render_memo_text, split_tags_and_content


def add_parser(sub):
    p = sub.add_parser("update", help="更新 memo")
    p.add_argument("id", type=positive_int)
    p.add_argument("content", nargs="+")
    p.set_defaults(func=cmd_update)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_update(conn, args):
    row = conn.execute("SELECT content, tags FROM memos WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise ValueError(f"memo #{args.id} not found")

    raw_content = " ".join(args.content).strip()
    if not raw_content:
        raise ValueError("content required")

    parsed_tags, content = split_tags_and_content(raw_content)
    if not content:
        raise ValueError("content required")

    existing_tags = json.loads(row["tags"]) if row["tags"] else []
    tags = parsed_tags or existing_tags

    try:
        with conn:
            conn.execute(
                "UPDATE memos SET content=?, tags=?, updated_at=? WHERE id=?",
                (content, json.dumps(tags, ensure_ascii=False), time.time(), args.id),
            )
            conn.execute(
                "INSERT OR REPLACE INTO memos_fts(rowid, content) VALUES (?, ?)",
                (args.id, render_memo_text(tags, content)),
            )
    except Exception as exc:
        raise RuntimeError(f"failed to update: {exc}") from exc

    print(f"updated #{args.id}")
    if tags:
        print(f"tags: {' '.join('#'+t.lstrip('#') for t in tags)}")