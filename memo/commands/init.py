"""init 子命令"""
from .. import connect


def add_parser(sub):
    p = sub.add_parser("init", help="初始化数据库")
    p.set_defaults(func=cmd_init)
    return p


def cmd_init(conn, args):
    print("ready")