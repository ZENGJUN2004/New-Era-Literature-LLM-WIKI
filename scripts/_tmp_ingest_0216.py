#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ingest_0216.py — 处理 2026-02-16 批次（1 篇 raw）
页面已手动创建，仅更新统计和日志
"""
import os, sys, re, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW_MD = ROOT / "raw" / "markdown" / "2026"
WIKI = ROOT / "wiki"
INDEX = ROOT / "index.md"
LOG = ROOT / "log.md"

def count_md(d):
    return len(glob.glob(str(d / "**" / "*.md"), recursive=True))

def read(f):
    return (f.read_text(encoding="utf-8") if f.exists() else "")

def write(f, t):
    f.write_text(t, encoding="utf-8")

idx = Path(INDEX)
log = Path(LOG)

# Phase 1: 断言锚点
print("\n========== Phase 1: assert anchors ==========")
idx_s = read(idx)
assert re.search(r"知识页面总数：\d+", idx_s), "index wiki count not found"
assert re.search(r"raw 原始文档总数：\d+", idx_s), "index raw count not found"
print("  index.md 格式验证 OK")
print("Phase 1 OK\n")

# Phase 2: 页面已创建（晓苏.md）
print("========== Phase 2: page already created ==========")
print("  人物/晓苏.md 已存在，跳过创建")
print("Phase 2 OK\n")

# Phase 3: 无更新页
print("========== Phase 3: no updates ==========")
print("Phase 3 OK\n")

# Phase 4: 更新 index
print("========== Phase 4: update index ==========")
wiki_count = count_md(WIKI)
raw_count = count_md(RAW_MD)
new_idx = re.sub(r"知识页面总数：\d+", f"知识页面总数：{wiki_count}", idx_s)
new_idx = re.sub(r"raw 原始文档总数：\d+", f"raw 原始文档总数：{raw_count}", new_idx)
write(idx, new_idx)
print(f"  index.md 统计写入 wiki={wiki_count}, raw={raw_count}")
print("Phase 4 OK\n")

# Phase 5: 更新 log
print("========== Phase 5: append log ==========")
log_s = read(log)
log_entry = f"""## 2026-09-08 Ingest 02-16 批次
- 【Ingest】采集 2026-02-16 八关键词数据，新增 1 篇 raw，完成 ingest
- 新建 1 页：人物/晓苏（国家一级作家，文学界称第二个"路遥"，悼念文章）
- 更新 0 页
- 轻处理 0 篇
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
write(log, log_s.rstrip() + "\n" + log_entry + "\n")
print("  Appended 02-16 ingest to log.md")
print("Phase 5 OK\n")

print("========== All phases completed ==========")
