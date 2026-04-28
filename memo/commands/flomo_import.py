"""flomo_import 子命令 — 从 flomo HTML 导出文件导入"""

import json
import re
import sys
import time
from html.parser import HTMLParser
from pathlib import Path
from typing import TypedDict

from .. import render_memo_text, split_tags_and_content


class ParsedMemo(TypedDict):
    time: str
    content: str


class CurrentMemo(TypedDict):
    time: str
    content: list[str]


def add_parser(sub):
    p = sub.add_parser("flomo-import", help="从 flomo HTML 导入")
    p.add_argument("html_path", type=Path)
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(func=cmd_flomo_import)
    return p


class FlomoHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.memos: list[ParsedMemo] = []
        self.memo_depth = 0
        self.current: CurrentMemo | None = None
        self.field: str | None = None
        self.field_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = set(attrs.get("class", "").split())

        if tag == "div" and "memo" in classes:
            self.current = {"time": "", "content": []}
            self.memo_depth = 1
            self.field = None
            self.field_depth = 0
            return

        if self.current is None:
            return

        self.memo_depth += 1

        if tag == "div" and "time" in classes:
            self.field = "time"
            self.field_depth = self.memo_depth
        elif tag == "div" and "content" in classes:
            self.field = "content"
            self.field_depth = self.memo_depth
        elif self.field == "content" and tag in {"p", "li", "br"}:
            self._append_content("\n")

    def handle_endtag(self, tag):
        if self.current is None:
            return

        if self.field and self.memo_depth == self.field_depth:
            self.field = None
            self.field_depth = 0

        self.memo_depth -= 1
        if self.memo_depth == 0:
            content = _clean_text("".join(self.current["content"]))
            ts = _clean_text(self.current["time"])
            if ts or content:
                self.memos.append({"time": ts, "content": content})
            self.current = None
            self.field = None
            self.field_depth = 0

    def handle_data(self, data):
        if self.current is None or not self.field:
            return
        if self.field == "time":
            self.current["time"] += data
        elif self.field == "content":
            self._append_content(data)

    def _append_content(self, text):
        if self.current is None:
            return
        self.current["content"].append(text)


def _clean_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_html(path) -> list[ParsedMemo]:
    parser = FlomoHTMLParser()
    parser.feed(Path(path).read_text(encoding="utf-8"))
    parser.close()
    return parser.memos


def parse_datetime(value):
    try:
        return time.mktime(time.strptime(value.strip(), "%Y-%m-%d %H:%M:%S"))
    except ValueError as exc:
        raise ValueError(f"invalid datetime format: {value}") from exc


def cmd_flomo_import(conn, args):
    if not args.html_path.exists():
        print(f"file not found: {args.html_path}", file=sys.stderr)
        return 1

    try:
        memos = parse_html(args.html_path)
    except OSError as exc:
        print(f"failed to read file: {exc}", file=sys.stderr)
        return 1

    print(f"parsed {len(memos)} memos")

    imported = 0
    skipped = 0
    failed = 0

    if args.dry_run:
        for memo in memos:
            if not memo["content"]:
                skipped += 1
                continue
            tags, content = split_tags_and_content(memo["content"])
            if not content:
                skipped += 1
                continue
            print(
                f"[dry] {memo['time']} | {render_memo_text(tags, content)[:50]}... | tags: {tags}"
            )
            imported += 1
        print(f"\nimported {imported}, skipped {skipped}, failed {failed}")
        print("(dry-run: no data written)")
        return 0

    for memo in memos:
        if not memo["content"]:
            skipped += 1
            continue
        tags, content = split_tags_and_content(memo["content"])
        if not content:
            skipped += 1
            continue
        try:
            ts = parse_datetime(memo["time"])
            with conn:
                cur = conn.execute(
                    """
                    INSERT INTO memos (content, tags, created_at, source)
                    VALUES (?, ?, ?, 'flomo')
                    """,
                    (content, json.dumps(tags, ensure_ascii=False), ts),
                )
                conn.execute(
                    "INSERT INTO memos_fts(rowid, content) VALUES (?, ?)",
                    (cur.lastrowid, render_memo_text(tags, content)),
                )
            imported += 1
        except Exception as exc:
            failed += 1
            print(f"failed: {memo.get('time', '')} | {exc}", file=sys.stderr)

    print(f"\nimported {imported}, skipped {skipped}, failed {failed}")
    return 1 if failed else 0
