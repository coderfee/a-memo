"""memo CLI 核心模块"""

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

from .helpers import (
    choose_review_layer,
    clean_content,
    fmt_datetime,
    fmt_history_time,
    fmt_review_time,
    fmt_time,
    fts_query,
    history_file_path,
    normalize_link_ids,
    parse_tags,
    render_memo_text,
    review_layer_bounds,
    split_tags_and_content,
    validate_relation_type,
    wrap_text,
)

__all__ = [
    "choose_review_layer",
    "clean_content",
    "connect",
    "create_backup",
    "DEFAULT_DATA_DIR",
    "ensure_data_dir",
    "fmt_datetime",
    "fmt_history_time",
    "fmt_review_time",
    "fmt_time",
    "fts_query",
    "get_data_dir",
    "get_db_path",
    "get_history_dir",
    "get_images_dir",
    "get_backups_dir",
    "history_file_path",
    "is_db_initialized",
    "linked_memos_for",
    "normalize_link_ids",
    "parse_tags",
    "render_memo_text",
    "require_memos",
    "rebuild_fts_index",
    "review_layer_bounds",
    "split_tags_and_content",
    "validate_relation_type",
    "warn",
    "wrap_text",
]

CURRENT_SCHEMA_VERSION = 1

SCHEMA_V1 = """
  CREATE TABLE IF NOT EXISTS memos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    content      TEXT NOT NULL,
    tags         TEXT,
    created_at   REAL NOT NULL,
    updated_at   REAL,
    review_count INTEGER DEFAULT 0,
    last_review_at REAL,
    source       TEXT DEFAULT 'cli'
  );
  CREATE INDEX IF NOT EXISTS idx_memos_created ON memos(created_at DESC);
  CREATE TABLE IF NOT EXISTS memo_links (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    from_memo_id INTEGER NOT NULL,
    to_memo_id   INTEGER NOT NULL,
    relation_type TEXT DEFAULT 'related',
    note         TEXT,
    created_at   REAL NOT NULL,
    source       TEXT DEFAULT 'agent',
    UNIQUE(from_memo_id, to_memo_id, relation_type)
  );
  CREATE INDEX IF NOT EXISTS idx_memo_links_from ON memo_links(from_memo_id);
  CREATE INDEX IF NOT EXISTS idx_memo_links_to ON memo_links(to_memo_id);
  CREATE VIRTUAL TABLE IF NOT EXISTS memos_fts
    USING fts5(content, tokenize='unicode61 remove_diacritics 2');
"""

DEFAULT_DATA_DIR = Path.home() / ".memo"


def get_data_dir():
    return Path(os.environ.get("MEMO_DATA_DIR", str(DEFAULT_DATA_DIR)))


def ensure_data_dir():
    dd = get_data_dir()
    dd.mkdir(parents=True, exist_ok=True)
    return dd


def get_db_path():
    explicit = os.environ.get("MEMO_DB_PATH")
    if explicit:
        return Path(explicit)
    return get_data_dir() / "memo.db"


def get_images_dir():
    return get_data_dir() / "images"


def get_history_dir():
    return get_data_dir() / "history"


def get_backups_dir():
    return get_data_dir() / "backups"


def is_db_initialized():
    db_path = get_db_path()
    if not db_path.exists():
        return False, 0
    conn = sqlite3.connect(str(db_path))
    try:
        count = conn.execute("SELECT COUNT(*) FROM memos").fetchone()[0]
        return True, count
    except sqlite3.OperationalError:
        return False, 0
    finally:
        conn.close()


def _schema_objects_exist(conn):
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='memos'").fetchone()
    return row is not None


def _migrate_to_v1(conn):
    conn.executescript(SCHEMA_V1)
    rebuild_fts_index(conn)


MIGRATIONS = {
    1: _migrate_to_v1,
}


def _get_schema_version(conn):
    return conn.execute("PRAGMA user_version").fetchone()[0]


def _set_schema_version(conn, version):
    conn.execute(f"PRAGMA user_version = {version}")


def migrate(conn):
    version = _get_schema_version(conn)

    if version > CURRENT_SCHEMA_VERSION:
        raise RuntimeError(
            f"database schema version {version} is newer than supported {CURRENT_SCHEMA_VERSION}"
        )

    for next_version in range(version + 1, CURRENT_SCHEMA_VERSION + 1):
        migration = MIGRATIONS[next_version]
        with conn:
            migration(conn)
            _set_schema_version(conn, next_version)

    if version == 0 and _schema_objects_exist(conn):
        with conn:
            _set_schema_version(conn, CURRENT_SCHEMA_VERSION)


def connect():
    ensure_data_dir()
    db_path = get_db_path()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    migrate(conn)
    return conn


def warn(msg):
    print(f"warning: {msg}", file=sys.stderr)


def require_memos(conn, ids):
    missing = []
    for memo_id in ids:
        if not conn.execute("SELECT id FROM memos WHERE id=?", (memo_id,)).fetchone():
            missing.append(memo_id)
    if missing:
        raise ValueError("memo not found: " + ", ".join(f"#{memo_id}" for memo_id in missing))


def rebuild_fts_index(conn):
    rows = conn.execute("SELECT id, content, tags FROM memos ORDER BY id").fetchall()
    conn.execute("DELETE FROM memos_fts")
    conn.executemany(
        "INSERT INTO memos_fts(rowid, content) VALUES (?, ?)",
        (
            (
                row["id"],
                render_memo_text(
                    json.loads(row["tags"]) if row["tags"] else [],
                    row["content"],
                ),
            )
            for row in rows
        ),
    )
    conn.execute("INSERT INTO memos_fts(memos_fts) VALUES('optimize')")
    return len(rows)


def create_backup(conn=None, out_path=None):
    db_path = get_db_path()
    if out_path is None:
        stamp = time.strftime("%Y%m%d-%H%M%S")
        out_path = get_backups_dir() / f"memo-{stamp}.db"
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if conn is not None:
        target = sqlite3.connect(str(out_path))
        try:
            conn.backup(target)
        finally:
            target.close()
    elif not db_path.exists():
        raise ValueError(f"database not found: {db_path}")
    else:
        source = sqlite3.connect(str(db_path))
        target = sqlite3.connect(str(out_path))
        try:
            source.backup(target)
        finally:
            source.close()
            target.close()
    return out_path


def linked_memos_for(conn, memo_id, limit=None):
    limit_clause = "" if limit is None else "LIMIT ?"
    params = [memo_id, memo_id, memo_id]
    if limit is not None:
        params.append(limit)
    rows = conn.execute(
        f"""
        SELECT
          m.id,
          m.content,
          m.tags,
          m.created_at,
          m.updated_at,
          l.relation_type,
          l.note,
          l.created_at AS linked_at
        FROM memo_links l
        JOIN memos m ON m.id = CASE
          WHEN l.from_memo_id = ? THEN l.to_memo_id
          ELSE l.from_memo_id
        END
        WHERE l.from_memo_id = ? OR l.to_memo_id = ?
        ORDER BY l.created_at DESC
        {limit_clause}
        """,
        params,
    ).fetchall()
    result = []
    for row in rows:
        entry = {
            "id": row["id"],
            "content": row["content"].strip(),
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "created_at": fmt_time(row["created_at"]),
            "relation_type": row["relation_type"],
            "linked_at": fmt_time(row["linked_at"]),
        }
        if row["updated_at"]:
            entry["updated_at"] = fmt_time(row["updated_at"])
        if row["note"]:
            entry["note"] = row["note"]
        result.append(entry)
    return result
