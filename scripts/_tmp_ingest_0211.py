#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ingest_0211.py — 处理 2026-02-11 批次（14 篇 raw）

分类：
- 更新主题/新大众文艺.md（+《中国作家》×天津作协"全民阅读的意义"座谈会）
- 轻处理其余 13 篇

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
xdzwy = ap("主题/新大众文艺.md")
s = read(xdzwy)
assert_count = lambda txt, pat, exp, msg: (
    print(f"  OK {msg}: '{pat[:50]}...' count={s.count(pat)}") or
    (None if s.count(pat) == exp else (_ for _ in []).throw(AssertionError(f"{msg} expected={exp} got={s.count(pat)}")))
)
assert_count(s, "- **2026-02-09**：中国作协联合抖音", 1, "xdzwy tl anchor 02-09")
assert_count(s, "素人写作者代表参加座谈", 0, "xdzwy 素人写作者 (should NOT exist yet)")

print("Phase 1 OK\n")

# Phase 2: 无新建页（王家新/黄锦树/王德威/第八届《星火》文学年已在 02-10 创建）
print("========== Phase 2: no new pages ==========")
print("Phase 2 OK (王家新/黄锦树/王德威/第八届《星火》文学年 已存在于 02-10)\n")

# Phase 3: 更新
print("========== Phase 3: update xdzwy ==========")
old = read(xdzwy)

# 查找时间线末尾锚点并追加新条目（在"## 来源"之前）
tl_anchor = "## 来源"
new_tl_entry = """- **2026-02-09**：《中国作家》与天津作协联合举办"全民阅读的意义"座谈会暨首届"全民阅读征文大赛"启动仪式——范雨素、小海、于俊杰等素人写作者代表分享阅读经历；阎晶明强调活动落实《全民阅读促进条例》（2月1日实施）具有全国效应，在"新大众文艺蓬勃发展"背景下探讨"全民阅读"具有引领性；施战军提出全民阅读、新大众文艺与"大文学观"检验文明观价值观；贺绍俊主张开放性阅读理解；潘凯雄呼吁警惕快餐文化；汪惠仁强调覆盖残疾人/弱势群体，不排斥 AI 辅助阅读。详见 [事件/《中国作家》新大众文艺与大文学观座谈会.md](../事件/《中国作家》新大众文艺与大文学观座谈会.md)。\n"""

# 检查是否已存在"全民阅读的意义"座谈会条目
if "全民阅读的意义" not in old:
    if tl_anchor in old:
        new = old.replace(tl_anchor, new_tl_entry + tl_anchor, 1)
        write(xdzwy, new)
        print("  Updated 主题/新大众文艺.md (+《中国作家》×天津作协'全民阅读的意义'座谈会)")
    else:
        print("  WARNING: tl_anchor '## 来源' not found in xdzwy")
else:
    print("  xdzwy already has '全民阅读的意义' entry — skipped")

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
log_entry = f"""## 2026-09-07 Ingest 02-11 批次
- 【Ingest】采集 2026-02-11 八关键词数据，新增 14 篇 raw，完成 ingest
- 新建 0 页（王家新/黄锦树/王德威/第八届《星火》文学年 已存在于 02-10）
- 更新 1 页：主题/新大众文艺（+《中国作家》×天津作协"全民阅读的意义"座谈会/范雨素小海于俊杰素人写作者/阎晶明施战军贺绍俊潘凯雄汪惠仁陈东捷等发言/《全民阅读促进条例》2月1日实施/大文学观与阅读关系）
- 轻处理 13 篇：贺与诤诺奖作品评论1、洪治纲故乡文学评论1、沈嘉禄寄娘的微笑小说1、刘小男铁和尘散文1、2026年度网络文学选题指南1、激发原创活力期刊综述1、作家书画贺新春1、菡萏冠带巷小说1、许旸融媒时代文学记者评论1、人民文学葡文版首刊发行1、茅盾故居文学档案实践1、2026年2月期刊目录盘点1、老林场文学新婚文学年报道1
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
write(log, log_s.rstrip() + "\n" + log_entry + "\n")
print("  Appended 02-11 ingest to log.md")
print("Phase 5 OK\n")

print("========== All phases completed ==========")
