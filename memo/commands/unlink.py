"""unlink 子命令"""

import argparse

from .. import normalize_link_ids, validate_relation_type


def add_parser(sub):
    p = sub.add_parser("unlink", help="删除两条 memo 的关联")
    p.add_argument("left_id", type=positive_int)
    p.add_argument("right_id", type=positive_int)
    p.add_argument("--type", default="related", help="关联类型: related, supports, contrasts")
    p.set_defaults(func=cmd_unlink)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_unlink(conn, args):
    relation_type = validate_relation_type(args.type)
    from_memo_id, to_memo_id = normalize_link_ids(args.left_id, args.right_id)

    try:
        with conn:
            cur = conn.execute(
                """
                DELETE FROM memo_links
                WHERE from_memo_id=? AND to_memo_id=? AND relation_type=?
                """,
                (from_memo_id, to_memo_id, relation_type),
            )
    except Exception as exc:
        raise RuntimeError(f"failed to unlink: {exc}") from exc

    if cur.rowcount == 0:
        raise ValueError(f"#{args.left_id} ↔ #{args.right_id} has no {relation_type} link")
    print(f"unlinked #{args.left_id} ↔ #{args.right_id} ({relation_type})")
