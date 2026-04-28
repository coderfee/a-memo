"""tags 子命令"""
import json

from .. import connect, warn


def add_parser(sub):
    p = sub.add_parser("tags", help="列出所有标签")
    p.set_defaults(func=cmd_tags)
    return p


def cmd_tags(conn, args):
    rows = conn.execute("SELECT tags FROM memos WHERE tags IS NOT NULL AND tags != ''").fetchall()
    tags = set()
    for row in rows:
        try:
            tags.update(json.loads(row["tags"]))
        except json.JSONDecodeError:
            warn(f"skipped malformed tags: {row['tags']}")

    result = sorted(tags)
    print(json.dumps(result, ensure_ascii=False, indent=2))