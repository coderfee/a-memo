"""reset 子命令 — 重置数据目录"""

import shutil
import time
from pathlib import Path

from .. import DEFAULT_DATA_DIR, create_backup, get_data_dir, get_db_path


def add_parser(sub):
    p = sub.add_parser("reset", help="重置数据目录")
    p.add_argument("--force", action="store_true", help="skip confirmation")
    p.add_argument("--no-backup", action="store_true", help="skip automatic backup")
    p.set_defaults(func=cmd_reset)
    return p


def _safe_reset_path(path):
    resolved = path.expanduser().resolve()
    home = Path.home().resolve()
    if resolved in {Path("/"), home, home.parent}:
        raise ValueError(f"refusing to reset unsafe data dir: {resolved}")
    if resolved == DEFAULT_DATA_DIR.resolve():
        return resolved
    if (resolved / "memo.db").exists():
        return resolved
    if "memo" not in resolved.name.lower():
        raise ValueError(f"refusing to reset data dir without memo in its name: {resolved}")
    return resolved


def _reset_backup_path(data_dir):
    stamp = time.strftime("%Y%m%d-%H%M%S")
    return data_dir.parent / f"{data_dir.name}-backup-{stamp}.db"


def cmd_reset(conn, args):
    data_dir = _safe_reset_path(get_data_dir())
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

    backup_path = None
    if not args.no_backup and get_db_path().exists():
        backup_path = create_backup(conn, _reset_backup_path(data_dir))

    shutil.rmtree(data_dir)
    if backup_path:
        print(f"backup saved: {backup_path}")
    print(f"deleted: {data_dir}")
    return 0
