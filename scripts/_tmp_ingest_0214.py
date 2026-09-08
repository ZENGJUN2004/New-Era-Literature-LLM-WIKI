#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ingest_0214.py — 处理 2026-02-14 批次（11 篇 raw）

分类：
- 全轻处理（11篇）：报刊作品节选7、文学评论2、活动文讯1、文史1、访谈1

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
# 无更新页面，仅需验证 index 格式
idx_s = read(idx)
assert re.search(r"知识页面总数：\d+", idx_s), "index wiki count not found"
assert re.search(r"raw 原始文档总数：\d+", idx_s), "index raw count not found"
print("  index.md 格式验证 OK")
print("Phase 1 OK\n")

# Phase 2: 无新建页
print("========== Phase 2: no new pages ==========")
print("Phase 2 OK\n")

# Phase 3: 无更新页
print("========== Phase 3: no updates ==========")
print("Phase 3 OK (all light processing)\n")

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
log_entry = f"""## 2026-09-07 Ingest 02-14 批次
- 【Ingest】采集 2026-02-14 八关键词数据，新增 11 篇 raw，完成 ingest
- 新建 0 页
- 更新 0 页
- 轻处理 11 篇：报刊作品节选7（胶东文学林为攀南方有座赤莲台/程建华小人书铁匠铺、山东文学安宁寻找遗失的文字、上海文学周宏翔人海孤鸿、边疆文学冯娜诗）、文学评论2（闲时策马赏春色文学文物里的中国年/网络文学国际化传播与经典性生成）、活动文讯1（第28届新概念作文大赛181位新人同题竞写）、文史1（寻访中国侦探文学先贤程小青陆澹盦赵苕狂）、访谈1（《江南》主编哲贵期待浙江文学再现群星璀璨）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
write(log, log_s.rstrip() + "\n" + log_entry + "\n")
print("  Appended 02-14 ingest to log.md")
print("Phase 5 OK\n")

print("========== All phases completed ==========")
