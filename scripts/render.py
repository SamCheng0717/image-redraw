#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
render.py — 用 Pillow 生成中文文字卡片图片
"""
import textwrap
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise ImportError("请安装依赖：pip install Pillow")

# Windows 中文字体候选
FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",       # 微软雅黑
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/simsun.ttc",     # 宋体
    "C:/Windows/Fonts/simhei.ttf",     # 黑体
    "/System/Library/Fonts/PingFang.ttc",  # macOS
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux
]

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def get_font(size: int):
    for path in FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_card(text: str, title: str = "", filename: str = None) -> Path:
    """
    将文字渲染为小红书/备忘录风格卡片图片
    返回保存路径
    """
    # ── 配置 ──
    W = 800
    PADDING = 48
    BG_COLOR = (255, 255, 255)
    HEADER_COLOR = (255, 182, 193)   # 粉色 header
    HEADER_HEIGHT = 80
    TITLE_COLOR = (80, 40, 40)
    BODY_COLOR = (50, 50, 50)
    LINE_SPACING = 12
    FONT_TITLE = get_font(32)
    FONT_BODY = get_font(26)
    FONT_SMALL = get_font(20)

    # ── 文字预处理 ──
    max_chars = (W - PADDING * 2) // 26  # 每行最大字符数（粗估）
    lines = []
    for para in text.strip().split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        # 去掉 Markdown 标题符号
        para = para.lstrip("#").strip()
        wrapped = textwrap.wrap(para, width=max_chars) or [""]
        lines.extend(wrapped)

    # ── 计算高度 ──
    body_line_h = 26 + LINE_SPACING
    body_h = len(lines) * body_line_h + PADDING * 2
    total_h = HEADER_HEIGHT + body_h + 40

    # ── 绘制 ──
    img = Image.new("RGB", (W, total_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([(0, 0), (W, HEADER_HEIGHT)], fill=HEADER_COLOR)
    header_text = title[:24] if title else "内容卡片"
    # 居中标题
    bbox = draw.textbbox((0, 0), header_text, font=FONT_TITLE)
    tw = bbox[2] - bbox[0]
    draw.text(((W - tw) // 2, (HEADER_HEIGHT - 36) // 2), header_text,
              font=FONT_TITLE, fill=TITLE_COLOR)

    # Body
    y = HEADER_HEIGHT + PADDING
    for line in lines:
        if line:
            draw.text((PADDING, y), line, font=FONT_BODY, fill=BODY_COLOR)
        y += body_line_h

    # Footer
    ts = datetime.now().strftime("%Y-%m-%d")
    draw.text((PADDING, total_h - 28), ts, font=FONT_SMALL, fill=(180, 180, 180))

    # ── 保存 ──
    if not filename:
        filename = f"card_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    save_path = OUTPUT_DIR / filename
    img.save(str(save_path), "PNG")
    return save_path
