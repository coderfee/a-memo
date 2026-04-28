"""delete 子命令"""

import argparse


def add_parser(sub):
    p = sub.add_parser("delete", help="删除 memo")
    p.add_argument("id", type=positive_int)
    p.set_defaults(func=cmd_delete)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_delete(conn, args):
    if not conn.execute("SELECT id FROM memos WHERE id=?", (args.id,)).fetchone():
        raise ValueError(f"memo #{args.id} not found")

    try:
        with conn:
            conn.execute("DELETE FROM memos WHERE id=?", (args.id,))
            conn.execute("DELETE FROM memos_fts WHERE rowid=?", (args.id,))
            conn.execute(
                "DELETE FROM memo_links WHERE from_memo_id=? OR to_memo_id=?",
                (args.id, args.id),
            )
    except Exception as exc:
        raise RuntimeError(f"failed to delete: {exc}") from exc

    print(f"deleted #{args.id}")
