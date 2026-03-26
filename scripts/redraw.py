#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image-redraw: 根据文字内容生成图片（阿里云百炼 通义万象）
用法：
    python scripts/redraw.py --text "韩国医美大实话，10条潜规则..."
    python scripts/redraw.py --file input.md
    python scripts/redraw.py --text "内容" --n 2 --size 1024*1024
"""
import argparse
import os
import sys
import re
from http import HTTPStatus
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from urllib.request import urlretrieve

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

try:
    import dashscope
    from dashscope import ImageSynthesis
except ImportError:
    print("[错误] 请先安装依赖：pip install dashscope")
    sys.exit(1)

API_KEY = os.getenv("DASHSCOPE_API_KEY")
OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# 默认模型
DEFAULT_MODEL = "wanx2.1-t2i-turbo"
DEFAULT_SIZE = "1024*1024"


def text_to_prompt(text: str) -> str:
    """将 OCR 文字/用户输入转换为图片生成 prompt"""
    # 截取前 300 字作为核心内容
    core = text.strip()[:300]
    # 统一风格：小红书/社交媒体风格卡片
    prompt = (
        f"简约风格信息图，白色背景，排版精美，"
        f"内容：{core}，"
        f"中文字体清晰，高清，适合社交媒体发布"
    )
    return prompt


def read_input(args) -> str:
    if args.text:
        return args.text
    if args.file:
        path = Path(args.file)
        if not path.exists():
            print(f"[错误] 文件不存在：{args.file}")
            sys.exit(1)
        content = path.read_text(encoding="utf-8")
        # 如果是 Markdown，提取 OCR 内容部分
        ocr_match = re.search(r"### 🔍 OCR 识别内容\n+([\s\S]+?)(?=\n###|\n---|\Z)", content)
        if ocr_match:
            return ocr_match.group(1).strip()
        return content
    print("[错误] 请提供 --text 或 --file 参数")
    sys.exit(1)


def generate_images(prompt: str, n: int, size: str, model: str) -> list:
    """调用通义万象生成图片，返回本地保存路径列表"""
    if not API_KEY:
        print("[错误] 未配置 DASHSCOPE_API_KEY，请在 .env 中设置")
        sys.exit(1)

    print(f"[生成] 模型：{model} | 尺寸：{size} | 数量：{n}")
    print(f"[Prompt] {prompt[:80]}...")

    rsp = ImageSynthesis.call(
        api_key=API_KEY,
        model=model,
        prompt=prompt,
        n=n,
        size=size,
    )

    if rsp.status_code != HTTPStatus.OK:
        print(f"[错误] 生成失败：{rsp.status_code} {rsp.code} {rsp.message}")
        return []

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    saved = []
    for i, result in enumerate(rsp.output.results):
        filename = f"redraw_{ts}_{i+1}.png"
        save_path = OUTPUT_DIR / filename
        urlretrieve(result.url, str(save_path))
        print(f"[✓] 图片保存：{save_path.name}")
        saved.append(save_path)

    return saved


def main():
    parser = argparse.ArgumentParser(description="根据文字内容生成图片")
    parser.add_argument("--text", type=str, help="直接输入文字内容")
    parser.add_argument("--file", type=str, help="读取文件（.md 或 .txt）")
    parser.add_argument("--prompt", type=str, help="直接指定 prompt（跳过自动转换）")
    parser.add_argument("--n", type=int, default=1, help="生成张数（默认 1）")
    parser.add_argument("--size", type=str, default=DEFAULT_SIZE, help="图片尺寸（默认 1024*1024）")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"模型（默认 {DEFAULT_MODEL}）")
    args = parser.parse_args()

    if args.prompt:
        prompt = args.prompt
    else:
        text = read_input(args)
        prompt = text_to_prompt(text)

    saved = generate_images(prompt, args.n, args.size, args.model)

    if saved:
        print(f"\n✓ 完成！生成 {len(saved)} 张图片，保存在 output/")
        for p in saved:
            print(f"  {p}")
    else:
        print("✗ 未生成任何图片")


if __name__ == "__main__":
    main()
