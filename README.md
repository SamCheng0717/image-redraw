# image-redraw

根据文字内容生成图片，使用阿里云百炼通义万象模型。

## 安装

```bash
npx clawhub@latest install image-redraw
# 或
npx skills@latest add SamCheng0717/image-redraw
```

## 配置

在项目根目录创建 `.env`：

```
DASHSCOPE_API_KEY=你的阿里云百炼API Key
```

获取 API Key：[阿里云百炼控制台](https://bailian.console.aliyun.com)

```bash
pip install dashscope python-dotenv
```

## 使用

```bash
# 输入文字
python scripts/redraw.py --text "韩国医美大实话，10条潜规则..."

# 读取 Markdown 文件
python scripts/redraw.py --file notes_韩国医美.md

# 自定义 prompt
python scripts/redraw.py --prompt "简约风格信息图，白色背景，排版精美"

# 生成多张 / 指定尺寸
python scripts/redraw.py --text "内容" --n 4 --size 1280*720
```

## 项目结构

```
image-redraw/
├── scripts/
│   └── redraw.py   # 主脚本
├── output/         # 生成图片保存目录
└── .env            # API Key 配置
```
