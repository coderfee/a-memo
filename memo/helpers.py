"""共用的格式化、解析、渲染工具函数"""

import random
import re
import unicodedata
from datetime import datetime, timedelta, timezone

TZ_BJ = timezone(timedelta(hours=8))
TAG_PATTERN = r"#[\w一-鿿][\w一-鿿.-]*(?:/[\w一-鿿][\w一-鿿.-]*)*"

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
