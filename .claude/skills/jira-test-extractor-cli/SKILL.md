---
name: "jira-test-extractor-cli"
description: "结合 jira-workflow CLI 从 Jira ticket 提取信息生成测试用例。当用户提供 Jira 单号或 URL 时调用此 skill。"
---

# Jira Test Extractor CLI

结合 jira-workflow CLI 使用，一键从 Jira ticket 提取信息并生成测试用例文档。

## 目录结构

```
.claude/skills/jira-test-extractor-cli/
├── jira-workflow.exe    # PyInstaller 打包的 CLI 可执行文件
├── SKILL.md             # 本文档
└── src/                 # 源码目录（预留）
```

## 工作流程

```
Jira Ticket URL → jira-workflow quick → test_cases.json → AI 生成文档
```

## 前置条件

### 配置文件

确保存在 `config.json` 配置文件，包含 Jira 连接信息：

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

配置文件搜索顺序：
1. `./config.json.local`
2. `./.claude/config.json.local`
3. `./config.json`
4. `./.claude/config.json`

## 命令用法

### 完整工作流（分步执行）

```bash
# 步骤 1: 提取 Ticket 信息到 info.json
.claude/skills/jira-test-extractor-cli/jira-workflow.exe extract <ticket>

# 步骤 2: 下载并读取所有附件
.claude/skills/jira-test-extractor-cli/jira-workflow.exe read-attachments <ticket>

# 步骤 3: 生成测试用例文档（需要 AI 生成 test_cases.json）
.claude/skills/jira-test-extractor-cli/jira-workflow.exe generate <json_file>
```

### 示例

```bash
# 提取单个 Ticket
.claude/skills/jira-test-extractor-cli/jira-workflow.exe extract PROJECT-123
.claude/skills/jira-test-extractor-cli/jira-workflow.exe extract https://jira.example.com/browse/PROJECT-123

# 读取附件内容
.claude/skills/jira-test-extractor-cli/jira-workflow.exe read-attachments PROJECT-123

# 生成文档（需先有 test_cases.json）
.claude/skills/jira-test-extractor-cli/jira-workflow.exe generate ./test_cases/PROJECT-123/test_cases.json
```

### 初始化配置

```bash
.claude/skills/jira-test-extractor-cli/jira-workflow.exe init
```

### 创建模板

```bash
.claude/skills/jira-test-extractor-cli/jira-workflow.exe template
```

### 显示帮助

```bash
.claude/skills/jira-test-extractor-cli/jira-workflow.exe help
```

## 输出结构

```
./test_cases/
└── PROJECT-123/
    ├── info.json              # Jira ticket 信息
    ├── combined_content.json  # 附件内容整合
    ├── test_cases.md          # Markdown 格式
    ├── test_cases.docx        # Word 格式
    └── test_cases.xlsx        # Excel 格式
```

## 使用场景

### 场景 1：用户提供 Jira 单号

```
用户: "帮我处理 PROJ-123 这个 ticket"
AI: 使用 jira-test-extractor-cli skill，运行 quick 命令提取并生成测试用例
```

### 场景 2：用户提供 Jira URL

```
用户: "这是 ticket 链接 https://jira.example.com/browse/PROJ-123"
AI: 使用 jira-test-extractor-cli skill，从 URL 提取单号，运行 quick 命令
```

### 场景 3：需要自定义模板

```
AI: 使用 generate 命令配合 -t 参数指定模板文件
.claude/skills/jira-test-extractor-cli/jira-workflow.exe generate test_cases.json -t template.xlsx
```

## CLI 子命令

| 命令 | 说明 |
|------|------|
| `extract <ticket>` | 从 Jira Ticket 提取信息到 info.json |
| `read-attachments <ticket>` | 下载并读取 Ticket 的所有附件内容 |
| `generate <file>` | 将 JSON 测试用例转换为文档格式 |
| `init` | 交互式创建 config.json |
| `template` | 创建默认 Excel 模板 |
| `help` | 显示帮助信息 |

## AI 调用指导

当用户提供 Jira 单号或 URL 时：

1. 提取 ticket ID（从 URL 或直接使用单号）
2. 调用 `jira-workflow.exe extract <ticket-id>` 提取信息
3. 调用 `jira-workflow.exe read-attachments <ticket-id>` 下载并读取附件
4. 读取生成的 `test_cases/` 目录下的文件
5. 根据需要让 AI 生成更详细的测试用例 JSON
6. 使用 `generate` 命令转换为最终文档格式

## 注意事项

- 确保 `jira-workflow.exe` 有执行权限
- 配置文件需包含有效的 Jira 账号密码
- 附件下载需要 Jira 对应文件的访问权限
- 输出目录默认 `test_cases/`，可使用 `-o` 参数指定
