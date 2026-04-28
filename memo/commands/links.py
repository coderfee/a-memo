"""links 子命令"""
import argparse
import json

from .. import connect, linked_memos_for, require_memos


def add_parser(sub):
    p = sub.add_parser("links", help="查看 memo 关联")
    p.add_argument("id", type=positive_int)
    p.add_argument("--limit", type=positive_int, default=20)
    p.set_defaults(func=cmd_links)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def cmd_links(conn, args):
    require_memos(conn, [args.id])
    rows = linked_memos_for(conn, args.id, args.limit)
    print(json.dumps(rows, ensure_ascii=False, indent=2))