# Claude Code 与 Jira Workflow 集成指南

本文档介绍如何将 Claude Code 与 Jira workflow 项目集成，实现智能化的测试用例生成和管理。

## 目录

1. [环境准备](#环境准备)
2. [MCP 集成方式](#mcp-集成方式)
3. [CLI 集成方式](#cli-集成方式)
4. [实际工作流程示例](#实际工作流程示例)
5. [常见问题](#常见问题)

---

## 环境准备

### 1. 确认 Claude Code 安装

```bash
# 检查版本
claude --version

# 查看帮助
claude --help
```

### 2. 确认 Python 环境

```bash
cd .claude/skills/jira-test-extractor

# 激活虚拟环境
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 验证依赖
pip list | grep -E "requests|openpyxl|python-docx"
```

### 3. Jira 配置确认

确保 `.claude/skills/jira-test-extractor/config.json` 已正确配置：

```json
{
  "jira": {
    "url": "https://your-jira-instance.com",
    "username": "your-username",
    "password": "your-api-token-or-password"
  },
  "output_dir": "./test_cases"
}
```

---

## MCP 集成方式

**MCP (Model Context Protocol)** 是 Claude Code 与外部工具的标准集成协议，允许 Claude Code 直接调用 Jira workflow 工具。

### 方式一：创建 MCP 服务器包装现有功能

#### 1. 创建 MCP 服务器脚本

创建 `jira_mcp_server.py` 文件：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jira Workflow MCP Server
包装现有的 Jira 提取和文档生成功能
"""
import os
import sys
import json
from pathlib import Path

# 添加项目路径
_skill_dir = Path(__file__).parent / ".claude" / "skills" / "jira-test-extractor"
_src_dir = _skill_dir / "src"
sys.path.insert(0, str(_src_dir))

from src.extractor import JiraExtractor, load_config
from src.generator import convert_to_docs


class JiraMCPTool:
    """MCP 工具包装器"""
    
    def __init__(self):
        self.config = load_config(_skill_dir / "config.json")
        self.extractor = JiraExtractor(self.config)
        self.extractor.connect()
    
    def extract_ticket_info(self, ticket_url: str, output_dir: str = None):
        """提取 Jira Ticket 信息"""
        try:
            ticket_data = self.extractor.extract_ticket(ticket_url)
            
            # 保存到指定目录
            if output_dir:
                from src.extractor import save_ticket_data
                ticket_dir = save_ticket_data(ticket_data, output_dir)
                return {
                    "success": True,
                    "ticket_id": ticket_data["id"],
                    "path": ticket_dir,
                    "data": ticket_data
                }
            return {
                "success": True,
                "ticket_id": ticket_data["id"],
                "data": ticket_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_test_docs(self, json_path: str, template_path: str = None):
        """生成测试文档"""
        try:
            files = convert_to_docs(json_path, template_path=template_path)
            return {
                "success": True,
                "files": files
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


# MCP 服务器主函数
def main():
    import sys
    
    # MCP 服务器通信使用 stdin/stdout
    tool = JiraMCPTool()
    
    print(json.dumps({
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "capabilities": {
                "tools": [
                    {
                        "name": "extract_jira_ticket",
                        "description": "从 Jira Ticket URL 提取信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ticket_url": {"type": "string", "description": "Jira Ticket URL"},
                                "output_dir": {"type": "string", "description": "输出目录（可选）"}
                            },
                            "required": ["ticket_url"]
                        }
                    },
                    {
                        "name": "generate_test_documents",
                        "description": "从 JSON 测试用例生成文档（支持模板）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "json_path": {"type": "string", "description": "JSON 测试用例文件路径"},
                                "template_path": {"type": "string", "description": "Excel 模板文件路径（可选）"}
                            },
                            "required": ["json_path"]
                        }
                    }
                ]
            }
        }
    }), flush=True)
    
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            method = request.get("method")
            
            if method == "tools/call":
                tool_name = request["params"]["name"]
                args = request["params"]["arguments"]
                
                if tool_name == "extract_jira_ticket":
                    result = tool.extract_ticket_info(
                        args["ticket_url"],
                        args.get("output_dir")
                    )
                elif tool_name == "generate_test_documents":
                    result = tool.generate_test_docs(
                        args["json_path"],
                        args.get("template_path")
                    )
                else:
                    result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                
                response = {
                    "jsonrpc": "2.0",
                    "id": request["id"],
                    "result": {
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]
                    }
                }
                print(json.dumps(response), flush=True)
                
        except Exception as e:
            print(json.dumps({
                "jsonrpc": "2.0",
                "id": request.get("id", 1),
                "error": {"code": -1, "message": str(e)}
            }), flush=True)


if __name__ == "__main__":
    main()
```

#### 2. 运行 MCP 服务器

```bash
# 启动 MCP 服务器
python jira_mcp_server.py
```

#### 3. Claude Code 连接 MCP 服务器

**方式 A: 临时连接（单次会话）**

```bash
claude --mcp-config '{"server": {"command": "python", "args": ["jira_mcp_server.py"]}}'
```

**方式 B: 永久配置**

创建 `.mcp.json` 文件：

```json
{
  "servers": {
    "jira-workflow": {
      "command": "python",
      "args": ["jira_mcp_server.py"],
      "env": {}
    }
  }
}
```

然后启动 Claude Code：

```bash
claude
```

MCP 服务器会自动加载。

### 方式二：使用现有工具作为 MCP 工具

也可以直接包装现有的 Python 脚本：

```bash
# 在 Claude Code 中可以直接调用
claude "请提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息"

# Claude Code 会自动检测并使用 extract_test_cases.py
```

---

## CLI 集成方式

### 1. 直接使用 Claude Code CLI

#### 场景 A: 提取 Jira Ticket 信息

```bash
claude --print "请从 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 提取信息"

# 或者使用管道
echo "提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息" | claude --print
```

#### 场景 B: 生成测试用例文档

```bash
# 有模板
claude --print "请使用模板 ./templates/default_template.xlsx 生成测试文档，输入文件是 ./test_cases/PROJECT-123/test_cases.json"

# 无模板
claude --print "请生成测试文档，输入文件是 ./test_cases/PROJECT-123/test_cases.json"
```

### 2. 创建 Claude Code 会话进行交互

```bash
# 启动交互式会话
claude

# 在 Claude Code 中输入：
# "请帮我处理 Jira Ticket PROJECT-123"
# Claude Code 会自动识别并调用相关工具
```

### 3. 使用 Agent 模式自动化

创建 `jira-agent.json`：

```json
{
  "jira-processor": {
    "description": "自动处理 Jira Ticket 并生成测试用例",
    "prompt": "你是一个 Jira Ticket 处理专家。当用户提供 Jira URL 时，请：\n1. 提取 Ticket 信息\n2. 分析需求并生成测试用例 JSON\n3. 根据模板生成文档",
    "tools": ["Bash", "Read", "Edit"]
  }
}
```

使用 Agent：

```bash
claude --agent jira-processor "处理 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123"
```

---

## 实际工作流程示例

### 完整流程（使用 Claude Code）

#### 步骤 1: 提取 Jira Ticket 信息

```bash
# 启动 Claude Code
claude

# 在 Claude Code 中输入：
# "请提取 Jira Ticket https://your-jira-instance.com/browse/PROJECT-123 的信息"
```

Claude Code 会自动：
1. 调用 `extract_test_cases.py`
2. 保存到 `./test_cases/PROJECT-123/info.json`

#### 步骤 2: 生成测试用例 JSON

```bash
# 在同一个 Claude Code 会话中继续输入：
# "请读取 ./test_cases/PROJECT-123/info.json 并生成测试用例 JSON，保存到 test_cases.json"
```

Claude Code 会：
1. 读取 `info.json`
2. 分析需求
3. 生成符合模板的 `test_cases.json`

#### 步骤 3: 生成测试文档

**有模板时：**

```bash
# 在 Claude Code 中输入：
# "请使用模板 ./templates/default_template.xlsx 生成测试文档，输入文件是 ./test_cases/PROJECT-123/test_cases.json"
```

**无模板时：**

```bash
# 在 Claude Code 中输入：
# "请生成测试文档，输入文件是 ./test_cases/PROJECT-123/test_cases.json"
```

### 批量处理多个 Ticket

```bash
claude --print "请处理以下 Jira Tickets：
1. https://your-jira-instance.com/browse/PROJECT-123
2. https://your-jira-instance.com/browse/PROJECT-456
3. https://your-jira-instance.com/browse/PROJECT-789

对每个 Ticket 执行：
- 提取信息
- 生成测试用例
- 使用模板生成文档"
```

---

## 常见问题

### Q1: Claude Code 找不到 Jira 工具怎么办？

**解决方案：**

1. 确认工具路径正确：

```bash
cd .claude/skills/jira-test-extractor
python extract_test_cases.py --help
```

2. 创建符号链接或配置 PATH：

```bash
# Windows PowerShell
New-Item -ItemType SymbolicLink -Path "C:\ProgramData\claude-tools\jira-extract.cmd" -Target ".claude\skills\jira-test-extractor\extract_test_cases.py"
```

### Q2: MCP 服务器连接失败？

**解决方案：**

1. 检查 MCP 配置文件：

```json
{
  "servers": {
    "jira-workflow": {
      "command": "python",
      "args": [".claude/skills/jira-test-extractor/jira_mcp_server.py"],
      "env": {}
    }
  }
}
```

2. 手动测试 MCP 服务器：

```bash
python .claude/skills/jira-test-extractor/jira_mcp_server.py
```

### Q3: 如何在 VSCode 中使用 Claude Code？

**解决方案：**

1. 安装 Claude Code VSCode 扩展
2. 打开命令面板 (Ctrl+Shift+P)
3. 输入 `Claude: Start Session`
4. Claude Code 会自动检测项目中的工具

### Q4: 如何调试 Claude Code 的工具调用？

**解决方案：**

```bash
# 启用调试模式
claude --debug

# 查看详细日志
claude --debug-file debug.log
```

---

## 推荐的工作流程

### 方式 1: 交互式（推荐新手）

```bash
# 启动 Claude Code
claude

# 交互式输入命令
用户: "提取 Jira Ticket PROJECT-123 的信息"
用户: "读取 info.json 并生成测试用例"
用户: "使用模板生成测试文档"
```

### 方式 2: 脚本化（推荐自动化）

创建 `process_jira_ticket.sh`：

```bash
#!/bin/bash
TICKET_URL=$1
TEMPLATE_PATH=$2

# 提取信息
claude --print "提取 Jira Ticket $TICKET_URL 的信息" > /dev/null

# 生成测试用例（需要先有 test_cases.json）
# 这里可以使用 AI 生成或者手动准备

# 生成文档
claude --print "使用模板 $TEMPLATE_PATH 生成测试文档"
```

其中 `$TEMPLATE_PATH` 可以是：
- 模板文件路径：`./templates/default_template.xlsx`
- 或者留空以生成默认格式
```

### 方式 3: Agent 模式（推荐批量处理）

```bash
claude --agent jira-processor "批量处理以下 Tickets: PROJECT-123, PROJECT-456, PROJECT-789"
```

---

## 总结

- **MCP 集成**：适合需要双向通信、实时交互的场景
- **CLI 集成**：适合脚本化、自动化的场景
- **推荐组合**：交互式使用 Claude Code + Agent 模式处理批量任务

如有问题，请参考：
- Claude Code 官方文档：`claude --help`
- 项目文档：`.claude/README.md`
- 技能文档：`.claude/skills/jira-test-extractor/SKILL.md`
