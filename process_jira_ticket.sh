#!/bin/bash
# Jira Ticket 自动处理脚本
# 使用 Claude Code + MCP 自动化处理 Jira Ticket

set -e

# 配置
TICKET_URL="$1"
TEMPLATE_PATH="$2"
OUTPUT_DIR="${3:-./test_cases}"

if [ -z "$TICKET_URL" ]; then
    echo "用法: $0 <jira-ticket-url> [template-path] [output-dir]"
    echo "示例: $0 https://your-jira-domain.com/browse/PROJECT-123 ./用例模板.xlsx"
    exit 1
fi

echo "======================================"
echo "Jira Ticket 自动处理脚本"
echo "======================================"
echo "Ticket URL: $TICKET_URL"
echo "模板路径: ${TEMPLATE_PATH:-无}"
echo "输出目录: $OUTPUT_DIR"
echo ""

# 步骤 1: 启动 MCP 服务器（后台）
echo "[1/4] 启动 MCP 服务器..."
python jira_mcp_server.py &
MCP_PID=$!
sleep 2

# 步骤 2: 使用 Claude Code 提取 Ticket 信息
echo "[2/4] 提取 Jira Ticket 信息..."
claude_output=$(claude --print --mcp-config '{"server": {"command": "python", "args": ["jira_mcp_server.py"]}}' \
    "请使用 extract_jira_ticket 工具提取 Ticket: $TICKET_URL，输出目录: $OUTPUT_DIR")

echo "$claude_output"

# 提取 ticket_id
ticket_id=$(echo "$claude_output" | grep -oP '"ticket_id":\s*"\K[^"]+')
if [ -z "$ticket_id" ]; then
    echo "错误: 无法提取 ticket_id"
    kill $MCP_PID
    exit 1
fi

echo "Ticket ID: $ticket_id"

# 步骤 3: 生成测试用例 JSON（需要 AI 分析）
echo "[3/4] 生成测试用例 JSON..."
json_path="$OUTPUT_DIR/$ticket_id/test_cases.json"

# 如果 JSON 不存在，让 Claude Code 生成
if [ ! -f "$json_path" ]; then
    claude --print "请读取 $OUTPUT_DIR/$ticket_id/info.json 并生成测试用例 JSON，保存到 $json_path"
fi

# 步骤 4: 生成测试文档
echo "[4/4] 生成测试文档..."
if [ -n "$TEMPLATE_PATH" ]; then
    echo "使用模板: $TEMPLATE_PATH"
    claude --print "请使用 generate_test_documents 工具，输入文件: $json_path，模板: $TEMPLATE_PATH"
else
    echo "不使用模板，生成默认格式"
    claude --print "请使用 generate_test_documents 工具，输入文件: $json_path"
fi

# 清理
kill $MCP_PID
wait $MCP_PID 2>/dev/null || true

echo ""
echo "======================================"
echo "✅ 处理完成！"
echo "输出目录: $OUTPUT_DIR/$ticket_id"
echo "======================================"
