"""共用的格式化、解析、渲染工具函数"""
import json
import os
import random
import re
import time
import unicodedata
from datetime import datetime, timezone, timedelta
from html import escape
from pathlib import Path

TZ_BJ = timezone(timedelta(hours=8))
TAG_PATTERN = r'#[\w一-鿿][\w一-鿿.-]*(?:/[\w一-鿿][\w一-鿿.-]*)*'

KAMI_PARCHMENT = "#f5f4ed"
KAMI_IVORY = "#faf9f5"
KAMI_INK = "#1B365D"
KAMI_TAG_BG = "#E4ECF5"
KAMI_NEAR_BLACK = "#141413"
KAMI_OLIVE = "#504e49"
KAMI_STONE = "#6b6a64"
KAMI_BORDER = "#e8e6dc"

RELATION_TYPES = {"related", "supports", "contrasts"}
REVIEW_LAYERS = (
    ("fresh", 0.20),
    ("middle", 0.45),
    ("old", 0.35),
)
REVIEW_FALLBACK_LAYERS = ("old", "middle", "fresh")


# ── tags ──────────────────────────────────────────────────────────────────────

def parse_tags(text):
    tags = re.findall(TAG_PATTERN, text, re.UNICODE)
    return list(dict.fromkeys(t.lower() for t in tags))


def clean_content(text):
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def remove_tags(text):
    return clean_content(re.sub(TAG_PATTERN, "", text, flags=re.UNICODE))


def split_tags_and_content(text):
    return parse_tags(text), remove_tags(text)


def render_memo_text(tags, content):
    tag_str = " ".join(f"#{tag.lstrip('#')}" for tag in tags)
    if tag_str and content:
        return f"{tag_str} {content}"
    return tag_str or content


# ── time ──────────────────────────────────────────────────────────────────────

def fmt_time(ts):
    dt = datetime.fromtimestamp(ts, TZ_BJ)
    return f"{dt.year}/{dt.month:02d}/{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}:{dt.second:02d}"


def fmt_datetime(ts):
    return fmt_time(ts)


def fmt_review_time(ts):
    return fmt_time(ts)


def fmt_history_time(ts):
    return fmt_time(ts)


def history_file_path(ts, history_dir):
    dt = datetime.fromtimestamp(ts, TZ_BJ)
    return history_dir / f"{dt.year}-{dt.month:02d}-{dt.day:02d}.md"


# ── text wrap ─────────────────────────────────────────────────────────────────

def text_units(text):
    total = 0
    for char in text:
        total += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return total


def wrap_line(line, max_units):
    if not line:
        return [""]
    lines = []
    current = ""
    current_units = 0
    for char in line:
        unit = 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
        if current and current_units + unit > max_units:
            lines.append(current)
            current = char
            current_units = unit
        else:
            current += char
            current_units += unit
    if current:
        lines.append(current)
    return lines


def wrap_text(text, max_units):
    lines = []
    for paragraph in text.splitlines():
        lines.extend(wrap_line(paragraph, max_units))
    return lines


# ── SVG rendering ─────────────────────────────────────────────────────────────

def svg_text_line(text, x, y, size, fill="#171717", weight=400):
    return (
        f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" '
        f'font-weight="{weight}" font-family="LXGW WenKai, LXGW WenKai Screen, '
        f'LXGW WenKai GB, PingFang SC, Hiragino Sans GB, Microsoft YaHei, sans-serif">'
        f"{escape(text)}</text>"
    )


def svg_rect(x, y, width, height, fill, stroke=None, radius=0, stroke_width=1):
    attrs = [
        f'x="{x}"',
        f'y="{y}"',
        f'width="{width}"',
        f'height="{height}"',
        f'fill="{fill}"',
    ]
    if radius:
        attrs.append(f'rx="{radius}"')
    if stroke:
        attrs.append(f'stroke="{stroke}"')
        attrs.append(f'stroke-width="{stroke_width}"')
    return f"<rect {' '.join(attrs)}/>"


def tag_chip_width(tag, font_size=24):
    return 24 + text_units(tag) * font_size * 0.48


def render_share_svg(row, total_memos, width=900):
    tags = json.loads(row["tags"]) if row["tags"] else []
    tag_items = [f"#{tag.lstrip('#')}" for tag in tags]
    content = row["content"].strip()
    created_at = fmt_datetime(row["created_at"])

    margin_x = 64
    margin_top = 52
    card_margin = 28
    content_x = margin_x
    max_units = 36
    content_lines = wrap_text(content, max_units)

    chip_rows = []
    current_row = []
    current_width = 0
    max_chip_width = width - margin_x * 2 - 40
    for tag in tag_items:
        chip_width = tag_chip_width(tag)
        if current_row and current_width + chip_width + 10 > max_chip_width:
            chip_rows.append(current_row)
            current_row = [tag]
            current_width = chip_width
        else:
            current_row.append(tag)
            current_width += chip_width + 10
    if current_row:
        chip_rows.append(current_row)

    content_line_height = 54
    chip_row_height = 34
    footer_gap = 36
    bottom_gap = 52
    footer_y = (
        margin_top
        + max(1, len(chip_rows)) * chip_row_height
        + 30
        + len(content_lines) * content_line_height
        + footer_gap
    )
    height = max(360, footer_y + bottom_gap)

    y = margin_top
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        svg_rect(0, 0, "100%", "100%", KAMI_PARCHMENT),
        svg_rect(card_margin, card_margin, width - card_margin * 2, height - card_margin * 2, KAMI_IVORY, radius=16),
    ]

    if chip_rows:
        for row_tags in chip_rows:
            x = content_x
            for tag in row_tags:
                chip_width = tag_chip_width(tag)
                elements.append(svg_rect(x, y - 25, chip_width, 30, KAMI_TAG_BG, radius=3))
                elements.append(svg_text_line(tag, x + 12, y - 4, 22, KAMI_INK, 500))
                x += chip_width + 10
            y += chip_row_height
    else:
        elements.append(svg_text_line("memo", content_x, y, 22, KAMI_INK, 500))
        y += chip_row_height

    y += 30
    for line in content_lines:
        elements.append(svg_text_line(line, content_x, y, 40, KAMI_NEAR_BLACK, 500))
        y += content_line_height

    elements.append(svg_text_line(f"创建于：{created_at}", content_x, footer_y, 23, KAMI_STONE, 400))
    brand_text = f"{total_memos} memos"
    brand_width = 10 + text_units(brand_text) * 23 * 0.48
    elements.append(svg_text_line(brand_text, width - margin_x - brand_width, footer_y, 23, KAMI_INK, 600))
    elements.append("</svg>")
    return "\n".join(elements)


# ── review ─────────────────────────────────────────────────────────────────────

def choose_review_layer():
    roll = random.random()
    cursor = 0
    for layer, probability in REVIEW_LAYERS:
        cursor += probability
        if roll < cursor:
            return layer
    return REVIEW_LAYERS[-1][0]


def review_layer_bounds(layer):
    if layer == "fresh":
        return 7, 30
    if layer == "middle":
        return 30, 180
    if layer == "old":
        return 180, None
    raise ValueError(f"unknown review layer: {layer}")


# ── search ────────────────────────────────────────────────────────────────────

def fts_query(text):
    tokens = re.findall(r"[\w一-鿿]+", text.lower(), re.UNICODE)
    escaped = [token.replace('"', '""') for token in tokens]
    return " ".join(f'"{token}"*' for token in escaped if token)


# ── link ──────────────────────────────────────────────────────────────────────

def normalize_link_ids(left_id, right_id):
    if left_id == right_id:
        raise ValueError("cannot link a memo to itself")
    return (left_id, right_id) if left_id < right_id else (right_id, left_id)


def validate_relation_type(value):
    relation_type = value.lower()
    if relation_type not in RELATION_TYPES:
        allowed = ", ".join(sorted(RELATION_TYPES))
        raise ValueError(f"relation type must be one of: {allowed}")
    return relation_type