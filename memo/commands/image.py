"""image 子命令 — 生成 memo 分享图"""

import argparse
import subprocess
import sys
from pathlib import Path

from .. import get_images_dir, render_share_svg


def add_parser(sub):
    p = sub.add_parser("image", help="生成分享图")
    p.add_argument("id", type=positive_int)
    p.add_argument("--format", choices=["svg", "png"], help="输出格式")
    p.add_argument("--out", help="输出文件路径")
    p.set_defaults(func=cmd_image)
    return p


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def _png_error_message(message):
    lower = message.lower()
    if "playwright" in lower and (
        "modulenotfounderror" in lower or "no module named" in lower or "cannot import" in lower
    ):
        return (
            "PNG generation requires the optional dependency. "
            'Run: uv tool install --force "a-memo[png]"'
        )
    if "executable doesn't exist" in lower or "browser" in lower and "install" in lower:
        return (
            "PNG generation requires a Chromium-compatible browser. "
            "Run: uv tool run playwright install chromium"
        )
    return message or "png generation failed"


def cmd_image(conn, args):
    row = conn.execute("SELECT * FROM memos WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise ValueError(f"memo #{args.id} not found")
    total_memos = conn.execute("SELECT COUNT(*) FROM memos").fetchone()[0]

    output_format = args.format
    if args.out:
        out = Path(args.out)
        if output_format is None and out.suffix.lower() in {".svg", ".png"}:
            output_format = out.suffix.lower().lstrip(".")
    else:
        output_format = output_format or "png"
        out = get_images_dir() / f"memo-share-{args.id}.{output_format}"
    output_format = output_format or "png"

    if output_format == "svg":
        if out.suffix.lower() not in {"", ".svg"}:
            raise ValueError("svg output requires .svg extension")
        if not out.suffix:
            out = out.with_suffix(".svg")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_share_svg(row, total_memos), encoding="utf-8")
        print(f"saved: {out}")
        return

    if output_format == "png":
        if out.suffix.lower() not in {"", ".png"}:
            raise ValueError("png output requires .png extension")
        if not out.suffix:
            out = out.with_suffix(".png")

        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "memo.share_image",
                "--db",
                str(conn.execute("PRAGMA database_list").fetchone()["file"]),
                "--id",
                str(args.id),
                "--out",
                str(out),
                "--total",
                str(total_memos),
            ],
            text=True,
            capture_output=True,
        )
        if proc.returncode != 0:
            message = proc.stderr.strip() or proc.stdout.strip() or "png generation failed"
            raise RuntimeError(_png_error_message(message))
        print(proc.stdout.strip())
        return

    raise ValueError("format must be svg or png")
