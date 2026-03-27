---
name: image-redraw
description: 医美内容改写 + 小红书图片生成。接收 douyin-scraper 抓取的笔记，用 LLM 检测医院信息并改写文案（无医院 → 二创，有医院 → 用户指定替换 + 白皮书注入），然后调用 baoyu-xhs-images 生成精美图片。当用户提到"改写图文"、"重绘配图"、"图文二创"、"医院替换"、"小红书配图"等场景时加载此技能。
---

# image-redraw

将抖音图文笔记改写并生成小红书图片的两步流程。

## 前置依赖

```bash
pip install openai python-dotenv
```

`.env` 配置：

```
DASHSCOPE_API_KEY=你的阿里云百炼 API Key
```

## Step 1：在终端运行 workflow.py

```bash
python <skill_path>/scripts/workflow.py --input notes_韩国医美.md
```

处理完后输出每篇文案的 MD 文件路径和推荐预设。

## Step 2：调用 baoyu-xhs-images 技能生成图片

使用 `baoyu-xhs-images` 技能，传入改写后的 MD 文件和推荐预设：

```
# Claude Code 环境
/baoyu-xhs-images <output_file> --preset <preset>
```

推荐预设：

- `checklist` — 干货清单（notion 风格）
- `cute-share` — 种草分享（cute 风格）
- `warning` — 避坑指南（bold 风格）
- `knowledge-card` — 专业科普（notion 风格）
- `product-review` — 项目测评（fresh 风格）
- `tutorial` — 操作教程（chalkboard 风格）

## 白皮书（可选）

`config/whitepaper.md` 包含机构信息，有医院替换时自动注入（1-2 句）。

## 已知限制

- DashScope 不支持 `--ref` 参考图
- workflow.py 需在终端交互运行（有 input() 询问）
