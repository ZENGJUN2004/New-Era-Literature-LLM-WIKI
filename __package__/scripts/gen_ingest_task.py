#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
gen_ingest_task.py — 生成下一次 LLM Ingest 的任务清单
=====================================================
对比 raw/markdown 与 wiki/ 中已引用的来源，找出尚未被整理进 wiki 的
原始文档，生成 tasks/ingest_YYYYMMDD.md，列出待 ingest 清单。

运行后，把生成的 task 文件丢给 LLM（或本 Agent），由 LLM 按 AGENTS.md
规则完成：读取 raw 文档 → 新建/更新 wiki 页面 → 更新 index.md → 记 log.md。
"""

import argparse
import os
import re
import sys
from datetime import datetime


def extract_doc_id(name: str) -> str:
    """从文件名/路径提取稳定文档 ID。

    wiki 页 sources 里引用的是 raw/json/<contentId>.json，
    raw 文件名则带日期前缀（2026-08-13_<contentId>.md），
    统一抽尾部的数字 ID 才能比对。
    """
    m = re.search(r"(\d+)\.(?:json|md)$", name)
    return m.group(1) if m else name


def load_wiki_source_ids(root="wiki"):
    """扫描 wiki/ 下所有 md 的 sources 引用，返回已用 raw 文档 ID 集合。"""
    used = set()
    if not os.path.isdir(root):
        return used
    for dirpath, _, files in os.walk(root):
        for fn in files:
            if not fn.endswith(".md"):
                continue
            p = os.path.join(dirpath, fn)
            content = open(p, encoding="utf-8").read()
            for m in re.finditer(r"raw/(?:json|markdown)/[^\s)\]]+", content):
                used.add(extract_doc_id(m.group(0)))
    return used


def gen_task_file(raw_dir="raw/markdown", tasks_dir="tasks", wiki_root="wiki"):
    """生成待 ingest 任务清单，返回 (输出路径, 待整理篇数)。其他脚本可复用。"""
    os.makedirs(tasks_dir, exist_ok=True)
    used = load_wiki_source_ids(wiki_root)

    pending = []
    for year in sorted(os.listdir(raw_dir)):
        ydir = os.path.join(raw_dir, year)
        if not os.path.isdir(ydir):
            continue
        for fn in sorted(os.listdir(ydir)):
            if fn.endswith(".md") and extract_doc_id(fn) not in used:
                # 统一用正斜杠路径，保证 Markdown 链接可用
                pending.append(f"{year}/{fn}")

    stamp = datetime.now().strftime("%Y%m%d")
    out = os.path.join(tasks_dir, f"ingest_{stamp}.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(f"# Ingest 任务清单 {stamp}\n\n")
        f.write(f"待整理 raw 文档：{len(pending)} 篇\n\n")
        f.write("请按 AGENTS.md 规则：读取每篇 → 判断涉及的实体/主题 →\n")
        f.write("新建/更新 wiki 页面（含时间线，精确到日）→ 更新 index.md → 记录 log.md。\n\n")
        f.write("## 待 ingest 文档\n")
        for item in pending:
            f.write(f"- [{item}](../raw/markdown/{item})\n")
    return out, len(pending)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="raw/markdown", help="raw markdown 目录")
    ap.add_argument("--tasks", default="tasks", help="任务输出目录")
    args = ap.parse_args()

    out, n = gen_task_file(args.raw, args.tasks)
    print(f"生成任务清单：{out}（{n} 篇待 ingest）")
    return 0


if __name__ == "__main__":
    sys.exit(main())