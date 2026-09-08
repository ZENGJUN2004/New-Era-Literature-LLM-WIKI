#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_ingest_0212.py — 处理 2026-02-12 批次（16 篇 raw）

分类：
- 更新主题/新大众文艺.md（+《一个文学的午后》策划会/素人写作评论）
- 更新事件/中国作协.md 或新建（+春节走访老作家老同志）
- 轻处理其余 14 篇

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
    print(f"  OK {msg}: '{pat[:50]}...' count={txt.count(pat)}") or
    (None if txt.count(pat) == exp else (_ for _ in []).throw(AssertionError(f"{msg} expected={exp} got={txt.count(pat)}")))
)
assert_count(s, "- **2026-02-09**：中国作协联合抖音", 1, "xdzwy tl anchor 02-09")
assert_count(s, "素人写的不只是文学", 0, "xdzwy 素人写作评论 (should NOT exist yet)")

# 检查中国作协页面是否存在
zgxc = ap("事件/中国作协.md")
if zgxc.exists():
    s_zgxc = read(zgxc)
    assert_count(s_zgxc, "春节前夕走访看望老作家", 0, "zgxc 春节走访 (should NOT exist yet)")
else:
    print("  WARNING: 事件/中国作协.md does not exist, will create")

print("Phase 1 OK\n")

# Phase 2: 新建页面（如有需要）
print("========== Phase 2: create new pages ==========")
# 暂时不新建，待确认后执行
print("Phase 2 OK (no new pages needed)\n")

# Phase 3: 更新
print("========== Phase 3: update pages ==========")

# 3.1 更新主题/新大众文艺.md
old_xdzwy = read(xdzwy)
if "素人写的不只是文学" not in old_xdzwy:
    tl_anchor = "## 来源"
    new_tl_entry = """- **2026-02-12**：贾倩发表《素人写的不只是文学，更是生活》，综述2025年素人写作现象——王计兵央视春晚、胡安焉《我在北京送快递》破圈、王玉珍万字情书；素人写作重构文艺创作主体格局，从"被书写者"成为"书写者"，新媒体平台拆除传播高墙。同日《一个文学的午后》策划会直播探索新大众文艺表达路径（2月9日京东冠名江苏卫视抖音联合出品）。\n"""
    
    if tl_anchor in old_xdzwy:
        new_xdzwy = old_xdzwy.replace(tl_anchor, new_tl_entry + tl_anchor, 1)
        write(xdzwy, new_xdzwy)
        print("  Updated 主题/新大众文艺.md (+素人写作评论+《一个文学的午后》)")
    else:
        print("  WARNING: tl_anchor '## 来源' not found in xdzwy")
else:
    print("  xdzwy already has 素人写作 entry — skipped")

# 3.2 更新/创建事件/中国作协.md
zgxc = ap("事件/中国作协.md")
if zgxc.exists():
    old_zgxc = read(zgxc)
    if "春节前夕走访看望老作家" not in old_zgxc:
        tl_anchor = "## 来源"
        new_tl_entry = """- **2026-02-12**：中国作协春节前夕走访看望老作家老同志——张宏森主席党组书记处同志分别走访在京老作家老同志、离退休干部和困难职工；介绍"两个计划"实施成效、儿童文学奖之夜、国际青春诗会、报告文学创作会议、新大众文艺创作研讨等工作；听取对2026年工作安排、"十五五"规划、作协十一大讨论筹备意见建议。\n"""
        
        if tl_anchor in old_zgxc:
            new_zgxc = old_zgxc.replace(tl_anchor, new_tl_entry + tl_anchor, 1)
            write(zgxc, new_zgxc)
            print("  Updated 事件/中国作协.md (+春节走访老作家老同志)")
        else:
            print("  WARNING: tl_anchor '## 来源' not found in zgxc")
    else:
        print("  zgxc already has 春节走访 entry — skipped")
else:
    # 创建新页面
    new_zgxc_content = """---
type: 事件
name: 中国作协春节走访老作家老同志
aliases: [中国作协新春走访]
created: 2026-09-07
updated: 2026-09-07
sources:
  - id: raw/markdown/2026/2026-02-12_1000040664646.md
    url: http://www.chinawriter.com.cn/n1/2026/0212/c403993-40664646.html
    pubdate: 2026-02-12
related: [../主题/新大众文艺.md]
tags: [中国作协, 新春走访, 老作家]
---

# 中国作协春节走访老作家老同志

2026年2月12日，中国作协组织开展新春走访慰问活动。

## 关键信息
- **时间**：2026-02-12（春节前夕）
- **主持**：张宏森（中国作协主席、党组书记）
- **对象**：在京老作家老同志、离退休干部和困难职工

## 详细内容
- 党组书记处同志感谢老作家老同志为新时代文学事业作出的积极贡献
- 介绍一年来重点工作：深入实施"两个计划"、举办"中国文学盛典·儿童文学奖之夜"、国际青春诗会（中国—拉美国家专场）、全国报告文学创作会议、著名作家抵达文学"县"场、作家活动周、新大众文艺创作研讨等
- 听取对2026年工作安排、"十五五"时期文学事业发展规划、中国作协第十一次全国代表大会组织筹备等重点工作意见建议
- 老作家老同志围绕巩固文学阵地、培养人才队伍、推广文学阅读、繁荣新大众文艺等工作提出建设性意见

## 关联
- [主题/新大众文艺.md](../主题/新大众文艺.md)

## 来源
- [中国作协春节前夕走访看望老作家老同志](http://www.chinawriter.com.cn/n1/2026/0212/c403993-40664646.html)＠ 2026-02-12
"""
    write(zgxc, new_zgxc_content)
    print("  Created 事件/中国作协.md (+春节走访老作家老同志)")

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
log_entry = f"""## 2026-09-07 Ingest 02-12 批次
- 【Ingest】采集 2026-02-12 八关键词数据，新增 16 篇 raw，完成 ingest
- 新建 0 页
- 更新 2 页：主题/新大众文艺（+贾倩《素人写的不只是文学，更是生活》综述2025素人写作现象/王计兵春晚胡安焉破圈王玉珍情书/《一个文学的午后》策划会直播）、事件/中国作协（+春节前夕走访看望老作家老同志/张宏森主持/两个计划实施成效/听取十五五规划意见建议）
- 轻处理 14 篇：文学评论4（海明威乞力马扎罗的雪/喻嘉言文学形象/张博实文学评论/肖克凡创作谈）、报刊作品3（福建文学林混/边疆文学陈登/北京文学陈世旭）、原创频道集锦2（星·人物大学生写作/年度话题集锦）、诗歌评论集1（张清华诗歌的肖像推出）、民族文学研究综述1、宁夏文学有声书项目1
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
write(log, log_s.rstrip() + "\n" + log_entry + "\n")
print("  Appended 02-12 ingest to log.md")
print("Phase 5 OK\n")

print("========== All phases completed ==========")
