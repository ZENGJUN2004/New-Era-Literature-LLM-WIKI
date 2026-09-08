#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
raw_to_md.py — 将采集的 raw/json/*.json 转为干净的 readable Markdown
====================================================================
转换规则：
- 保留全部元数据时间字段（displayTime/inputTime 精确到日）写进 frontmatter
- 正文 HTML 去掉样式标签，转为纯文本段落
- 输出到 raw/markdown/YEAR/ 下，文件名含日期，便于按时间浏览
- 原始 json 永不修改（Source of Truth）
"""

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta

BJT = timezone(timedelta(hours=8))


def strip_html(raw: str) -> str:
    """粗略但稳妥的 HTML->纯文本。"""
    if not raw:
        return ""
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", raw)
    s = re.sub(r"(?i)<br\s*/?>", "\n", s)
    s = re.sub(r"(?i)</p>", "\n\n", s)
    s = re.sub(r"(?i)</(div|h\d|li|tr)>", "\n", s)
    s = re.sub(r"(?s)<[^>]+>", "", s)
    s = html.unescape(s)
    s = re.sub(r"[ \t\u3000]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def to_md(rec: dict) -> str:
    # 标题去掉检索 API 返回的 <em> 高亮标签
    title = html.unescape(re.sub(r"(?i)</?em>", "", rec.get("title") or "无标题"))
    url = rec.get("url") or ""
    dt = rec.get("displayTime")
    pd = ""
    if dt:
        pd = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y-%m-%d %H:%M:%S")
    column = rec.get("originNodeRname") or ""
    source = rec.get("source") or ""
    author = rec.get("author") or ""
    body = strip_html(rec.get("contentOriginal") or rec.get("content") or "")

    lines = [
        "---",
        f"type: news",
        f"title: {title}",
        f"pubdate: {pd}",
        f"url: {url}",
        f"column: {column}",
        f"source: {source}",
        f"author: {author}",
        "---",
        "",
        f"# {title}",
        "",
        f"- **栏目**：{column}",
        f"- **发布时间**：{pd}",
        f"- **来源**：{source or '中国作家网'}",
        f"- **原文链接**：{url}",
        "",
    ]
    if body:
        lines.append("\n".join(p.strip() for p in body.split("\n\n") if p.strip()))
    else:
        lines.append("（正文为空）")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="raw/json -> raw/markdown")
    ap.add_argument("--src", default="raw/json", help="json 目录")
    ap.add_argument("--out", default="raw/markdown", help="markdown 输出目录")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    total = 0
    for fname in sorted(os.listdir(args.src)):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(args.src, fname), encoding="utf-8") as f:
            rec = json.load(f)
        dt = rec.get("displayTime")
        year = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y") if dt else "unknown"
        day = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y-%m-%d") if dt else "unknown"
        out_dir = os.path.join(args.out, year)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{day}_{fname[:-5]}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(to_md(rec))
        total += 1
    print(f"转换完成：{total} 个 json -> {args.out}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())