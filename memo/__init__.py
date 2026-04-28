"""memo CLI 核心模块"""

import json
import os
import sqlite3
import sys
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
    render_share_svg,
    review_layer_bounds,
    split_tags_and_content,
    validate_relation_type,
    wrap_text,
)

__all__ = [
    "choose_review_layer",
    "clean_content",
    "connect",
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
    "history_file_path",
    "is_db_initialized",
    "linked_memos_for",
    "normalize_link_ids",
    "parse_tags",
    "render_memo_text",
    "render_share_svg",
    "require_memos",
    "review_layer_bounds",
    "split_tags_and_content",
    "validate_relation_type",
    "warn",
    "wrap_text",
]

SCHEMA = """
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


def connect():
    ensure_data_dir()
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript(SCHEMA)
    conn.commit()
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
