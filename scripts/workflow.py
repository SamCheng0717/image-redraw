#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image-redraw workflow
用法：
    python scripts/workflow.py --input notes_韩国医美.md
    python scripts/workflow.py --input notes_韩国医美.md --my-hospital "我的诊所"
"""
import argparse
import os
import re
import sys
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

# ─────────────────── 医院关键词 ────────────────────
HOSPITAL_KEYWORDS = [
    "医院", "诊所", "皮肤科", "整形", "医美", "门诊",
    "pfk", "PFK", "江南", "弘大", "纯真", "OLIVE",
    "jayjun", "bb皮肤", "弗洛雷斯", "萤仁齐",
    "院长", "主治医", "专科",
]

HOSPITAL_PAT = re.compile(
    r"(" + "|".join(re.escape(k) for k in HOSPITAL_KEYWORDS) + r")",
    re.IGNORECASE
)


def detect_hospital(text: str) -> list:
    """返回文本中检测到的医院相关词列表（去重）"""
    matches = HOSPITAL_PAT.findall(text)
    return list(dict.fromkeys(matches))  # 保序去重


# ─────────────────── 解析 Markdown ────────────────────
def parse_notes_md(md_path: Path) -> list:
    """解析 douyin-scraper 输出的 Markdown，返回笔记列表"""
    text = md_path.read_text(encoding="utf-8")
    notes = []

    # 按 ## 笔记 N 分割
    blocks = re.split(r'\n(?=## 笔记 \d+)', text)
    for block in blocks:
        if not block.strip().startswith("## 笔记"):
            continue
        note = {}

        # 标题
        m = re.search(r'## 笔记 \d+ — (.+)', block)
        note["title"] = m.group(1).strip() if m else ""

        # 链接
        m = re.search(r'\*\*🔗 链接\*\*：(https?://\S+)', block)
        note["url"] = m.group(1).strip() if m else ""

        # OCR 内容
        m = re.search(r'### 🔍 OCR 识别内容\n+([\s\S]+?)(?=\n###|\n---|\Z)', block)
        note["ocr"] = m.group(1).strip() if m else ""

        if note["ocr"]:
            notes.append(note)

    return notes


# ─────────────────── LLM 改写 ────────────────────
def rewrite_with_llm(text: str, instruction: str) -> str:
    """用 Qwen 改写文本"""
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("  [警告] 未配置 DASHSCOPE_API_KEY，跳过 LLM 改写")
        return text

    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        resp = client.chat.completions.create(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "你是一个内容编辑助手，帮助改写医美内容文案。保持原有格式和结构，只修改指定内容。"},
                {"role": "user", "content": f"{instruction}\n\n原文：\n{text}"}
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"  [LLM错误] {e}")
        return text


# ─────────────────── 主流程 ────────────────────
def process_note(note: dict, idx: int, my_hospital: str, auto: bool) -> dict:
    """处理单篇笔记，返回处理结果"""
    title = note["title"][:40]
    ocr = note["ocr"]
    hospitals = detect_hospital(ocr)

    print(f"\n{'='*60}")
    print(f"笔记 {idx}: {title}")
    print(f"链接: {note['url']}")
    print(f"{'='*60}")

    result = {
        "idx": idx,
        "title": title,
        "url": note["url"],
        "original_ocr": ocr,
        "final_text": ocr,
        "action": "direct",   # direct / rewrite / skip
        "image_path": None,
    }

    if not hospitals:
        print("  ✅ 未检测到医院信息 → 可直接转发")
        result["action"] = "direct"

        if not auto:
            choice = input("  是否生成图片？[y/N] ").strip().lower()
            if choice != "y":
                return result
    else:
        print(f"  ⚠️  检测到医院/机构信息：{', '.join(hospitals)}")
        print()
        print("  原文预览：")
        for line in ocr.split("\n")[:8]:
            if line.strip():
                print(f"    {line}")
        print()

        if auto:
            choice = "1"
        else:
            print("  请选择操作：")
            print("  [1] 替换医院信息并改写文案")
            print("  [2] 只修改部分文字（自定义指令）")
            print("  [3] 直接转发（不改）")
            print("  [4] 跳过")
            choice = input("  选择 [1/2/3/4]: ").strip()

        if choice == "4":
            result["action"] = "skip"
            print("  ⏭️  已跳过")
            return result

        elif choice == "3":
            result["action"] = "direct"
            print("  ➡️  直接转发，生成图片...")

        elif choice == "1":
            result["action"] = "rewrite"
            hospital_info = my_hospital
            if not hospital_info and not auto:
                hospital_info = input("  请输入你的医院/诊所名称及简介（回车跳过）：").strip()

            if hospital_info:
                instruction = (
                    f"将文中所有竞品医院/机构名称（{', '.join(hospitals)}）"
                    f"替换为「{hospital_info}」，"
                    f"保持文章结构和风格，语言自然流畅。"
                )
            else:
                instruction = (
                    f"将文中所有竞品医院/机构名称（{', '.join(hospitals)}）"
                    f"改为「某知名医院」，保持结构和风格。"
                )

            print("  ✍️  正在改写...")
            rewritten = rewrite_with_llm(ocr, instruction)

            print("\n  改写结果预览：")
            for line in rewritten.split("\n")[:10]:
                if line.strip():
                    print(f"    {line}")
            print()

            if not auto:
                confirm = input("  确认使用此改写结果？[Y/n] ").strip().lower()
                if confirm == "n":
                    custom = input("  请输入自定义修改指令（或直接粘贴修改后的文本）：\n  > ").strip()
                    if custom:
                        if len(custom) > 50:
                            rewritten = custom
                        else:
                            rewritten = rewrite_with_llm(ocr, custom)

            result["final_text"] = rewritten

        elif choice == "2":
            result["action"] = "rewrite"
            if not auto:
                instruction = input("  请输入修改指令：\n  > ").strip()
            else:
                instruction = "优化文案，使其更适合社交媒体传播"

            print("  ✍️  正在改写...")
            rewritten = rewrite_with_llm(ocr, instruction)
            result["final_text"] = rewritten

    # ── 生成图片 ──
    try:
        from render import render_card
    except ImportError:
        sys.path.insert(0, str(Path(__file__).parent))
        from render import render_card

    filename = f"note_{idx:02d}_{datetime.now().strftime('%H%M%S')}.png"
    img_path = render_card(
        text=result["final_text"],
        title=title,
        filename=filename
    )
    result["image_path"] = img_path
    print(f"  🖼️  图片已生成：{img_path.name}")

    return result


def generate_report(results: list, output_dir: Path) -> Path:
    """生成发布清单 Markdown"""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 发布清单", "",
        f"生成时间：{ts}", "",
        f"共 {len(results)} 篇，"
        f"可直接转发：{sum(1 for r in results if r['action']=='direct')} 篇，"
        f"已改写：{sum(1 for r in results if r['action']=='rewrite')} 篇，"
        f"已跳过：{sum(1 for r in results if r['action']=='skip')} 篇",
        "", "---",
    ]

    for r in results:
        status = {"direct": "✅ 直接转发", "rewrite": "✏️ 已改写", "skip": "⏭️ 跳过"}[r["action"]]
        lines += [
            f"\n## {r['idx']}. {r['title']}",
            f"**状态**：{status}",
            f"**链接**：{r['url']}",
        ]
        if r["image_path"]:
            lines.append(f"**图片**：`{r['image_path']}`")
        if r["action"] == "rewrite":
            lines += ["", "**改写后文案**：", "", r["final_text"]]
        lines.append("\n---")

    report_path = output_dir / f"publish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def main():
    parser = argparse.ArgumentParser(description="内容分析 + 改写 + 生成图片")
    parser.add_argument("--input", required=True, help="douyin-scraper 输出的 Markdown 文件")
    parser.add_argument("--my-hospital", default="", help="你的医院/诊所名称")
    parser.add_argument("--auto", action="store_true", help="自动模式（无交互，有医院信息自动替换）")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"[错误] 文件不存在：{args.input}")
        sys.exit(1)

    print(f"[读取] {md_path.name}")
    notes = parse_notes_md(md_path)
    if not notes:
        print("[警告] 未解析到任何笔记（检查文件格式）")
        sys.exit(1)

    print(f"[发现] {len(notes)} 篇笔记，开始处理...\n")

    output_dir = Path(__file__).parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    results = []

    for i, note in enumerate(notes, 1):
        result = process_note(note, i, args.my_hospital, args.auto)
        results.append(result)

    report_path = generate_report(results, output_dir)

    print(f"\n{'='*60}")
    print(f"✓ 完成！")
    print(f"  处理笔记：{len(results)} 篇")
    print(f"  生成图片：{sum(1 for r in results if r['image_path'])} 张")
    print(f"  发布清单：{report_path}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
