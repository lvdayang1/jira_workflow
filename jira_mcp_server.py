#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jira Workflow MCP Server
包装现有的 Jira 提取和文档生成功能供 Claude Code 调用
"""
import os
import sys
import json
from pathlib import Path

# 添加项目路径
_current_dir = Path(__file__).parent
_skill_dir = _current_dir / ".trae" / "skills" / "jira-test-extractor"
_src_dir = _skill_dir / "src"
sys.path.insert(0, str(_src_dir))

from src.extractor import JiraExtractor, load_config, save_ticket_data
from src.generator import convert_to_docs


class JiraWorkflowTool:
    """Jira Workflow 工具包装器"""

    def __init__(self):
        self.config = load_config(_skill_dir / "config.json")
        self.extractor = JiraExtractor(self.config)
        self.extractor.connect()

    def extract_ticket(self, ticket_url: str, output_dir: str = None):
        """提取 Jira Ticket 信息

        Args:
            ticket_url: Jira Ticket URL
            output_dir: 输出目录（可选）

        Returns:
            dict: 包含提取结果的字典
        """
        try:
            print(f"[MCP] 正在提取 Ticket: {ticket_url}", flush=True)
            ticket_data = self.extractor.extract_ticket(ticket_url)

            # 保存到指定目录
            if output_dir:
                ticket_dir = save_ticket_data(ticket_data, output_dir)
                return {
                    "success": True,
                    "ticket_id": ticket_data["id"],
                    "summary": ticket_data["summary"],
                    "path": ticket_dir,
                    "data": ticket_data
                }

            return {
                "success": True,
                "ticket_id": ticket_data["id"],
                "summary": ticket_data["summary"],
                "data": ticket_data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def generate_documents(self, input_file: str, template_path: str = None, output_dir: str = None):
        """生成测试文档

        Args:
            input_file: JSON 或 MD 测试用例文件路径
            template_path: 模板文件路径（可选）
            output_dir: 输出目录（可选）

        Returns:
            dict: 包含生成文件列表的字典
        """
        try:
            print(f"[MCP] 正在生成文档: {input_file}", flush=True)
            files = convert_to_docs(input_file, output_dir, template_path)

            return {
                "success": True,
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_ticket_info(self, ticket_id: str):
        """获取已保存的 Ticket 信息

        Args:
            ticket_id: Ticket ID

        Returns:
            dict: Ticket 信息
        """
        try:
            test_cases_dir = _skill_dir / "test_cases"
            info_path = test_cases_dir / ticket_id / "info.json"

            if not info_path.exists():
                return {
                    "success": False,
                    "error": f"找不到 Ticket {ticket_id} 的信息文件"
                }

            with open(info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            return {
                "success": True,
                "data": data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }


def main():
    """MCP 服务器主函数"""
    import sys

    tool = JiraWorkflowTool()

    # 发送初始化响应（MCP 协议）
    init_response = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "capabilities": {
                "tools": [
                    {
                        "name": "extract_jira_ticket",
                        "description": "从 Jira Ticket URL 提取信息并保存",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ticket_url": {
                                    "type": "string",
                                    "description": "Jira Ticket 的完整 URL，例如 https://your-jira-domain.com/browse/PROJECT-123"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录路径（可选，默认 ./test_cases）"
                                }
                            },
                            "required": ["ticket_url"]
                        }
                    },
                    {
                        "name": "generate_test_documents",
                        "description": "从 JSON 或 Markdown 测试用例生成文档（支持 Excel/Word/Markdown 模板）",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "input_file": {
                                    "type": "string",
                                    "description": "JSON 或 MD 测试用例文件的完整路径"
                                },
                                "template_path": {
                                    "type": "string",
                                    "description": "模板文件路径（可选）。支持 .xlsx、.docx、.md 格式。不提供则生成 MD/DOCX/XLSX 三种默认格式"
                                },
                                "output_dir": {
                                    "type": "string",
                                    "description": "输出目录（可选，默认与输入文件同目录）"
                                }
                            },
                            "required": ["input_file"]
                        }
                    },
                    {
                        "name": "get_ticket_info",
                        "description": "获取已保存的 Jira Ticket 信息",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "ticket_id": {
                                    "type": "string",
                                    "description": "Ticket ID，例如 PROJECT-123"
                                }
                            },
                            "required": ["ticket_id"]
                        }
                    }
                ]
            }
        }
    }

    print(json.dumps(init_response), flush=True)

    # 处理请求
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
            request_id = request.get("id", 1)
            method = request.get("method")

            if method == "tools/call":
                tool_name = request["params"]["name"]
                args = request["params"]["arguments"]

                if tool_name == "extract_jira_ticket":
                    result = tool.extract_ticket(
                        args["ticket_url"],
                        args.get("output_dir")
                    )
                elif tool_name == "generate_test_documents":
                    result = tool.generate_documents(
                        args["input_file"],
                        args.get("template_path"),
                        args.get("output_dir")
                    )
                elif tool_name == "get_ticket_info":
                    result = tool.get_ticket_info(args["ticket_id"])
                else:
                    result = {
                        "success": False,
                        "error": f"未知的工具: {tool_name}"
                    }

                # 构建响应
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, ensure_ascii=False, indent=2)
                            }
                        ]
                    }
                }

                print(json.dumps(response), flush=True)

            elif method == "notifications/show":
                # 忽略通知
                pass

            else:
                # 未知方法
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"方法未找到: {method}"
                    }
                }
                print(json.dumps(response), flush=True)

        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": 1,
                "error": {
                    "code": -32700,
                    "message": f"JSON 解析错误: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id", 1) if 'request' in locals() else 1,
                "error": {
                    "code": -1,
                    "message": f"服务器错误: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nMCP 服务器已停止", flush=True)
        sys.exit(0)
    except Exception as e:
        print(json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "error": {
                "code": -1,
                "message": f"启动失败: {str(e)}"
            }
        }), flush=True)
        sys.exit(1)
