# Jira 测试用例提取工具使用指南

本文档介绍如何使用 `jira-test-extractor` skill 从 Jira ticket 提取信息并生成测试用例文档。

## 目录结构

```
jira-test-extractor/
├── src/                          # Python 源码
│   ├── extractor.py              # Jira 信息提取模块
│   ├── generator.py              # 文档生成模块
│   └── template_parser.py         # 模板解析模块
├── templates/                     # 模板目录
│   └── default_template.xlsx      # 默认测试用例模板
├── extract_test_cases.py          # 阶段1：提取 Jira 信息
├── generate_docs.py               # 阶段2：生成测试用例文档
└── create_template.py             # 创建默认模板工具
```

## 环境准备

### 1. 安装依赖

```bash
cd .trae/skills/jira-test-extractor

# 创建虚拟环境（如果还没有）
python -m venv .venv

# 激活虚拟环境
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

# 安装依赖
pip install playwright pyyaml python-docx openpyxl lxml

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 配置 Jira

复制 `config.json.example` 为 `config.json`，填入你的 Jira 信息：

```json
{
  "jira": {
    "url": "https://your-jira-domain.com",
    "username": "你的用户名",
    "password": "你的密码"
  },
  "output_dir": "./test_cases"
}
```

## 使用流程

### 流程图

```
┌─────────────────────────────────────────────────────────────────┐
│                    Jira 测试用例提取流程                          │
└─────────────────────────────────────────────────────────────────┘

  ┌──────────┐      ┌─────────────────┐      ┌──────────────────┐
  │          │      │                 │      │                  │
  │   Jira   │ ──▶ │ extract_test_   │ ──▶ │   info.json      │
  │  Ticket  │      │ cases.py        │      │   + 附件         │
  │   URL    │      │                 │      │                  │
  │          │      └─────────────────┘      └──────────────────┘
  └──────────┘                                       │
                                                      ▼
  ┌──────────┐      ┌─────────────────┐      ┌──────────────────┐
  │          │      │                 │      │                  │
  │  AI 生成 │ ◀─── │ 分析描述和附件   │ ◀─── │ 读取 info.json   │
  │  测试用例 │      │ 识别测试点       │      │  和附件          │
  │          │      │                 │      │                  │
  └──────────┘      └─────────────────┘      └──────────────────┘
                              │
                              ▼
  ┌──────────┐      ┌─────────────────┐      ┌──────────────────┐
  │          │      │                 │      │                  │
  │  测试用例 │ ──▶ │ generate_docs.py │ ──▶ │  Excel (模板格式) │
  │ JSON 文件 │      │   + 模板文件     │      │   或              │
  │          │      │                 │      │  MD/DOCX/XLSX    │
  └──────────┘      └─────────────────┘      └──────────────────┘
                           │                              │
                           │   -t 模板.xlsx ──▶ 只生成 Excel
                           │   无模板 ─────────▶ 生成MD/DOCX/XLSX
```

## 详细步骤

### 步骤 1：提取 Jira Ticket 信息

```bash
cd .trae/skills/jira-test-extractor
python extract_test_cases.py <jira-ticket-url>
```

**示例：**
```bash
python extract_test_cases.py https://your-jira-domain.com/browse/PROJECT-123
```

**参数说明：**
- `ticket_url`：Jira ticket 的完整 URL（必填）
- `--config`：配置文件路径（可选，默认使用 config.json）
- `--output`：输出目录（可选，默认 `./test_cases`）
- `--no-download`：不下载附件（可选）

**输出：**
```
正在连接 Jira...
正在提取 Ticket 信息：https://your-jira-domain.com/browse/PROJECT-123
已提取：[PROJECT-123] 示例功能
状态：In Progress
优先级：High
描述长度：500 字符
评论数量：3
附件数量：2

正在下载附件...
  下载成功: mockup.png
  下载成功: api_spec.pdf

提取完成!数据保存在: ./test_cases/PROJECT-123
```

**生成的文件：**
```
test_cases/PROJECT-123/
├── info.json           # Jira ticket 详细信息
└── attachments/       # 下载的附件
    ├── mockup.png
    └── api_spec.pdf
```

### 步骤 2：AI 生成测试用例

读取 `test_cases/<ticket_id>/info.json` 和附件内容，让 AI 生成测试用例 JSON。

**提示词模板：**

```
请基于以下 Jira Ticket 信息生成测试用例：

1. 读取 ./test_cases/<ticket_id>/info.json 获取 Ticket 详情
2. 如有附件，读取 attachments/ 文件夹中的截图或文档
3. 分析问题描述和评论，识别测试点
4. 【重要】严格按照以下模板格式生成测试用例：

【模板字段】（请严格按此格式生成）
- 用例编号：格式 TC-XXX（如 TC-001）
- 操作：描述测试的操作步骤
- 前提条件：测试前需要满足的条件
- 输入：测试输入数据
- 预期结果：预期的测试结果
- 测试结果：（留空，由测试人员填写）

5. 将结果保存到 ./test_cases/<ticket_id>/test_cases.json
```

### 步骤 3：生成测试用例文档

```bash
cd .trae/skills/jira-test-extractor

# 使用模板生成（只生成 Excel，按模板格式）
python generate_docs.py <test_cases.json> -t <template.xlsx>

# 不使用模板生成（生成 MD、DOCX、XLSX 默认格式）
python generate_docs.py <test_cases.json>
```

**示例（使用模板）：**
```bash
python generate_docs.py ./test_cases/PROJECT-123/test_cases.json -t ./templates/default_template.xlsx
```

**示例（不使用模板）：**
```bash
python generate_docs.py ./test_cases/PROJECT-123/test_cases.json
```

**参数说明：**
- `input_file`：JSON 测试用例文件路径（必填）
- `-t, --template`：Excel 模板文件路径（可选）
  - 提供模板：只生成 Excel 格式（按模板列结构）
  - 不提供模板：生成 MD、DOCX、XLSX 三种默认格式

**生成的文件：**

使用模板时：
```
test_cases/PROJECT-123/
└── 测试用例.xlsx    # 按模板格式生成
```

不使用模板时：
```
test_cases/PROJECT-123/
├── 测试用例.md       # Markdown 格式
├── 测试用例.docx     # Word 格式
└── 测试用例.xlsx     # Excel 默认格式
```