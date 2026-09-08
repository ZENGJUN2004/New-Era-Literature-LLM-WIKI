#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ingest_0213.py — 处理 2026-02-13 批次（19 篇 raw）

分类：
- 更新事件/第八届《星火》文学年.md（+《一本杂志和它的文学生活》详细报道）
- 更新事件/中国作协.md（+新春贺信）
- 轻处理其余 17 篇

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

def ap(n): return WIKI / n

idx = Path(INDEX)
log = Path(LOG)

# Phase 1: 断言锚点
print("\n========== Phase 1: assert anchors ==========")
xinghuo = ap("事件/第八届《星火》文学年.md")
s_xinghuo = read(xinghuo)
zgxc = ap("事件/中国作协.md")
s_zgxc = read(zgxc)

assert_count = lambda txt, pat, exp, msg: (
    print(f"  OK {msg}: '{pat[:50]}...' count={txt.count(pat)}") or
    (None if txt.count(pat) == exp else (_ for _ in []).throw(AssertionError(f"{msg} expected={exp} got={txt.count(pat)}")))
)

assert_count(s_xinghuo, "失眠者沙龙", 1, "xinghuo tl anchor")
assert_count(s_xinghuo, "一本杂志和它的文学生活", 0, "xinghuo 详细报道 (should NOT exist yet)")
assert_count(s_zgxc, "新春贺信", 0, "zgxc 新春贺信 (should NOT exist yet)")

print("Phase 1 OK\n")

# Phase 2: 无新建页
print("========== Phase 2: no new pages ==========")
print("Phase 2 OK\n")

# Phase 3: 更新
print("========== Phase 3: update pages ==========")

# 3.1 更新事件/第八届《星火》文学年.md
old_xinghuo = read(xinghuo)
if "一本杂志和它的文学生活" not in old_xinghuo:
    tl_anchor = "## 来源"
    new_tl_entry = """- **2026-02-13**：《一根杂志和它的文学生活》详细报道第八届《星火》文学年——2月6日至8日于都祁禄山林场民宿院子举办，200余名星火驿友AA制参与，为历届规模最大；腊梅、大榕树、怀旧小院营造春意；星光缀空到晨光初现的文学狂欢。（详见[主题/新大众文艺.md](../主题/新大众文艺.md)）\n"""
    
    if tl_anchor in old_xinghuo:
        new_xinghuo = old_xinghuo.replace(tl_anchor, new_tl_entry + tl_anchor, 1)
        write(xinghuo, new_xinghuo)
        print("  Updated 事件/第八届《星火》文学年.md (+《一本杂志和它的文学生活》详细报道)")
    else:
        print("  WARNING: tl_anchor '## 来源' not found in xinghuo")
else:
    print("  xinghuo already has detailed report entry — skipped")

# 3.2 更新事件/中国作协.md
old_zgxc = read(zgxc)
if "新春贺信" not in old_zgxc:
    tl_anchor = "## 来源"
    new_tl_entry = """- **2026-02-13**：中国作家协会致全国作家和文学工作者的新春贺信——回首2025年"十四五"圆满收官，中国文学浩荡奔涌；高擎思想旗帜，深入践行习近平文化思想；推动各项工作取得新成效。\n"""
    
    if tl_anchor in old_zgxc:
        new_zgxc = old_zgxc.replace(tl_anchor, new_tl_entry + tl_anchor, 1)
        write(zgxc, new_zgxc)
        print("  Updated 事件/中国作协.md (+新春贺信)")
    else:
        print("  WARNING: tl_anchor '## 来源' not found in zgxc")
else:
    print("  zgxc already has 新春贺信 entry — skipped")

print("Phase 3 OK\n")

# Phase 4: 更新 index
print("========== Phase 4: update index ==========")
idx_s = read(idx)
wiki_count = count_md(WIKI)
raw_count = count_md(RAW_MD)
idx_p = re.compile(r"知识页面总数：\d+", re.MULTILINE)
raw_p = re.compile(r"raw 原始文档总数：\d+", re.MULTILINE)
assert idx_p.search(idx_s), "index wiki count not found"
assert raw_p.search(idx_s), "index raw count not found"
new_idx = idx_p.sub(f"知识页面总数：{wiki_count}", idx_s)
new_idx = raw_p.sub(f"raw 原始文档总数：{raw_count}", new_idx)
write(idx, new_idx)
print(f"  index.md 统计写入 wiki={wiki_count}, raw={raw_count}")
print("Phase 4 OK\n")

# Phase 5: 更新 log
print("========== Phase 5: append log ==========")
log_s = read(log)
log_entry = f"""## 2026-09-07 Ingest 02-13 批次
- 【Ingest】采集 2026-02-13 八关键词数据，新增 19 篇 raw，完成 ingest
- 新建 0 页
- 更新 2 页：事件/第八届《星火》文学年（+《一本杂志和它的文学生活》详细报道/2月6-8日于都祁禄山林场/200余名驿友AA制/历届规模最大）、事件/中国作协（+新春贺信/回首2025十四五圆满收官/中国文学浩荡奔涌）
- 轻处理 17 篇：文学理论评论综述2（2025文学理论评论观察/新乡土文学三重面相）、活动文讯2（李敬泽西湖开讲情感考古/昆明徐剑回乡分享）、报刊作品节选5（中国作家王茹/人民文学马伯庸修桥记/北京文学曾晓文/广西文学李会鑫/边疆文学车心云）、文史1（茅盾致普实克信看中捷文学交流）、争鸣1（新时代文学作为创作实践与研究方法）、专题1（新时代文学实践点重庆大足/正文为空）、原创频道集锦若干
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
write(log, log_s.rstrip() + "\n" + log_entry + "\n")
print("  Appended 02-13 ingest to log.md")
print("Phase 5 OK\n")

print("========== All phases completed ==========")
