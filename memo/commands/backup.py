"""backup 子命令"""

from pathlib import Path

from .. import create_backup


def add_parser(sub):
    p = sub.add_parser("backup", help="备份数据库")
    p.add_argument("--out", help="输出 .db 文件路径")
    p.set_defaults(func=cmd_backup)
    return p


def cmd_backup(conn, args):
    out = create_backup(conn, Path(args.out) if args.out else None)
    print(f"backup saved: {out}")
