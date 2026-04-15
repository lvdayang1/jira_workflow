#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试用例文档生成器 - 入口脚本

用法:
    # 无模板：生成 MD、DOCX、XLSX 默认格式
    python generate_docs.py <test_cases.json>

    # 有模板：根据模板格式生成对应文档
    python generate_docs.py <test_cases.json> -t template.xlsx
    python generate_docs.py <test_cases.json> -t template.docx
    python generate_docs.py <test_cases.json> -t template.md
"""
import os
import sys

# 直接添加到 src 目录到路径
_skill_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_skill_dir, "src")
sys.path.insert(0, _src_dir)

from generator import convert_to_docs


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='将 JSON 测试用例转换为文档格式',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 无模板（生成 MD、DOCX、XLSX 默认格式）
  python generate_docs.py test_cases.json

  # 有模板：根据模板格式生成对应文档
  python generate_docs.py test_cases.json -t template.xlsx
  python generate_docs.py test_cases.json -t template.docx
  python generate_docs.py test_cases.json -t template.md
        """
    )
    parser.add_argument('input_file', help='JSON 测试用例文件路径')
    parser.add_argument('-o', '--output', help='输出目录（默认与输入文件同目录）')
    parser.add_argument('-t', '--template', help='模板文件路径（可选）。不提供则生成 MD/DOCX/XLSX，提供则根据模板格式生成对应文档')

    args = parser.parse_args()

    try:
        files = convert_to_docs(args.input_file, args.output, args.template)
        print(f"\n转换完成！共生成 {len(files)} 个文件:")
        for f in files:
            print(f"  - {f}")
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()