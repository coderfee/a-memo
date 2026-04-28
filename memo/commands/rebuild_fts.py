"""rebuild_fts 子命令"""

from .. import rebuild_fts_index


def add_parser(sub):
    p = sub.add_parser("rebuild-fts", help="重建搜索索引")
    p.set_defaults(func=cmd_rebuild_fts)
    return p


def cmd_rebuild_fts(conn, args):
    try:
        with conn:
            count = rebuild_fts_index(conn)
    except Exception as exc:
        raise RuntimeError(f"failed to rebuild fts: {exc}") from exc

    print(f"fts rebuilt ({count} memos indexed)")
