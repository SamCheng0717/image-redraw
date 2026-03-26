---
name: image-redraw
description: 根据文字内容生成图片，使用阿里云百炼通义万象模型。支持直接输入文字、读取 Markdown 文件（兼容 douyin-scraper 输出）或自定义 prompt。当用户提到"图片生成"、"AI生图"、"重绘"、"文生图"、"内容配图"等场景时加载此技能。
---

# image-redraw

根据文字内容生成图片 —— 输入文字或 Markdown 文件，调用阿里云百炼通义万象模型，输出图片到 `output/`。

## ⚠️ 前置配置

### 1. 安装依赖

```bash
pip install dashscope python-dotenv
```

### 2. 配置 API Key

在技能目录创建 `.env`：

```
DASHSCOPE_API_KEY=你的阿里云百炼API Key
```

获取 API Key：[阿里云百炼控制台](https://bailian.console.aliyun.com)

---

## 使用

```bash
# 直接输入文字
python <skill_path>/scripts/redraw.py --text "韩国医美大实话，10条潜规则..."

# 读取 Markdown 文件（自动提取 OCR 内容）
python <skill_path>/scripts/redraw.py --file notes_韩国医美.md

# 自定义 prompt
python <skill_path>/scripts/redraw.py --prompt "简约风格信息图，白色背景..."

# 生成多张
python <skill_path>/scripts/redraw.py --text "内容" --n 4

# 指定尺寸
python <skill_path>/scripts/redraw.py --text "内容" --size 1280*720
```

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--text` | 直接输入文字内容 | - |
| `--file` | 读取文件路径（.md/.txt）| - |
| `--prompt` | 直接指定 prompt（跳过自动转换）| - |
| `--n` | 生成张数 | `1` |
| `--size` | 图片尺寸 | `1024*1024` |
| `--model` | 模型名称 | `wanx2.1-t2i-turbo` |

---

## 与 douyin-scraper 配合

```bash
# 先用 douyin-scraper 采集
python douyin-scraper/scripts/full_workflow.py --keyword "韩国医美" --count 5

# 再用 image-redraw 生成配图
python image-redraw/scripts/redraw.py --file douyin-scraper/output/notes_韩国医美_xxx.md
```

---

## 输出

图片保存至 `output/redraw_{timestamp}_{n}.png`
