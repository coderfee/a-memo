"""review 子命令"""
import argparse
import json
import time

from .. import (
    connect,
    fmt_time,
    linked_memos_for,
    history_file_path,
    get_history_dir,
    render_memo_text,
)


def add_parser(sub):
    p = sub.add_parser("review", help="回顾 memos")
    p.add_argument("--count", type=positive_int, default=5)
    p.add_argument("--push", action="store_true")
    p.set_defaults(func=cmd_review)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def select_review_row_from_layer(conn, layer):
    min_days, max_days = _layer_bounds(layer)
    max_filter = "" if max_days is None else "AND days_since_review < ?"
    params = [min_days]
    if max_days is not None:
        params.append(max_days)
    return conn.execute(
        f"""
        WITH eligible AS (
          SELECT
            *,
            COALESCE(last_review_at, created_at) as sort_time,
            ((unixepoch() - COALESCE(last_review_at, created_at)) / 86400.0) as days_since_review
          FROM memos
        ),
        weighted AS (
          SELECT *,
            (days_since_review / (review_count + 1)) *
            (0.7 + abs(random() / 9223372036854775808.0) * 0.6) as score
          FROM eligible
          WHERE days_since_review >= ?
          {max_filter}
        )
        SELECT id, content, tags, created_at, updated_at, review_count
        FROM weighted ORDER BY score DESC LIMIT 1
        """,
        params,
    ).fetchone()


def _layer_bounds(layer):
    if layer == "fresh":
        return 7, 30
    if layer == "middle":
        return 30, 180
    if layer == "old":
        return 180, None
    raise ValueError(f"unknown review layer: {layer}")


def _fallback_layers(layer):
    order = ("fresh", "middle", "old")
    idx = order.index(layer) if layer in order else -1
    return (*order[idx+1:], *order[:idx+1])


def select_single_review_row(conn):
    from ..helpers import choose_review_layer
    selected = choose_review_layer()
    for layer in (selected, *_fallback_layers(selected)):
        row = select_review_row_from_layer(conn, layer)
        if row:
            return row
    return None


def cmd_review(conn, args):
    if args.count == 1:
        row = select_single_review_row(conn)
        rows = [row] if row else []
    else:
        rows = conn.execute("""
          WITH eligible AS (
            SELECT *, COALESCE(last_review_at, created_at) as sort_time
            FROM memos
            WHERE COALESCE(last_review_at, created_at) < (unixepoch() - 604800)
          ),
          weighted AS (
            SELECT *,
              (1.0 / (review_count + 1)) *
              ((unixepoch() - sort_time) / 86400.0) as weight
            FROM eligible
          )
          SELECT id, content, tags, created_at, updated_at, review_count
          FROM weighted ORDER BY weight DESC LIMIT ?
        """, (args.count,)).fetchall()

    if not rows:
        print("[]")
        return

    ids = [row["id"] for row in rows]

    result = []
    for row in rows:
        tags = json.loads(row["tags"]) if row["tags"] else []
        result.append({
            "id": row["id"],
            "content": row["content"].strip(),
            "tags": tags,
            "created_at": fmt_time(row["created_at"]) if row["created_at"] else None,
            "updated_at": fmt_time(row["updated_at"]) if row["updated_at"] else None,
            "review_count": row["review_count"] or 0,
            "links": linked_memos_for(conn, row["id"]),
        })

    print(json.dumps(result, ensure_ascii=False, indent=2))

    if args.push and ids:
        now = time.time()
        _append_history(rows, now)
        placeholders = ",".join("?" * len(ids))
        with conn:
            conn.execute(
                f"UPDATE memos SET review_count=review_count+1, last_review_at=? WHERE id IN ({placeholders})",
                [now] + ids,
            )


def _append_history(rows, reviewed_at=None):
    if not rows:
        return
    reviewed_at = reviewed_at or time.time()
    history_dir = get_history_dir()
    history_dir.mkdir(parents=True, exist_ok=True)
    out = history_file_path(reviewed_at, history_dir)

    from .. import fmt_history_time
    entries = []
    for row in rows:
        tags = json.loads(row["tags"]) if row["tags"] else []
        memo = render_memo_text(tags, row["content"].strip())
        entries.append(f"{fmt_history_time(reviewed_at)}\n{memo}\n---")

    prefix = ""
    if out.exists() and out.stat().st_size > 0:
        with out.open("rb") as fh:
            fh.seek(-1, os.SEEK_END)
            if fh.read(1) != b"\n":
                prefix = "\n"

    with out.open("a", encoding="utf-8") as fh:
        fh.write(prefix + "\n".join(entries) + "\n")


import os