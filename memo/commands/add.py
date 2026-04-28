"""add 子命令"""

import json
import time

from .. import render_memo_text, split_tags_and_content


def add_parser(sub):
    p = sub.add_parser("add", help="添加 memo")
    p.add_argument("content", nargs="+")
    p.set_defaults(func=cmd_add)
    return p


def cmd_add(conn, args):
    raw_content = " ".join(args.content).strip()
    if not raw_content:
        raise ValueError("content required")

    tags, content = split_tags_and_content(raw_content)
    if not content:
        raise ValueError("content required")
    now = time.time()

    try:
        with conn:
            cur = conn.execute(
                "INSERT INTO memos (content, tags, created_at, source) VALUES (?, ?, ?, 'cli')",
                (content, json.dumps(tags, ensure_ascii=False), now),
            )
            conn.execute(
                "INSERT INTO memos_fts(rowid, content) VALUES (?, ?)",
                (cur.lastrowid, render_memo_text(tags, content)),
            )
    except Exception as exc:
        raise RuntimeError(f"failed to add: {exc}") from exc

    print(f"created #{cur.lastrowid}")
    if tags:
        print(f"tags: {' '.join('#' + t.lstrip('#') for t in tags)}")
