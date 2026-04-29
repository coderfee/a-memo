"""Render memo share images as PNG."""

import json
from pathlib import Path

from .helpers import (
    KAMI_INK,
    KAMI_IVORY,
    KAMI_NEAR_BLACK,
    KAMI_PARCHMENT,
    KAMI_STONE,
    fmt_datetime,
    text_units,
)


def _load_pillow():
    from PIL import Image, ImageDraw, ImageFont

    return Image, ImageDraw, ImageFont


def _font_paths(weight):
    bundled_fonts = Path(__file__).resolve().parent / "assets" / "fonts"
    home_fonts = Path.home() / "Library" / "Fonts"
    if weight == "medium":
        return [
            bundled_fonts / "LXGWWenKai-Medium.ttf",
            home_fonts / "LXGWWenKai-Medium.ttf",
            home_fonts / "LXGWWenKaiMono-Medium.ttf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
            "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    return [
        bundled_fonts / "LXGWWenKai-Regular.ttf",
        home_fonts / "LXGWWenKai-Regular.ttf",
        home_fonts / "LXGWWenKaiMono-Regular.ttf",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]


def _font(font_module, size, weight="regular"):
    for path in _font_paths(weight):
        candidate = Path(path)
        if candidate.exists():
            return font_module.truetype(str(candidate), size=size)
    return font_module.load_default(size=size)


def _text_size(draw, text, font):
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def _draw_text_top(draw, xy, text, font, fill):
    x, top = xy
    bbox = draw.textbbox((0, 0), text, font=font)
    draw.text((x - bbox[0], top - bbox[1]), text, fill=fill, font=font)


def _draw_text_center_y(draw, xy, text, font, fill, box_height):
    x, top = xy
    _, text_height = _text_size(draw, text, font)
    _draw_text_top(draw, (x, top + (box_height - text_height) / 2), text, font, fill)


def _wrap_text_pixels(draw, text, font, max_width):
    leading_punctuation = "，。；：？！、,.!?;:)]}）】》"
    lines = []
    for paragraph in text.splitlines():
        if not paragraph:
            lines.append("")
            continue
        current = ""
        for char in paragraph:
            candidate = current + char
            if current and draw.textlength(candidate, font=font) > max_width:
                if char in leading_punctuation:
                    lines.append(candidate)
                    current = ""
                else:
                    lines.append(current)
                    current = char
            else:
                current = candidate
        if current:
            lines.append(current)
    return lines


def _chip_width(draw, tag, font, scale):
    return int(draw.textlength(tag, font=font) / scale + 20)


def _chip_rows(draw, tags, width, margin_x, font, scale):
    rows = []
    current = []
    current_width = 0
    max_width = width - margin_x * 2
    for tag in tags:
        chip_width = _chip_width(draw, tag, font, scale)
        if current and current_width + chip_width + 10 > max_width:
            rows.append(current)
            current = [tag]
            current_width = chip_width
        else:
            current.append(tag)
            current_width += chip_width + 10
    if current:
        rows.append(current)
    return rows


def _content_metrics(content):
    units = max((text_units(line) for line in content.splitlines()), default=0)
    total_units = text_units(content)
    if total_units <= 36 and units <= 28:
        size = 30
    elif total_units <= 86 and units <= 38:
        size = 28
    elif total_units <= 180:
        size = 25
    elif total_units <= 360:
        size = 23
    else:
        size = 21
    return size, int(size * 1.72)


def _theme(style):
    themes = {
        "clean": {
            "page": "#f6f6f2",
            "card": "#ffffff",
            "shadow": None,
            "border": None,
            "tag_bg": "#eeeeeb",
            "tag_text": "#5c625f",
            "content": "#151514",
            "footer": "#7b7b75",
            "brand": "#3f4643",
            "divider_color": "#deded8",
            "radius": 0,
            "card_margin": 0,
            "pad_y": 50,
            "content_x": 54,
            "tag_radius": 13,
            "shadow_offset": 0,
            "show_divider": True,
        },
        "paper": {
            "page": KAMI_PARCHMENT,
            "card": KAMI_IVORY,
            "shadow": "#eeece2",
            "border": "#e8e4d8",
            "tag_bg": "#edf3f7",
            "tag_text": KAMI_INK,
            "content": KAMI_NEAR_BLACK,
            "footer": KAMI_STONE,
            "brand": KAMI_INK,
            "divider_color": "#ebe7dc",
            "radius": 18,
            "card_margin": 26,
            "pad_y": 38,
            "content_x": 52,
            "tag_radius": 3,
            "shadow_offset": 4,
            "show_divider": True,
        },
        "ink": {
            "page": "#ebe9df",
            "card": "#fbfaf2",
            "shadow": "#dedace",
            "border": "#233a5d",
            "tag_bg": "#233a5d",
            "tag_text": "#f7f5ec",
            "content": "#111827",
            "footer": "#626863",
            "brand": "#172f52",
            "divider_color": "#233a5d",
            "radius": 10,
            "card_margin": 24,
            "pad_y": 42,
            "content_x": 50,
            "tag_radius": 2,
            "shadow_offset": 6,
            "show_divider": True,
        },
    }
    if style not in themes:
        allowed = ", ".join(themes)
        raise ValueError(f"image style must be one of: {allowed}")
    return themes[style]


def render_png(row, out_path, total_memos, width=600, style="paper"):
    Image, ImageDraw, ImageFont = _load_pillow()

    scale = 3
    canvas_width = width * scale
    out_path = Path(out_path)
    theme = _theme(style)

    tags = json.loads(row["tags"]) if row["tags"] else []
    tag_items = [f"#{tag.lstrip('#')}" for tag in tags] or ["memo"]
    content = row["content"].strip()
    content_size, content_line_h = _content_metrics(content)
    created_at = fmt_datetime(row["created_at"])
    brand_text = f"a-memo · {total_memos} memos"

    card_margin = theme["card_margin"]
    card_pad_y = theme["pad_y"]
    content_x = theme["content_x"]
    content_right = width - theme["content_x"]
    tag_h = 26
    tag_row_gap = 6
    content_gap = 34
    footer_gap = 38
    footer_h = 28
    tag_font = _font(ImageFont, 18 * scale, "medium")
    content_font = _font(ImageFont, content_size * scale, "medium")
    footer_font = _font(ImageFont, 18 * scale)
    footer_brand_font = _font(ImageFont, 18 * scale, "medium")

    def s(value):
        return int(round(value * scale))

    measure = Image.new("RGB", (1, 1), theme["page"])
    measure_draw = ImageDraw.Draw(measure)
    rows = _chip_rows(measure_draw, tag_items, width, content_x, tag_font, scale)
    tag_top = card_margin + card_pad_y
    tags_h = len(rows) * tag_h + max(0, len(rows) - 1) * tag_row_gap
    content_top = tag_top + tags_h + content_gap
    content_lines = _wrap_text_pixels(
        measure_draw,
        content,
        content_font,
        s(content_right - content_x),
    )
    footer_top = content_top + len(content_lines) * content_line_h + footer_gap
    content_height = footer_top + footer_h + card_pad_y - card_margin
    height = card_margin * 2 + content_height
    image = Image.new("RGB", (canvas_width, height * scale), theme["page"])
    draw = ImageDraw.Draw(image)

    shadow_offset = theme["shadow_offset"]
    radius = theme["radius"]
    if theme["shadow"]:
        draw.rounded_rectangle(
            (
                s(card_margin + shadow_offset),
                s(card_margin + shadow_offset),
                s(width - card_margin + shadow_offset),
                s(height - card_margin + shadow_offset),
            ),
            radius=s(radius),
            fill=theme["shadow"],
        )
    draw.rounded_rectangle(
        (s(card_margin), s(card_margin), s(width - card_margin), s(height - card_margin)),
        radius=s(radius),
        fill=theme["card"],
        outline=theme["border"],
        width=s(1) if theme["border"] else 0,
    )

    y = tag_top
    for row_tags in rows:
        x = content_x
        for tag in row_tags:
            chip_width = _chip_width(draw, tag, tag_font, scale)
            draw.rounded_rectangle(
                (s(x), s(y), s(x + chip_width), s(y + tag_h)),
                radius=s(theme["tag_radius"]),
                fill=theme["tag_bg"],
            )
            _draw_text_center_y(draw, (s(x + 10), s(y)), tag, tag_font, theme["tag_text"], s(tag_h))
            x += chip_width + 10
        y += tag_h + tag_row_gap

    y = content_top
    for line in content_lines:
        _draw_text_top(
            draw,
            (s(content_x), s(y)),
            line,
            content_font,
            theme["content"],
        )
        y += content_line_h

    if theme["show_divider"]:
        divider_y = footer_top - 14
        draw.line(
            (s(content_x), s(divider_y), s(content_right), s(divider_y)),
            fill=theme["divider_color"],
            width=s(1),
        )
    _draw_text_center_y(
        draw,
        (s(content_x), s(footer_top)),
        created_at,
        footer_font,
        theme["footer"],
        s(footer_h),
    )
    brand_width = draw.textlength(brand_text, font=footer_brand_font) / scale
    _draw_text_center_y(
        draw,
        (s(content_right - brand_width), s(footer_top)),
        brand_text,
        footer_brand_font,
        theme["brand"],
        s(footer_h),
    )

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG")
    return out_path
