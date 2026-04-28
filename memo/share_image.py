"""生成 memo PNG 分享图（Playwright + Chrome）"""

import argparse
import asyncio
import json
import shutil
import sqlite3
from datetime import datetime, timedelta, timezone
from html import escape
from pathlib import Path

from playwright.async_api import async_playwright

TZ_BJ = timezone(timedelta(hours=8))


def fmt_datetime(ts):
    dt = datetime.fromtimestamp(ts, TZ_BJ)
    return f"{dt.year}/{dt.month:02d}/{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def font_uri(weight="regular"):
    home_fonts = Path.home() / "Library" / "Fonts"
    if weight == "medium":
        candidates = [
            home_fonts / "LXGWWenKai-Medium.ttf",
            home_fonts / "LXGWWenKaiMono-Medium.ttf",
        ]
    else:
        candidates = [
            home_fonts / "LXGWWenKai-Regular.ttf",
            home_fonts / "LXGWWenKai-Light.ttf",
            home_fonts / "LXGWWenKaiMono-Regular.ttf",
        ]
    for path in candidates:
        if path.exists():
            return path.resolve().as_uri()
    return ""


def chrome_executable():
    candidates = [
        shutil.which("google-chrome"),
        shutil.which("chromium"),
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return None


def load_memo(db_path, memo_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM memos WHERE id=?", (memo_id,)).fetchone()
    finally:
        conn.close()
    if not row:
        raise SystemExit(f"memo #{memo_id} 不存在")
    return row


def render_html(row, total_memos):
    tags = json.loads(row["tags"]) if row["tags"] else []
    tag_html = "\n".join(f'<span class="tag">#{escape(tag.lstrip("#"))}</span>' for tag in tags)
    if not tag_html:
        tag_html = '<span class="tag">memo</span>'

    regular_font = font_uri("regular")
    medium_font = font_uri("medium") or regular_font
    regular_face = (
        (
            f'@font-face {{ font-family: "MemoWenKai"; src: url("{regular_font}") '
            'format("truetype"); font-weight: 400; }'
        )
        if regular_font
        else ""
    )
    medium_face = (
        (
            f'@font-face {{ font-family: "MemoWenKai"; src: url("{medium_font}") '
            'format("truetype"); font-weight: 500; }'
        )
        if medium_font
        else ""
    )

    content = escape(row["content"].strip())
    created_at = escape(fmt_datetime(row["created_at"]))
    brand_text = escape(f"{total_memos} memos")

    return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<style>
{regular_face}
{medium_face}
:root {{
  --parchment: #f5f4ed;
  --ivory: #faf9f5;
  --near-black: #141413;
  --stone: #6b6a64;
  --brand: #1B365D;
  --border: #e8e6dc;
  --tag-bg: #E4ECF5;
  --serif: "MemoWenKai", "LXGW WenKai", "Songti SC", "STSong", serif;
}}
* {{ box-sizing: border-box; }}
html, body {{
  margin: 0;
  padding: 0;
  background: var(--parchment);
}}
body {{
  width: 900px;
  color: var(--near-black);
  font-family: var(--serif);
  letter-spacing: 0;
}}
.page {{
  width: 900px;
  padding: 28px;
  background: var(--parchment);
}}
.card {{
  padding: 24px 36px 30px;
  border-radius: 16px;
  background: var(--ivory);
}}
.tags {{
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 0 0 30px;
}}
.tag {{
  display: inline-block;
  padding: 2px 10px 3px;
  border-radius: 3px;
  background: var(--tag-bg);
  color: var(--brand);
  font-size: 22px;
  line-height: 1.15;
  font-weight: 500;
}}
.content {{
  margin: 0;
  color: var(--near-black);
  font-family: var(--serif);
  font-size: 40px;
  line-height: 1.38;
  font-weight: 400;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}}
.footer {{
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-top: 36px;
  color: var(--stone);
  font-size: 23px;
  line-height: 1.3;
  font-weight: 400;
}}
.brand {{
  color: var(--brand);
  font-weight: 500;
}}
</style>
</head>
<body>
  <main class="page">
    <section class="card">
      <div class="tags">{tag_html}</div>
      <pre class="content">{content}</pre>
      <footer class="footer">
        <span>创建于：{created_at}</span>
        <span class="brand">{brand_text}</span>
      </footer>
    </section>
  </main>
</body>
</html>"""


async def render_png(row, out_path, total_memos):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    executable = chrome_executable()
    launch_args = {"headless": True}
    if executable:
        launch_args["executable_path"] = executable

    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_args)
        page = await browser.new_page(viewport={"width": 900, "height": 800}, device_scale_factor=1)
        await page.set_content(render_html(row, total_memos), wait_until="load")
        await page.evaluate("document.fonts && document.fonts.ready")
        await page.locator(".page").screenshot(path=str(out_path), animations="disabled")
        await browser.close()


def parse_args():
    parser = argparse.ArgumentParser(description="生成 memo PNG 分享图")
    parser.add_argument("--db", required=True)
    parser.add_argument("--id", required=True, type=int)
    parser.add_argument("--out", required=True)
    parser.add_argument("--total", required=True, type=int)
    return parser.parse_args()


def main():
    args = parse_args()
    row = load_memo(args.db, args.id)
    asyncio.run(render_png(row, Path(args.out), args.total))
    print(f"saved: {args.out}")


if __name__ == "__main__":
    main()
