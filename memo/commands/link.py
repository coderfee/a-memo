"""link 子命令"""

import argparse
import time

from .. import clean_content, normalize_link_ids, require_memos, validate_relation_type


def add_parser(sub):
    p = sub.add_parser("link", help="关联两条 memo")
    p.add_argument("left_id", type=positive_int)
    p.add_argument("right_id", type=positive_int)
    p.add_argument("--type", default="related", help="关联类型: related, supports, contrasts")
    p.add_argument("--note", help="关联说明")
    p.set_defaults(func=cmd_link)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_link(conn, args):
    relation_type = validate_relation_type(args.type)
    from_memo_id, to_memo_id = normalize_link_ids(args.left_id, args.right_id)
    require_memos(conn, [from_memo_id, to_memo_id])
    note = clean_content(args.note) if args.note else None

    try:
        with conn:
            cur = conn.execute(
                """
                INSERT OR IGNORE INTO memo_links
                  (from_memo_id, to_memo_id, relation_type, note, created_at, source)
                VALUES (?, ?, ?, ?, ?, 'cli')
                """,
                (from_memo_id, to_memo_id, relation_type, note, time.time()),
            )
            if cur.rowcount == 0 and note:
                conn.execute(
                    """
                    UPDATE memo_links
                    SET note=?
                    WHERE from_memo_id=? AND to_memo_id=? AND relation_type=?
                    """,
                    (note, from_memo_id, to_memo_id, relation_type),
                )
    except Exception as exc:
        raise RuntimeError(f"failed to link: {exc}") from exc

    action = "linked" if cur.rowcount else "link exists"
    note_suffix = f" · {note}" if note else ""
    print(f"{action} #{args.left_id} ↔ #{args.right_id} ({relation_type}){note_suffix}")
