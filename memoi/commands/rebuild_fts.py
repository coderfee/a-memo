"""rebuild_fts 子命令"""
import json

from .. import connect, render_memo_text


def add_parser(sub):
    p = sub.add_parser("rebuild-fts", help="重建搜索索引")
    p.set_defaults(func=cmd_rebuild_fts)
    return p


def cmd_rebuild_fts(conn, args):
    rows = conn.execute("SELECT id, content, tags FROM memos ORDER BY id").fetchall()
    try:
        with conn:
            conn.execute("DELETE FROM memos_fts")
            conn.executemany(
                "INSERT INTO memos_fts(rowid, content) VALUES (?, ?)",
                (
                    (
                        row["id"],
                        render_memo_text(
                            json.loads(row["tags"]) if row["tags"] else [],
                            row["content"],
                        ),
                    )
                    for row in rows
                ),
            )
            conn.execute("INSERT INTO memos_fts(memos_fts) VALUES('optimize')")
    except Exception as exc:
        raise RuntimeError(f"failed to rebuild fts: {exc}") from exc

    print(f"fts rebuilt ({len(rows)} memos indexed)")