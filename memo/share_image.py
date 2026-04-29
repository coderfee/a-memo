"""Render memo share images as PNG."""

import json
from pathlib import Path

from .helpers import (
    KAMI_INK,
    KAMI_IVORY,
    KAMI_NEAR_BLACK,
    KAMI_PARCHMENT,
    KAMI_STONE,
    KAMI_TAG_BG,
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
    return int(draw.textlength(tag, font=font) / scale + 24)


def _chip_rows(draw, tags, width, margin_x, font, scale):
    rows = []
    current = []
    current_width = 0
    max_width = width - margin_x * 2 - 40
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
    if total_units <= 34 and units <= 28:
        size = 32
    elif total_units <= 72 and units <= 36:
        size = 30
    elif total_units <= 140:
        size = 28
    else:
        size = 24
    return size, int(size * 1.52)


def render_png(row, out_path, total_memos, width=600):
    Image, ImageDraw, ImageFont = _load_pillow()

    scale = 3
    canvas_width = width * scale
    out_path = Path(out_path)

    tags = json.loads(row["tags"]) if row["tags"] else []
    tag_items = [f"#{tag.lstrip('#')}" for tag in tags] or ["memo"]
    content = row["content"].strip()
    content_size, content_line_h = _content_metrics(content)
    created_at = fmt_datetime(row["created_at"])
    brand_text = f"{total_memos} memos"

    card_margin = 28
    card_pad_y = 36
    content_x = 44
    content_right = width - 44
    tag_h = 30
    tag_row_gap = 4
    content_gap = 30
    footer_gap = 36
    footer_h = 30
    tag_font = _font(ImageFont, 22 * scale, "medium")
    content_font = _font(ImageFont, content_size * scale, "medium")
    footer_font = _font(ImageFont, 23 * scale)
    footer_brand_font = _font(ImageFont, 23 * scale, "medium")

    def s(value):
        return int(round(value * scale))

    measure = Image.new("RGB", (1, 1), KAMI_PARCHMENT)
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
    image = Image.new("RGB", (canvas_width, height * scale), KAMI_PARCHMENT)
    draw = ImageDraw.Draw(image)

    draw.rounded_rectangle(
        (s(card_margin), s(card_margin), s(width - card_margin), s(height - card_margin)),
        radius=s(16),
        fill=KAMI_IVORY,
    )

    y = tag_top
    for row_tags in rows:
        x = content_x
        for tag in row_tags:
            chip_width = _chip_width(draw, tag, tag_font, scale)
            draw.rounded_rectangle(
                (s(x), s(y), s(x + chip_width), s(y + tag_h)),
                radius=s(3),
                fill=KAMI_TAG_BG,
            )
            _draw_text_center_y(draw, (s(x + 12), s(y)), tag, tag_font, KAMI_INK, s(tag_h))
            x += chip_width + 10
        y += tag_h + tag_row_gap

    y = content_top
    for line in content_lines:
        _draw_text_center_y(
            draw,
            (s(content_x), s(y)),
            line,
            content_font,
            KAMI_NEAR_BLACK,
            s(content_line_h),
        )
        y += content_line_h

    _draw_text_center_y(
        draw,
        (s(content_x), s(footer_top)),
        created_at,
        footer_font,
        KAMI_STONE,
        s(footer_h),
    )
    brand_width = draw.textlength(brand_text, font=footer_brand_font) / scale
    _draw_text_center_y(
        draw,
        (s(content_right - brand_width), s(footer_top)),
        brand_text,
        footer_brand_font,
        KAMI_INK,
        s(footer_h),
    )

    image = image.resize((width, height), Image.Resampling.LANCZOS)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(out_path, "PNG")
    return out_path
