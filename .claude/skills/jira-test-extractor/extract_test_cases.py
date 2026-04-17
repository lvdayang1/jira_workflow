#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Jira Ticket 信息提取器 - 入口脚本

用法:
    python extract_test_cases.py <jira-ticket-id> [--config config.json] [--output ./test_cases] [--no-download]

示例:
    python extract_test_cases.py PROJECT-123
    python extract_test_cases.py https://jira.example.com/browse/PROJECT-123
"""
import os
import sys

# 直接添加到 src 目录到路径
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_skill_dir, "src")
sys.path.insert(0, _src_dir)

from extractor import (
    JiraExtractor, load_config, save_ticket_data,
    find_project_root, find_config_path, resolve_output_dir
)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="从 Jira Ticket 提取信息并保存到文件夹")
    parser.add_argument("ticket", help="Jira Ticket ID 或完整 URL（如 PROJECT-123）")
    parser.add_argument("--config", default=None, help="配置文件路径")
    parser.add_argument("--output", default=None, help="输出根目录")
    parser.add_argument("--no-download", action="store_true", help="不下载附件")
    args = parser.parse_args()

    project_root = find_project_root()
    config_path = args.config if args.config else find_config_path(project_root)
    output_dir = args.output if args.output else "./test_cases"
    output_dir = resolve_output_dir(output_dir, project_root)

    os.makedirs(output_dir, exist_ok=True)

    print(f"项目根目录: {project_root}", flush=True)
    print(f"输出目录: {output_dir}", flush=True)
    print(f"正在连接 Jira...", flush=True)

    config = load_config(config_path)
    extractor = JiraExtractor(config)
    extractor.connect()

    try:
        print(f"正在提取 Ticket 信息：{args.ticket}", flush=True)
        ticket_data = extractor.extract_ticket(args.ticket)
        print(f"已提取：{ticket_data['summary']}", flush=True)
        print(f"状态：{ticket_data['status']}", flush=True)
        print(f"优先级：{ticket_data['priority']}", flush=True)
        print(f"描述长度：{len(ticket_data['description'])} 字符", flush=True)
        print(f"评论数量：{len(ticket_data['comments'])}", flush=True)
        print(f"附件数量：{len(ticket_data['attachments'])}", flush=True)

        if not args.no_download and ticket_data["attachments"]:
            print("\n正在下载附件...", flush=True)
            ticket_data["attachments"] = extractor.download_attachments(
                ticket_data["id"],
                ticket_data["attachments"],
                output_dir
            )

        ticket_dir = save_ticket_data(ticket_data, output_dir)
        print(f"\n提取完成！数据保存在: {ticket_dir}", flush=True)
        print("\n下一步：请让 AI 模型读取该文件夹内容生成测试用例", flush=True)

    finally:
        extractor.disconnect()


if __name__ == "__main__":
    main()