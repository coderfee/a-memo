"""import 子命令"""

import json
import time
from pathlib import Path

from .. import create_backup, rebuild_fts_index


def add_parser(sub):
    p = sub.add_parser("import", help="导入 JSON")
    p.add_argument("json_path", type=Path)
    p.add_argument("--replace", action="store_true", help="replace existing data")
    p.add_argument("--no-backup", action="store_true", help="skip backup before replace")
    p.set_defaults(func=cmd_import)
    return p


def _load_payload(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ValueError(f"failed to read import file: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON export: {exc}") from exc

    if payload.get("format") != "a-memo-export":
        raise ValueError("unsupported import format")
    if not isinstance(payload.get("memos"), list):
        raise ValueError("invalid export: memos must be a list")
    if not isinstance(payload.get("memo_links", []), list):
        raise ValueError("invalid export: memo_links must be a list")
    return payload


def _insert_memo(conn, memo, preserve_id):
    fields = [
        "content",
        "tags",
        "created_at",
        "updated_at",
        "review_count",
        "last_review_at",
        "source",
    ]
    values = [memo.get(field) for field in fields]
    if preserve_id:
        conn.execute(
            """
            INSERT INTO memos
              (id, content, tags, created_at, updated_at, review_count, last_review_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [memo["id"], *values],
        )
        return memo["id"]

    cur = conn.execute(
        """
        INSERT INTO memos
          (content, tags, created_at, updated_at, review_count, last_review_at, source)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        values,
    )
    return cur.lastrowid


def _insert_link(conn, link, id_map, preserve_id):
    from_id = id_map.get(link.get("from_memo_id"))
    to_id = id_map.get(link.get("to_memo_id"))
    if from_id is None or to_id is None:
        return

    if preserve_id:
        conn.execute(
            """
            INSERT OR IGNORE INTO memo_links
              (id, from_memo_id, to_memo_id, relation_type, note, created_at, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                link.get("id"),
                from_id,
                to_id,
                link.get("relation_type", "related"),
                link.get("note"),
                link.get("created_at", time.time()),
                link.get("source", "import"),
            ),
        )
        return

    conn.execute(
        """
        INSERT OR IGNORE INTO memo_links
          (from_memo_id, to_memo_id, relation_type, note, created_at, source)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            from_id,
            to_id,
            link.get("relation_type", "related"),
            link.get("note"),
            link.get("created_at", time.time()),
            link.get("source", "import"),
        ),
    )


def cmd_import(conn, args):
    payload = _load_payload(args.json_path)

    backup_path = None
    if args.replace and not args.no_backup:
        backup_path = create_backup(conn)

    with conn:
        if args.replace:
            conn.execute("DELETE FROM memo_links")
            conn.execute("DELETE FROM memos_fts")
            conn.execute("DELETE FROM memos")

        id_map = {}
        imported_count = 0
        for memo in payload["memos"]:
            if "id" not in memo or not memo.get("content") or memo.get("created_at") is None:
                raise ValueError("invalid export: each memo needs id, content, created_at")
            new_id = _insert_memo(conn, memo, preserve_id=args.replace)
            id_map[memo["id"]] = new_id
            imported_count += 1

        for link in payload.get("memo_links", []):
            _insert_link(conn, link, id_map, preserve_id=args.replace)

        rebuild_fts_index(conn)

    print(f"imported {imported_count} memos")
    if backup_path:
        print(f"backup saved: {backup_path}")
    return 0
