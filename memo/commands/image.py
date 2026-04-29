"""image 子命令 — 生成 memo 分享图"""

import argparse
from pathlib import Path

from .. import get_images_dir


def positive_int(value):
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a non-negative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be >= 0")
    return parsed


def add_parser(sub):
    p = sub.add_parser("image", help="生成分享图")
    p.add_argument("id", type=positive_int)
    p.add_argument("--out", help="输出文件路径")
    p.set_defaults(func=cmd_image)
    return p


def cmd_image(conn, args):
    row = conn.execute("SELECT * FROM memos WHERE id=?", (args.id,)).fetchone()
    if not row:
        raise ValueError(f"memo #{args.id} not found")
    total_memos = conn.execute("SELECT COUNT(*) FROM memos").fetchone()[0]

    if args.out:
        out = Path(args.out)
    else:
        out = get_images_dir() / f"memo-share-{args.id}.png"

    if out.suffix.lower() not in {"", ".png"}:
        raise ValueError("image output requires .png extension")
    if not out.suffix:
        out = out.with_suffix(".png")

    from memo.share_image import render_png

    render_png(row, out, total_memos)
    print(f"saved: {out}")
