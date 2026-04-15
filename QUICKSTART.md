# Claude Code + Jira Workflow 快速开始

## ✅ 安装验证

```bash
# 确认 Claude Code 已安装
claude --version
# 输出: 2.1.109 (Claude Code)

# 查看帮助
claude --help
```

## 🚀 三种使用方式

### 方式 1: 交互式会话（推荐新手）

```bash
# 启动 Claude Code（自动加载 MCP 服务器）
claude

# 在 Claude Code 中输入：
用户: 请提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息
用户: 读取 info.json 并生成测试用例
用户: 使用模板生成测试文档
```

### 方式 2: 单次命令（推荐脚本）

```bash
# 直接执行单个命令
claude --print "提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息"

# 使用模板生成文档
claude --print "使用模板 ./templates/default_template.xlsx 生成测试文档，输入文件是 ./test_cases/PROJECT-123/test_cases.json"
```

### 方式 3: Agent 模式（推荐批量）

```bash
# 使用预配置的 Agent
claude --agents "$(cat agents.json)" --agent jira-processor "处理 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123"

# 批量处理多个 Tickets
claude --agents "$(cat agents.json)" --agent jira-batch-processor "批量处理以下 Tickets: PROJECT-123, PROJECT-456, PROJECT-789"
```

## 📋 完整工作流程示例

### 场景 1: 单个 Ticket 处理

```bash
# 步骤 1: 提取信息
claude --print "请使用 extract_jira_ticket 工具提取 Ticket: https://your-jira-instance.com/browse/PROJECT-123"

# 步骤 2: 生成测试用例 JSON（Claude Code 会自动读取 info.json 并生成）
claude --print "请读取 ./test_cases/PROJECT-123/info.json 并生成测试用例 JSON，保存到 ./test_cases/PROJECT-123/test_cases.json"

# 步骤 3: 生成文档
# 有模板
claude --print "请使用 generate_test_documents 工具，输入文件: ./test_cases/PROJECT-123/test_cases.json，模板: ./templates/default_template.xlsx"

# 无模板（生成默认格式）
claude --print "请使用 generate_test_documents 工具，输入文件: ./test_cases/PROJECT-123/test_cases.json"
```

### 场景 2: 批量处理

```bash
# 创建批量处理脚本 batch_process.txt
cat > batch_process.txt <<EOF
请处理以下 Jira Tickets：

1. https://your-jira-instance.com/browse/PROJECT-123
2. https://your-jira-instance.com/browse/PROJECT-456
3. https://your-jira-instance.com/browse/PROJECT-789

对每个 Ticket 执行：
- 提取信息
- 生成测试用例 JSON
- 使用模板 ./templates/default_template.xlsx 生成文档
EOF

# 执行批量处理
claude --print "$(cat batch_process.txt)"
```

### 场景 3: 使用 Shell 脚本自动化

```bash
# 运行自动处理脚本（已在项目中提供）
bash process_jira_ticket.sh https://your-jira-instance.com/browse/PROJECT-123 ./templates/default_template.xlsx

# 或在 Windows 上使用 PowerShell
python jira_mcp_server.py &
claude --print "提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息"
```

## 🛠️ 可用工具

### 1. extract_jira_ticket

**用途**: 从 Jira Ticket URL 提取信息并保存

**参数**:
- `ticket_url` (必填): Jira Ticket 的完整 URL
- `output_dir` (可选): 输出目录路径

**示例**:
```bash
claude --print "请使用 extract_jira_ticket 工具，ticket_url: https://your-jira-instance.com/browse/PROJECT-123"
```

**输出**:
```json
{
  "success": true,
  "ticket_id": "PROJECT-123",
  "summary": "示例功能开发",
  "path": "./test_cases/PROJECT-123"
}
```

### 2. generate_test_documents

**用途**: 从 JSON 或 Markdown 测试用例生成文档

**参数**:
- `input_file` (必填): JSON 或 MD 测试用例文件路径
- `template_path` (可选): 模板文件路径（支持 .xlsx、.docx、.md）
- `output_dir` (可选): 输出目录

**示例**:
```bash
# 有模板
claude --print "请使用 generate_test_documents 工具，input_file: ./test_cases/PROJECT-123/test_cases.json，template_path: ./templates/default_template.xlsx"

# 无模板（生成默认格式）
claude --print "请使用 generate_test_documents 工具，input_file: ./test_cases/PROJECT-123/test_cases.json"
```

**输出**:
```json
{
  "success": true,
  "files": ["./test_cases/PROJECT-123/测试用例.xlsx"],
  "count": 1
}
```

### 3. get_ticket_info

**用途**: 获取已保存的 Jira Ticket 信息

**参数**:
- `ticket_id` (必填): Ticket ID

**示例**:
```bash
claude --print "请使用 get_ticket_info 工具，ticket_id: PROJECT-123"
```

## 🔧 高级用法

### 自定义 Agent

```bash
# 使用自定义 Agent 配置
claude --agents '{"my-agent": {"description": "我的自定义 Agent", "prompt": "你是一个...", "tools": ["Bash"]}}' --agent my-agent "我的任务"
```

### 调试模式

```bash
# 启用调试模式
claude --debug

# 将日志输出到文件
claude --debug-file claude_debug.log
```

### 配置权限模式

```bash
# 自动接受所有编辑（危险，仅用于可信环境）
claude --permission-mode auto

# 计划模式（适合复杂任务）
claude --permission-mode plan
```

## 📁 项目结构

```
jira_workflow/
├── jira_mcp_server.py          # MCP 服务器（自动加载）
├── .mcp.json                   # MCP 配置
├── agents.json                 # Agent 配置
├── process_jira_ticket.sh      # 批量处理脚本
├── Claude_Code_Integration_Guide.md  # 完整集成文档
└── .trae/
    └── skills/jira-test-extractor/
        ├── extract_test_cases.py    # 阶段1：提取 Jira 信息
        ├── generate_docs.py         # 阶段2：生成测试文档
        ├── src/
        │   ├── extractor.py         # Jira 提取器
        │   ├── generator.py         # 文档生成器
        │   └── template_parser.py   # 模板解析器
        ├── config.json              # Jira 配置
        └── test_cases/              # 输出目录
            └── <ticket_id>/
                ├── info.json
                ├── test_cases.json
                └── 测试用例.xlsx
```

## ❓ 常见问题

### Q: Claude Code 找不到工具怎么办？

**A**: 确认 `.mcp.json` 在项目根目录，并重新启动 Claude Code。

### Q: 如何在 VSCode 中使用？

**A**: 
1. 安装 Claude Code VSCode 扩展
2. 打开命令面板 (Ctrl+Shift+P)
3. 输入 `Claude: Start Session`
4. Claude Code 会自动检测 MCP 服务器

### Q: 如何查看 MCP 服务器日志？

**A**: 
```bash
# 手动启动 MCP 服务器查看日志
python jira_mcp_server.py

# 在另一个终端启动 Claude Code
claude
```

### Q: 批量处理失败如何调试？

**A**: 使用调试模式重新运行：
```bash
claude --debug --print "批量处理 Tickets..."
```

## 📚 更多资源

- **完整集成文档**: `Claude_Code_Integration_Guide.md`
- **Jira Skill 文档**: `.trae/skills/jira-test-extractor/SKILL.md`
- **项目说明**: `.trae/README.md`
- **Claude Code 官方文档**: `claude --help` 或访问官网

## 🎯 下一步

1. ✅ 验证安装：`claude --version`
2. 🚀 尝试提取一个 Ticket：`claude --print "提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123"`
3. 📖 阅读完整文档：`Claude_Code_Integration_Guide.md`
4. 🤖 配置自定义 Agent：修改 `agents.json`
