# -*- coding: utf-8 -*-
"""
Jira 信息抽取器 - 从 Jira Ticket 提取信息
"""
import os
import json
import re
import base64
from pathlib import Path
import requests


class JiraExtractor:
    """Jira Ticket 信息提取器"""

    def __init__(self, config):
        """
        初始化提取器

        Args:
            config: 配置字典，包含 jira url, username, password
        """
        self.config = config
        self.jira_url = config["jira"]["url"].rstrip("/")
        self.session = requests.Session()
        self._setup_auth()

    def _setup_auth(self):
        """设置 HTTP Basic Auth"""
        username = self.config["jira"]["username"]
        password = self.config["jira"]["password"]
        credentials = f"{username}:{password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        })

    def connect(self):
        """连接到 Jira（验证认证）"""
        # 验证连接
        response = self.session.get(f"{self.jira_url}/rest/api/2/myself")
        if not response.ok:
            raise Exception(f"Jira 认证失败: {response.status_code}")
        return self

    def disconnect(self):
        """断开连接"""
        self.session.close()

    def _get_rest_api(self, endpoint):
        """通过 REST API 获取数据"""
        url = f"{self.jira_url}{endpoint}"
        response = self.session.get(url)
        if response.ok:
            return response.json()
        return None

    def _extract_ticket_id(self, url):
        """从 URL 提取 ticket ID"""
        match = re.search(r"/browse/([A-Z]+-\d+)", url)
        if match:
            return match.group(1)
        raise ValueError(f"无法从 URL 中提取 ticket ID：{url}")

    def _fix_url(self, url):
        """修复 URL（https -> http）"""
        if url.startswith("https://"):
            url = "http://" + url[8:]
        return url

    def _clean_text(self, text):
        """清理文本"""
        if not text:
            return ""
        return " ".join(str(text).split())

    def _clean_html(self, html_content):
        """清理 HTML 标签"""
        if not html_content:
            return ""
        text = re.sub(r'<[^>]+>', '', str(html_content))
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&amp;', '&')
        return " ".join(text.split())

    def _parse_comments(self, comments_data):
        """解析评论"""
        comments = []
        for c in comments_data:
            author = c.get("author", {}).get("displayName", "Unknown")
            created = c.get("created", "")[:10] if c.get("created") else ""
            body = self._clean_html(c.get("body", ""))
            comments.append({
                "author": author,
                "time": created,
                "body": body
            })
        return comments

    def _parse_attachments(self, attachments_data):
        """解析附件"""
        attachments = []
        for att in attachments_data:
            attachments.append({
                "filename": att.get("filename", ""),
                "url": att.get("content", ""),
                "size": att.get("size", 0),
                "mimeType": att.get("mimeType", "")
            })
        return attachments

    def _get_unique_filename(self, filepath):
        """获取不重复的文件名"""
        if not os.path.exists(filepath):
            return filepath
        base, ext = os.path.splitext(filepath)
        counter = 1
        while os.path.exists(filepath):
            filepath = f"{base}_{counter}{ext}"
            counter += 1
        return filepath

    def extract_ticket(self, ticket):
        """
        提取 Ticket 信息

        Args:
            ticket: Jira Ticket URL 或 Ticket ID（如 "PROJ-123"）

        Returns:
            包含 ticket 信息的字典
        """
        # 判断是 URL 还是纯 ticket ID
        if "/" in ticket or "://" in ticket:
            ticket_id = self._extract_ticket_id(ticket)
            url = self._fix_url(ticket)
        else:
            # 纯 ticket ID，直接使用
            ticket_id = ticket.upper()
            url = f"{self.jira_url}/browse/{ticket_id}"

        print(f"正在通过 REST API 获取 Ticket 信息...", flush=True)
        api_url = f"/rest/api/2/issue/{ticket_id}?fields=summary,status,priority,assignee,reporter,created,updated,description,comment,attachment"
        data = self._get_rest_api(api_url)

        if not data:
            raise Exception(f"无法获取 Ticket {ticket_id} 的 REST API 数据")

        fields = data.get("fields", {})

        assignee = fields.get("assignee")
        reporter = fields.get("reporter")

        comments_data = fields.get("comment", {}).get("comments", [])

        ticket_data = {
            "id": ticket_id,
            "url": url,
            "summary": fields.get("summary", ""),
            "status": self._clean_text(fields.get("status", {}).get("name", "")),
            "priority": self._clean_text(fields.get("priority", {}).get("name", "")),
            "assignee": assignee.get("displayName", "") if assignee else "",
            "reporter": reporter.get("displayName", "") if reporter else "",
            "created": fields.get("created", "")[:10] if fields.get("created") else "",
            "updated": fields.get("updated", "")[:10] if fields.get("updated") else "",
            "description": self._clean_html(fields.get("description", "")),
            "comments": self._parse_comments(comments_data),
            "attachments": self._parse_attachments(fields.get("attachment", [])),
        }
        return ticket_data

    def download_attachments(self, ticket_id, attachments, output_dir):
        """
        下载附件

        Args:
            ticket_id: Ticket ID
            attachments: 附件列表
            output_dir: 输出目录

        Returns:
            下载后的附件列表
        """
        downloaded = []
        att_dir = os.path.join(output_dir, ticket_id, "attachments")
        os.makedirs(att_dir, exist_ok=True)

        for att in attachments:
            filename = att["filename"]
            url = att["url"]
            try:
                response = self.session.get(url)
                if response.ok:
                    filepath = os.path.join(att_dir, filename)
                    filepath = self._get_unique_filename(filepath)
                    actual_filename = os.path.basename(filepath)
                    with open(filepath, "wb") as f:
                        f.write(response.body())
                    downloaded.append({
                        "filename": actual_filename,
                        "path": filepath,
                        "status": "success"
                    })
                    print(f"  下载成功: {actual_filename}", flush=True)
                else:
                    downloaded.append({
                        "filename": filename,
                        "url": url,
                        "status": "failed"
                    })
                    print(f"  下载失败: {filename}", flush=True)
            except Exception as e:
                downloaded.append({
                    "filename": filename,
                    "url": url,
                    "status": "error",
                    "error": str(e)
                })
                print(f"  下载错误: {filename} - {e}", flush=True)
        return downloaded


def load_config(config_path):
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"配置文件不存在：{config_path}，请创建 config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_ticket_data(ticket_data, output_dir):
    """
    保存 Ticket 数据到文件夹

    Args:
        ticket_data: Ticket 数据字典
        output_dir: 输出目录

    Returns:
        Ticket 文件夹路径
    """
    ticket_id = ticket_data["id"]
    ticket_dir = os.path.join(output_dir, ticket_id)
    os.makedirs(ticket_dir, exist_ok=True)

    info_path = os.path.join(ticket_dir, "info.json")
    with open(info_path, "w", encoding="utf-8") as f:
        json.dump(ticket_data, f, ensure_ascii=False, indent=2)

    print(f"信息已保存到: {info_path}")
    return ticket_dir


def find_project_root():
    """查找项目根目录"""
    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / ".claude").exists() or (parent / "config.json").exists():
            return parent
    return Path(os.getcwd())


def find_config_path(project_root):
    """查找配置文件路径"""
    search_paths = [
        project_root / "config.json.local",
        project_root / ".claude" / "config.json.local",
        project_root / "config.json",
        project_root / ".claude" / "config.json",
        Path(os.getcwd()) / "config.json.local",
        Path(os.getcwd()) / ".claude" / "config.json.local",
        Path(os.getcwd()) / "config.json",
        Path(os.getcwd()) / ".claude" / "config.json",
    ]
    for path in search_paths:
        if path.exists():
            return path
    return project_root / "config.json.local"


def resolve_output_dir(output_dir, project_root):
    """解析输出目录"""
    output_path = Path(output_dir)
    if output_path.is_absolute():
        return str(output_path)
    return str((project_root / output_dir).resolve())


if __name__ == "__main__":
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

    finally:
        extractor.disconnect()