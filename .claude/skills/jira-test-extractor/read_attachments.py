#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
读取 Ticket 所有附件内容

用法:
    python read_attachments.py <ticket-id> [--output combined_content.txt]
"""
import os
import sys
import json
import argparse

# 添加 src 目录到路径
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_skill_dir, "src")
sys.path.insert(0, _src_dir)

from extractor import JiraExtractor, load_config
from attachment_reader import read_attachment


def download_and_read_attachments(ticket_id: str, config: dict, output_dir: str = None):
    """下载并读取所有附件"""
    # 读取 info.json 获取附件列表
    if output_dir is None:
        output_dir = os.path.join(_skill_dir, "test_cases", ticket_id)
    else:
        output_dir = os.path.join(output_dir, ticket_id)

    attachments_dir = os.path.join(output_dir, "attachments")
    os.makedirs(attachments_dir, exist_ok=True)

    info_path = os.path.join(output_dir, "info.json")
    if not os.path.exists(info_path):
        print(f"错误: 找不到 {info_path}")
        return None

    with open(info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)

    # 检查是否需要下载（如果附件有 url 字段但没有本地路径，需要下载）
    needs_download = any('url' in att and 'path' not in att for att in info['attachments'])

    if needs_download:
        extractor = JiraExtractor(config)
        extractor.connect()

        print(f"开始下载 {len(info['attachments'])} 个附件...")

        # 下载所有附件
        for att in info['attachments']:
            if 'path' in att:
                print(f"  跳过(已存在): {att['filename']}")
                continue

            filename = att['filename']
            url = att['url']
            filepath = os.path.join(attachments_dir, filename)

            try:
                response = extractor.session.get(url)
                if response.ok:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    # 更新 info.json 中的附件信息
                    att['path'] = filepath
                    att['status'] = 'success'
                    print(f"  下载成功: {filename}")
                else:
                    print(f"  下载失败: {filename} - {response.status_code}")
            except Exception as e:
                print(f"  下载错误: {filename} - {e}")

        # 保存更新后的 info.json
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, ensure_ascii=False, indent=2)

        extractor.disconnect()
    else:
        print("附件已下载，直接读取...")

    # 读取所有附件内容
    print("\n开始读取附件内容...")
    attachment_contents = []

    for att in info['attachments']:
        filename = att['filename']
        filepath = os.path.join(attachments_dir, filename)

        if not os.path.exists(filepath):
            continue

        print(f"  读取: {filename}")
        content = read_attachment(filepath)

        if content and not content.startswith('[不支持'):
            attachment_contents.append({
                'filename': filename,
                'content': content
            })

    return attachment_contents


def combine_ticket_info(info: dict, attachment_contents: list, output_path: str = None):
    """组合 ticket 信息和附件内容"""

    combined = {
        'ticket_id': info['id'],
        'summary': info.get('summary', ''),
        'status': info.get('status', ''),
        'priority': info.get('priority', ''),
        'description': info.get('description', ''),
        'comments': info.get('comments', []),
        'attachments_summary': [
            {'filename': a['filename'], 'content_preview': a['content'][:500] + '...' if len(a['content']) > 500 else a['content']}
            for a in attachment_contents
        ],
        'full_attachment_contents': attachment_contents
    }

    if output_path:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(combined, f, ensure_ascii=False, indent=2)
        print(f"\n组合内容已保存到: {output_path}")

    return combined


def print_combined_info(combined: dict):
    """打印组合后的信息"""
    print("\n" + "="*60)
    print(f"Ticket: {combined['ticket_id']} - {combined['summary']}")
    print("="*60)

    print("\n【基本信息】")
    print(f"状态: {combined['status']}")
    print(f"优先级: {combined['priority']}")

    print("\n【描述】")
    print(combined['description'][:1000] + '...' if len(combined['description']) > 1000 else combined['description'])

    print("\n【评论】")
    if combined['comments']:
        for c in combined['comments']:
            print(f"  - {c.get('author', 'Unknown')} ({c.get('time', '')}): {c.get('body', '')[:200]}")
    else:
        print("  (无评论)")

    print("\n【附件列表】")
    for att in combined['attachments_summary']:
        print(f"  - {att['filename']}")
        print(f"    内容预览: {att['content_preview'][:300]}...")

    print("\n【完整附件内容】")
    for att in combined['full_attachment_contents']:
        print(f"\n--- {att['filename']} ---")
        content = att['content']
        # 截断过长的内容
        if len(content) > 2000:
            print(content[:2000] + '\n... (内容已截断) ...')
        else:
            print(content)


def main():
    parser = argparse.ArgumentParser(description="读取 Ticket 所有附件内容")
    parser.add_argument("ticket_id", help="Jira Ticket ID")
    parser.add_argument("--output", "-o", default=None, help="输出文件路径(JSON)")
    parser.add_argument("--config", "-c", default=None, help="配置文件路径")
    args = parser.parse_args()

    # 确定配置文件路径
    if args.config:
        config_path = args.config
    else:
        skill_dir = os.path.dirname(os.path.abspath(__file__))
        # 优先查找 config.json.local，然后是 config.json
        local_config = os.path.join(skill_dir, "config.json.local")
        normal_config = os.path.join(skill_dir, "config.json")
        config_path = local_config if os.path.exists(local_config) else normal_config

    if not os.path.exists(config_path):
        print(f"错误: 配置文件不存在: {config_path}")
        return 1

    config = load_config(config_path)

    # 读取 info.json
    ticket_id = args.ticket_id.upper()
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(skill_dir, "test_cases", ticket_id)
    info_path = os.path.join(output_dir, "info.json")

    if not os.path.exists(info_path):
        print(f"错误: 找不到 {info_path}，请先运行 extract_test_cases.py")
        return 1

    with open(info_path, 'r', encoding='utf-8') as f:
        info = json.load(f)

    # 下载并读取附件
    attachment_contents = download_and_read_attachments(ticket_id, config, output_dir=None)

    if attachment_contents is None:
        return 1

    # 组合信息
    combined = combine_ticket_info(info, attachment_contents, args.output)

    # 打印信息
    print_combined_info(combined)

    return 0


if __name__ == "__main__":
    sys.exit(main())
