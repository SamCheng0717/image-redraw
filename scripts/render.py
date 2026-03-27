#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — 生成视觉精美的中文内容卡片
"""
import textwrap
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont, ImageFilter
except ImportError:
    raise ImportError("请安装依赖：pip install Pillow")

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]

# 配色方案
THEMES = {
    "rose": {
        "grad_top":    (255, 220, 225),   # 浅玫瑰
        "grad_bottom": (255, 245, 248),   # 近白
        "card_bg":     (255, 255, 255),   # 卡片白
        "accent":      (220, 90, 110),    # 深玫红
        "title_fg":    (180, 50, 70),
        "body_fg":     (55, 45, 45),
        "meta_fg":     (180, 160, 160),
        "dot":         (240, 150, 165),
    },
    "sage": {
        "grad_top":    (220, 235, 225),
        "grad_bottom": (245, 250, 247),
        "card_bg":     (255, 255, 255),
        "accent":      (80, 140, 110),
        "title_fg":    (50, 110, 80),
        "body_fg":     (45, 55, 50),
        "meta_fg":     (160, 180, 170),
        "dot":         (140, 190, 165),
    },
}


def get_font(size: int, bold: bool = False):
    candidates = FONT_CANDIDATES if not bold else [
        "C:/Windows/Fonts/msyhbd.ttc",
        "C:/Windows/Fonts/msyh.ttc",
    ] + FONT_CANDIDATES
    for path in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def gradient_bg(w: int, h: int, c1: tuple, c2: tuple) -> Image.Image:
    """垂直渐变背景"""
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        r = int(c1[0] + (c2[0] - c1[0]) * y / h)
        g = int(c1[1] + (c2[1] - c1[1]) * y / h)
        b = int(c1[2] + (c2[2] - c1[2]) * y / h)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img


def draw_rounded_rect(draw, xy, radius, fill, outline=None, outline_width=2):
    """绘制圆角矩形"""
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill,
                            outline=outline, width=outline_width)


def render_card(text: str, title: str = "", filename: str = None,
                theme: str = "rose") -> Path:
    """
    渲染精美内容卡片
    """
    t = THEMES.get(theme, THEMES["rose"])

    W = 820
    CARD_PAD_H = 56     # 卡片左右内边距
    CARD_PAD_V = 44     # 卡片上下内边距
    CARD_MARGIN = 36    # 卡片距画布边距
    HEADER_H = 88
    FOOTER_H = 48

    font_title = get_font(30, bold=True)
    font_body  = get_font(26)
    font_small = get_font(19)

    # ── 预处理文字 ──
    max_chars = (W - CARD_MARGIN * 2 - CARD_PAD_H * 2) // 27
    MAX_LINES = 28  # 超出自动截断，避免卡片过长
    lines = []
    for para in text.strip().split("\n"):
        para = para.strip().lstrip("#").strip()
        if not para:
            lines.append("")
            continue
        # 去掉 Markdown 粗体/分隔线
        para = re.sub(r'\*\*(.+?)\*\*', r'\1', para)
        if para.startswith("---"):
            continue
        for wrapped in textwrap.wrap(para, width=max_chars) or [""]:
            lines.append(wrapped)
        if len(lines) >= MAX_LINES:
            lines.append("…")
            break

    # ── 计算高度 ──
    line_h = 30
    body_h = sum(line_h if l else line_h // 2 for l in lines)
    card_h = HEADER_H + CARD_PAD_V + body_h + CARD_PAD_V + FOOTER_H
    total_h = CARD_MARGIN + card_h + CARD_MARGIN + 20

    # ── 背景 ──
    img = gradient_bg(W, total_h, t["grad_top"], t["grad_bottom"])
    draw = ImageDraw.Draw(img)

    # 装饰圆点（右上、左下）
    for cx, cy, r in [(W - 50, 50, 80), (50, total_h - 50, 60)]:
        draw.ellipse([cx-r, cy-r, cx+r, cy+r],
                     fill=(*t["dot"], 60) if len(t["dot"]) == 3 else t["dot"])

    # ── 卡片阴影（伪阴影：略大一圈的深色圆角矩形）──
    sx, sy = CARD_MARGIN, CARD_MARGIN
    ex, ey = W - CARD_MARGIN, CARD_MARGIN + card_h
    shadow_offset = 6
    draw_rounded_rect(draw,
                      (sx + shadow_offset, sy + shadow_offset,
                       ex + shadow_offset, ey + shadow_offset),
                      radius=20, fill=(200, 185, 190))

    # ── 卡片主体 ──
    draw_rounded_rect(draw, (sx, sy, ex, ey), radius=20,
                      fill=t["card_bg"], outline=None)

    # ── Header ──
    # 左侧强调色竖条
    draw.rounded_rectangle([sx, sy, sx + 8, sy + HEADER_H], radius=4,
                            fill=t["accent"])
    # 标题文字
    title_display = title[:28] if title else "内容卡片"
    bbox = draw.textbbox((0, 0), title_display, font=font_title)
    tw = bbox[2] - bbox[0]
    tx = sx + CARD_PAD_H
    ty = sy + (HEADER_H - (bbox[3] - bbox[1])) // 2
    draw.text((tx, ty), title_display, font=font_title, fill=t["title_fg"])

    # Header 分隔线
    draw.line([(sx + 24, sy + HEADER_H), (ex - 24, sy + HEADER_H)],
              fill=(*t["accent"][:3], 60) if True else t["accent"], width=1)

    # ── 正文 ──
    y = sy + HEADER_H + CARD_PAD_V
    for line in lines:
        if line:
            draw.text((sx + CARD_PAD_H, y), line, font=font_body, fill=t["body_fg"])
            y += line_h
        else:
            y += line_h // 2

    # ── Footer ──
    footer_y = ey - FOOTER_H + 14
    draw.line([(sx + 24, ey - FOOTER_H), (ex - 24, ey - FOOTER_H)],
              fill=(*t["meta_fg"][:3], 80) if True else t["meta_fg"], width=1)
    ts_str = datetime.now().strftime("%Y-%m-%d")
    draw.text((sx + CARD_PAD_H, footer_y), ts_str,
              font=font_small, fill=t["meta_fg"])

    # ── 保存 ──
    if not filename:
        filename = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = OUTPUT_DIR / filename
    # 轻微模糊装饰圆点（让背景更柔和）
    img = img.filter(ImageFilter.SMOOTH_MORE) if False else img
    img.save(str(save_path), "PNG")
    return save_path


import re  # 补充 import（render.py 内部使用）
