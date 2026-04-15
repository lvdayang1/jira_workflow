---
name: "jira-test-extractor"
description: "从 Jira ticket 提取信息生成测试用例。当用户提供 Jira URL 或需要从 Jira ticket 提取测试用例时调用此 skill。"
---

# Jira Test Case Extractor

从 Jira ticket 提取信息并生成测试用例文档的 skill。

## 目录结构

```
.trae/skills/jira-test-extractor/
├── src/                           # Python 源代码
│   ├── __init__.py
│   ├── extractor.py               # Jira 信息提取
│   ├── generator.py               # 文档生成
│   └── template_parser.py         # 模板解析
├── templates/                      # 模板目录
│   └── default_template.xlsx      # 默认模板
├── .venv/                         # Python 虚拟环境
├── config.json                    # Jira 配置文件
├── config.json.example            # 配置模板
├── requirements.txt               # 依赖列表
├── extract_test_cases.py          # 阶段1入口：提取 Jira 信息
├── generate_docs.py               # 阶段2入口：生成测试用例文档
└── create_template.py             # 创建默认模板
```

## 工作流程

```
Jira Ticket URL → extract_test_cases.py → info.json → AI 生成 test_cases.json → generate_docs.py → MD/DOCX/XLSX
```

### 步骤 1：提取 Jira 信息

```bash
cd .trae/skills/jira-test-extractor
python extract_test_cases.py <jira-ticket-url>
```

脚本会：
1. 使用配置文件中的凭据连接 Jira
2. 提取 ticket 的描述、评论、附件信息
3. 将信息保存到 `./test_cases/<ticket_id>/info.json`

### 步骤 2：AI 生成测试用例 JSON

AI 读取 `info.json`，根据 Jira Ticket 内容生成 `test_cases.json`。

### 步骤 3：生成测试用例文档

```bash
cd .trae/skills/jira-test-extractor

# 无模板：生成 MD、DOCX、XLSX 默认格式
python generate_docs.py ./test_cases/<ticket_id>/test_cases.json

# 有模板：根据模板格式生成对应文档
python generate_docs.py ./test_cases/<ticket_id>/test_cases.json -t template.xlsx
python generate_docs.py ./test_cases/<ticket_id>/test_cases.json -t template.docx
python generate_docs.py ./test_cases/<ticket_id>/test_cases.json -t template.md
```

## 核心逻辑：模板判定

| 场景 | 命令 | 生成文件 |
|------|------|---------|
| 无模板 | `python generate_docs.py test_cases.json` | MD + DOCX + XLSX（三种默认格式） |
| .xlsx 模板 | `python generate_docs.py test_cases.json -t template.xlsx` | XLSX（按模板格式） |
| .docx 模板 | `python generate_docs.py test_cases.json -t template.docx` | DOCX（按模板格式） |
| .md 模板 | `python generate_docs.py test_cases.json -t template.md` | MD（按模板格式） |

### 自定义模板字段

模板中的列名将自动映射到测试用例 JSON 字段：

| 模板字段 | JSON Key | 说明 |
|---------|----------|------|
| 用例编号 | id | 格式：TC-XXX |
| 用例标题 | name | 测试目的描述 |
| 测试模块 | module | 如"用户管理-登录" |
| 测试类型 | type | 功能测试/接口测试/性能测试 |
| 优先级 | priority | 高/中/低 |
| 前置条件 | precondition | 测试前准备 |
| 测试步骤 | steps | 数组，每步一行 |
| 预期结果 | expected_results | 数组，每条一行 |
| 测试数据 | test_data | JSON 对象 |
| 备注 | remarks | 补充说明 |

## 文件夹结构

```
./test_cases/
└── PROJECT-123/
    ├── info.json             # Jira ticket 信息
    ├── test_cases.json       # AI 生成的 JSON 格式测试用例
    ├── test_cases.md         # Markdown 格式测试用例
    ├── test_cases.docx       # Word 格式测试用例
    ├── test_cases.xlsx       # Excel 格式测试用例
    └── attachments/          # 下载的附件
        └── ...
```

## info.json 结构

```json
{
  "id": "PROJECT-123",
  "url": "https://your-jira-domain.com/browse/PROJECT-123",
  "summary": "示例功能开发",
  "status": "Resolved",
  "priority": "一般",
  "assignee": "开发人员",
  "reporter": "测试人员",
  "description": "这是一个示例功能...",
  "comments": [
    {
      "author": "评论者",
      "time": "2026-04-09",
      "body": "这是一个示例评论..."
    }
  ],
  "attachments": []
}
```

## test_cases.json 结构

```json
{
  "id": "PROJECT-123",
  "summary": "示例功能开发",
  "priority": "一般",
  "status": "Submitted",
  "reporter": "测试人员",
  "assignee": "开发人员",
  "test_cases": [
    {
      "id": "TC-001",
      "name": "测试示例功能",
      "module": "示例模块",
      "type": "功能测试",
      "priority": "高",
      "precondition": "1. 用户已登录系统\\n2. 进入功能页面",
      "steps": ["1. 进入功能页面", "2. 执行操作"],
      "expected_results": ["1. 操作成功", "2. 显示成功提示"],
      "test_data": {"key": "value"},
      "remarks": ""
    }
  ]
}
```

## 依赖说明

| 依赖包 | 用途 |
|--------|------|
| requests | HTTP 请求，用于 Jira API |
| openpyxl | Excel 文件读写，解析模板和生成文档 |
| python-docx | Word 文档生成 |
| lxml | XML/HTML 解析 |

## 首次使用安装依赖

```bash
cd .trae/skills/jira-test-extractor
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac
pip install requests openpyxl python-docx lxml
```

## AI 生成测试用例的提示词

读取 `info.json` 后，AI 根据 Ticket 信息生成测试用例。

### 确认模板

**如果用户提供了用例模板 Excel 文件**：
1. 让用户提供模板文件路径
2. 使用 `src/template_parser.py` 的 `TemplateParser` 读取模板 Excel 文件，提取表头作为字段映射
3. 在提示词中明确说明"请严格按照以下模板格式生成测试用例"

**如果用户没有提供模板**：
使用默认字段格式生成。

### 输出格式要求

- test_cases.json 必须与模板字段完全对应
- steps 和 expected_results 使用数组格式
- test_data 使用 JSON 格式对象

## 配置文件

### config.json

```json
{
  "jira": {
    "url": "https://your-jira-domain.com",
    "username": "your_username",
    "password": "your_password"
  },
  "output_dir": "./test_cases"
}
```
