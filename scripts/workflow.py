#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
image-redraw workflow

两条路：
  无医院信息 → LLM 二创 → 生成精美图片
  有医院信息 → 告知用户 → 用户指定替换 → LLM + 白皮书改写 → 生成精美图片

用法：
    python scripts/workflow.py --input notes_韩国医美.md
    python scripts/workflow.py --input notes_韩国医美.md --whitepaper config/whitepaper.md
"""
import argparse
import json
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

SCRIPT_DIR = Path(__file__).parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
OUTPUT_DIR = SCRIPT_DIR.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


# ─────────────────── LLM 调用 ────────────────────

def call_llm(messages: list, temperature: float = 0.4) -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("  [错误] 未配置 DASHSCOPE_API_KEY")
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )
        resp = client.chat.completions.create(
            model="qwen-plus",
            messages=messages,
            temperature=temperature,
        )
        content = resp.choices[0].message.content.strip()
        # 去掉 LLM 常见废话前缀
        for prefix in ["当然可以！", "当然！", "好的！", "好的，", "以下是", "如下："]:
            if content.startswith(prefix):
                # 找到第一个实质内容行
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if line.strip() and not any(line.startswith(p) for p in
                       ["当然", "好的", "以下是", "如下", "---", "这是"]):
                        content = "\n".join(lines[i:]).strip()
                        break
                break
        return content
    except Exception as e:
        print(f"  [LLM错误] {e}")
        return ""


# ─────────────────── 医院提取 ────────────────────

def extract_hospitals(text: str) -> list:
    """用 LLM 从文本中提取医院/诊所/医美机构名称"""
    result = call_llm([
        {"role": "system", "content": (
            "你是信息提取助手。从用户提供的文本中，提取所有医院、诊所、皮肤科、"
            "医美机构的名称（包括中文名、英文简称、缩写）。"
            "以 JSON 数组格式返回，例如：[\"pfk\", \"江南bb\", \"弗洛雷斯\"]。"
            "如果没有任何医疗机构名称，返回空数组：[]"
        )},
        {"role": "user", "content": text}
    ], temperature=0.1)

    # 解析 JSON
    try:
        match = re.search(r'\[.*?\]', result, re.DOTALL)
        if match:
            hospitals = json.loads(match.group())
            return [h.strip() for h in hospitals if h.strip()]
    except Exception:
        pass
    return []


# ─────────────────── 二创（无医院）────────────────────

def rewrite_creative(text: str) -> str:
    """无医院信息时，二创改写，使内容更适合社交媒体传播"""
    return call_llm([
        {"role": "system", "content": (
            "你是一位擅长医美内容创作的小红书博主。"
            "将用户提供的内容进行二次创作：保留核心干货，"
            "语气更亲切活泼，加入适当的表情符号，"
            "优化段落排版，使其更适合在小红书/微信等平台传播。"
            "保持原有信息的准确性，不要添加不实内容。"
        )},
        {"role": "user", "content": f"请对以下内容进行二创：\n\n{text}"}
    ])


# ─────────────────── 改写（有医院）────────────────────

def rewrite_with_replacement(text: str, replacements: dict, whitepaper: str) -> str:
    """有医院信息时，按替换表改写，并注入白皮书知识"""
    replacement_desc = "、".join([f"「{k}」→「{v}」" for k, v in replacements.items()])

    if whitepaper:
        system_prompt = (
            "你是一位医美内容编辑。根据以下替换规则改写文案，"
            "将竞品机构名称替换为指定机构，并结合机构白皮书，"
            "在适当位置自然地融入替换后机构的相关优势或特色介绍（1-2句即可，不要过度推销）。"
            "保持原文整体结构和风格。\n\n"
            f"【机构白皮书】\n{whitepaper}"
        )
        user_content = f"替换规则：{replacement_desc}\n\n原文：\n{text}"
    else:
        system_prompt = (
            "你是一位医美内容编辑。根据替换规则改写文案，"
            "将竞品机构名称替换为指定机构名称，"
            "使替换后的文案读起来自然流畅，保持原文结构和风格。"
        )
        user_content = f"替换规则：{replacement_desc}\n\n原文：\n{text}"

    return call_llm([
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content}
    ])


# ─────────────────── 解析 Markdown ────────────────────

def parse_notes_md(md_path: Path) -> list:
    text = md_path.read_text(encoding="utf-8")
    notes = []
    blocks = re.split(r'\n(?=## 笔记 \d+)', text)
    for block in blocks:
        if not block.strip().startswith("## 笔记"):
            continue
        note = {}
        m = re.search(r'## 笔记 \d+ — (.+)', block)
        note["title"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*🔗 链接\*\*：(https?://\S+)', block)
        note["url"] = m.group(1).strip() if m else ""
        m = re.search(r'### 🔍 OCR 识别内容\n+([\s\S]+?)(?=\n###|\n---|\Z)', block)
        note["ocr"] = m.group(1).strip() if m else ""
        if note["ocr"]:
            notes.append(note)
    return notes


# ─────────────────── 处理单篇笔记 ────────────────────

def _recommend_preset(text: str) -> str:
    """根据文案内容推荐 baoyu-xhs-images 预设"""
    t = text.lower()
    # 避坑/警示类
    if any(w in t for w in ["避坑", "千万别", "注意", "警惕", "骗局", "黑幕", "后悔", "翻车"]):
        return "warning"
    # 干货/清单/排行
    if any(w in t for w in ["推荐", "必备", "清单", "排行", "top", "最佳", "攻略", "秘籍"]):
        return "checklist"
    # 对比/测评
    if any(w in t for w in ["对比", "vs", "测评", "区别", "哪个好", "优缺点"]):
        return "product-review"
    # 教程/步骤
    if any(w in t for w in ["步骤", "教程", "怎么做", "方法", "流程", "操作"]):
        return "tutorial"
    # 干货知识
    if any(w in t for w in ["原理", "成分", "科普", "为什么", "知识", "了解"]):
        return "knowledge-card"
    # 种草/分享（默认医美内容）
    return "cute-share"


def process_note(note: dict, idx: int, whitepaper: str) -> dict:
    title = note["title"][:50]
    ocr = note["ocr"]

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
        "action": "direct",
    }

    # ── Step 1: 提取医院信息 ──
    print("  [分析] 正在检测医院/机构信息...")
    hospitals = extract_hospitals(ocr)

    if not hospitals:
        # ── 无医院 → 二创 ──
        print("  ✅ 未检测到医院信息")
        print("  ✍️  正在二创改写...")
        rewritten = rewrite_creative(ocr)
        if rewritten:
            result["final_text"] = rewritten
            result["action"] = "二创"
            print("  改写预览：")
            for line in rewritten.split("\n")[:6]:
                if line.strip():
                    print(f"    {line}")
            print()
        else:
            print("  [警告] 二创失败，使用原文")

    else:
        # ── 有医院 → 用户指定替换 ──
        print(f"  ⚠️  检测到医院/机构：{', '.join(f'「{h}」' for h in hospitals)}")
        print()
        print("  原文预览：")
        for line in ocr.split("\n")[:6]:
            if line.strip():
                print(f"    {line}")
        print()

        # 逐个询问替换
        replacements = {}
        print("  请为每个机构指定替换名称（直接回车跳过不替换）：")
        for h in hospitals:
            target = input(f"    「{h}」 → ").strip()
            if target:
                replacements[h] = target

        if not replacements:
            print("  ➡️  未指定替换，进行二创改写...")
            rewritten = rewrite_creative(ocr)
            result["final_text"] = rewritten or ocr
            result["action"] = "二创（无替换）"
        else:
            print()
            if whitepaper:
                print("  📄 使用白皮书生成机构介绍...")
            else:
                print("  ✍️  正在改写（无白皮书）...")
            rewritten = rewrite_with_replacement(ocr, replacements, whitepaper)
            if rewritten:
                result["final_text"] = rewritten
                result["action"] = "替换改写"
                print("  改写预览：")
                for line in rewritten.split("\n")[:8]:
                    if line.strip():
                        print(f"    {line}")
                print()
            else:
                print("  [警告] 改写失败，使用原文")

    # ── Step 2: 保存内容文件（供 baoyu-xhs-images 生成图片）──
    content_file = OUTPUT_DIR / f"note_{idx:02d}_{datetime.now().strftime('%H%M%S')}.md"
    content_file.write_text(
        f"# {title}\n\n{result['final_text']}",
        encoding="utf-8"
    )
    result["content_file"] = content_file

    # 推荐预设
    preset = _recommend_preset(result["final_text"])
    result["preset"] = preset
    print(f"  📄 内容已保存：{content_file.name}")
    print(f"  💡 推荐图片预设：{preset}")

    return result


# ─────────────────── 发布清单 ────────────────────

def generate_report(results: list) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# 发布清单", "",
        f"生成时间：{ts}", "",
        f"共 {len(results)} 篇 | "
        f"二创：{sum(1 for r in results if '二创' in r['action'])} | "
        f"替换改写：{sum(1 for r in results if r['action']=='替换改写')}",
        "", "---",
    ]
    for r in results:
        lines += [
            f"\n## {r['idx']}. {r['title']}",
            f"**操作**：{r['action']}",
            f"**链接**：{r['url']}",
        ]
        if r.get("content_file"):
            lines.append(f"**内容文件**：`{r['content_file']}`")
        if r.get("preset"):
            lines.append(f"**图片预设**：`{r['preset']}`")
            lines.append(f"**生成命令**：`/baoyu-xhs-images {r['content_file']} --preset {r['preset']}`")
        lines += ["", "**改写后文案**：", "", r["final_text"], "\n---"]

    path = OUTPUT_DIR / f"publish_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


# ─────────────────── 入口 ────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="douyin-scraper 输出的 Markdown 文件")
    parser.add_argument("--whitepaper", default="", help="白皮书 Markdown 文件路径（可选）")
    args = parser.parse_args()

    md_path = Path(args.input)
    if not md_path.exists():
        print(f"[错误] 文件不存在：{args.input}")
        sys.exit(1)

    # 加载白皮书
    whitepaper = ""
    wp_path = Path(args.whitepaper) if args.whitepaper else CONFIG_DIR / "whitepaper.md"
    if wp_path.exists():
        whitepaper = wp_path.read_text(encoding="utf-8")
        print(f"[白皮书] 已加载：{wp_path.name}")
    else:
        print("[白皮书] 未配置，将在替换时不添加机构介绍")

    print(f"[读取] {md_path.name}")
    notes = parse_notes_md(md_path)
    if not notes:
        print("[错误] 未解析到笔记")
        sys.exit(1)

    print(f"[发现] {len(notes)} 篇笔记\n")

    results = []
    for i, note in enumerate(notes, 1):
        result = process_note(note, i, whitepaper)
        results.append(result)

    report = generate_report(results)
    print(f"\n{'='*60}")
    print(f"✓ 完成！共 {len(results)} 篇")
    print(f"发布清单：{report}")
    print()
    print("📸 生成图片（在 Claude Code 中运行）：")
    for r in results:
        if r.get("content_file") and r.get("preset"):
            print(f"  /baoyu-xhs-images {r['content_file']} --preset {r['preset']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
