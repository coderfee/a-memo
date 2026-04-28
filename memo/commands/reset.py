"""reset 子命令 — 重置数据目录"""

import shutil

from .. import get_data_dir


def add_parser(sub):
    p = sub.add_parser("reset", help="重置数据目录")
    p.add_argument("--force", action="store_true", help="skip confirmation")
    p.set_defaults(func=cmd_reset)
    return p


def cmd_reset(conn, args):
    data_dir = get_data_dir()
    if not data_dir.exists():
        print(f"data dir not found: {data_dir}")
        return 0

    if not args.force:
        print(f"will delete data dir: {data_dir}")
        print("includes: memo.db, images/, history/")
        print()
        confirm = input("type 'yes' to confirm: ")
        if confirm.strip() != "yes":
            print("cancelled")
            return 0

    shutil.rmtree(data_dir)
    print(f"deleted: {data_dir}")
    return 0
