"""export 子命令"""

import json
import time
from pathlib import Path

from .. import CURRENT_SCHEMA_VERSION


def add_parser(sub):
    p = sub.add_parser("export", help="导出 JSON")
    p.add_argument("--out", help="输出 JSON 文件路径")
    p.set_defaults(func=cmd_export)
    return p


def _rows(conn, query):
    return [dict(row) for row in conn.execute(query).fetchall()]


def export_payload(conn):
    return {
        "format": "a-memo-export",
        "schema_version": CURRENT_SCHEMA_VERSION,
        "exported_at": time.time(),
        "memos": _rows(conn, "SELECT * FROM memos ORDER BY id"),
        "memo_links": _rows(conn, "SELECT * FROM memo_links ORDER BY id"),
    }


def cmd_export(conn, args):
    payload = export_payload(conn)
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"exported: {out}")
        return 0
    print(text)
    return 0
