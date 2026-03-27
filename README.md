# image-redraw

将抖音图文笔记（douyin-scraper 输出）改写成适合发布的文案，并通过 baoyu-xhs-images 生成精美小红书图片。

## 流程

```
douyin-scraper 输出.md
        ↓
python scripts/workflow.py      ← 检测医院信息、LLM 改写、保存文案
        ↓
output/note_XX.md（改写后文案）
        ↓
/baoyu-xhs-images output/note_XX.md --preset <预设>   ← 在 Claude Code 中运行
        ↓
xhs-images/{主题}/01-cover.png … 05-ending.png
```

## 安装依赖

```bash
pip install openai python-dotenv
```

## 配置

在技能目录创建 `.env`：

```
DASHSCOPE_API_KEY=你的阿里云百炼 API Key
```

获取 API Key：[阿里云百炼控制台](https://bailian.console.aliyun.com)

## Step 1：改写文案

```bash
# 基本用法（自动加载 config/whitepaper.md）
python scripts/workflow.py --input path/to/notes_韩国医美.md

# 指定白皮书
python scripts/workflow.py --input notes_韩国医美.md --whitepaper config/whitepaper.md
```

**两条路径：**
- **无医院信息** → LLM 二创改写，语气更适合小红书传播
- **有医院信息** → 告知用户 → 用户逐个指定替换 → LLM 结合白皮书改写

每篇处理完后，输出：
- `output/note_XX_HHMMSS.md` — 改写后文案
- 推荐的图片预设（如 `checklist`、`cute-share`、`warning`）

## Step 2：生成图片

在 **Claude Code** 中运行（不是终端）：

```
/baoyu-xhs-images output/note_01_143052.md --preset checklist
```

常用预设：

| 预设 | 风格 | 适合内容 |
|------|------|----------|
| `checklist` | notion + list | 干货清单、规则总结 |
| `cute-share` | cute + balanced | 种草分享、日常医美 |
| `warning` | bold + list | 避坑指南、注意事项 |
| `knowledge-card` | notion + dense | 专业科普、成分解析 |
| `product-review` | fresh + comparison | 项目对比、测评 |
| `tutorial` | chalkboard + flow | 步骤教程、操作流程 |

## 白皮书配置

`config/whitepaper.md` 是可选文件，包含你的机构信息（名称、优势、明星项目等）。有医院替换时，LLM 会自然引入白皮书内容（1-2 句，不过度推销）。

参考模板：`config/whitepaper.md.example`

## 注意事项

- DashScope（通义万象）不支持参考图（`--ref`），风格一致性靠 prompt 描述实现
- DashScope 并发限制较严，batch 生成建议不超过 2 并发
- `workflow.py` 有交互式输入（医院替换），必须在终端运行，不能在 Bash 工具中运行
- `xhs-images/` 和 `output/` 均为生成内容，已加入 `.gitignore`

## 项目结构

```
image-redraw/
├── scripts/
│   └── workflow.py         # 主流程：检测医院 → 改写 → 保存文案
├── config/
│   ├── whitepaper.md       # 你的机构白皮书（可选）
│   └── whitepaper.md.example
├── output/                 # 改写后文案 MD + 发布清单
└── xhs-images/             # baoyu-xhs-images 生成的图片
```
