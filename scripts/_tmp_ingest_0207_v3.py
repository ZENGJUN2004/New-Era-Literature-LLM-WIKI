# -*- coding: utf-8 -*-
"""Fix 02-07 ingest for 新大众文艺.md (repair duplicates + add missing entries)."""
import io, os, glob

WIKI = r"d:\zjun\新时代文学LLMWIKI\wiki"
INDEX = r"d:\zjun\新时代文学LLMWIKI\index.md"
LOG = r"d:\zjun\新时代文学LLMWIKI\log.md"

def read(path):
    with io.open(path, "r", encoding="utf-8") as f:
        return f.read()

def write(path, content):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

def assert_count(text, sub, expected, desc):
    c = text.count(sub)
    assert c == expected, f"FAIL [{desc}] count={c} expected={expected}"

def count_md(root):
    return len(glob.glob(os.path.join(root, "**", "*.md"), recursive=True))

print("Phase 1: Reading and asserting anchors...")

xdzwy = read(os.path.join(WIKI, r"主题\新大众文艺.md"))
idx = read(INDEX)
lg = read(LOG)

# --- Fix 1: duplicate related line (lines 76) ---
dup = 'related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md] [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]'
assert_count(xdzwy, dup, 1, "xdzwy dup related")
xdzwy = xdzwy.replace(dup, 'related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]', 1)

# --- Fix 2: 02-04 source missing pubdate ---
xdzwy = xdzwy.replace(
    'url: http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html\n  - id:',
    'url: http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html\n    pubdate: 2026-02-04\n  - id:',
    1
)

# --- Fix 3: add 02-07 frontmatter source ---
xdzwy = xdzwy.replace(
    '    pubdate: 2026-02-06\nrelated:',
    '    pubdate: 2026-02-06\n  - id: raw/markdown/2026/2026-02-07_1000040661415.md\n    url: http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html\n    pubdate: 2026-02-07\nrelated:',
    1
)
assert_count(xdzwy, 'pubdate: 2026-02-07', 1, "xdzwy fm 0207")

# --- Fix 4: add 02-07 timeline entry (after line 120) ---
xdzwy = xdzwy.replace(
    '- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野；季亚娅谈杂志是小小的"肺"，面向碎片化时代如何抵达更多读者（详见下节）。\n\n### 北京皮村新工人文学小组',
    '''- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野；季亚娅谈杂志是小小的"肺"，面向碎片化时代如何抵达更多读者（详见下节）。
- **2026-02-07**：徐元锋发表《雪原里，有个热腾腾的文学小院》，报道宁夏西吉县木兰书院农民作家剧本创作培训班——史静波返乡创办，1600多名写作者、300多名农民作者；马金莲负责南麓文学社；农民作家单小花、李成山参与舞台剧；西吉县获中华文学基金会"文学之乡"称号；"文学村BA"直播25场助农销售80多万元（详见下节）。

### 北京皮村新工人文学小组''',
    1
)
assert_count(xdzwy, "- **2026-02-07**：徐元锋发表", 1, "xdzwy tl updated")

# --- Fix 5: add 02-07 detail section before ## 关联 ---
xdzwy = xdzwy.replace(
    '### 《十月》主编季亚娅访谈（方涛，2026-02-06，观点归作者）\n- 提及AI对写作者的冲击引发热议、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野。\n- 季亚娅认为文学杂志是小小的"肺"（呼吸与吐纳），2013年《十月》创刊35周年时接手系统梳理历年重要作品；2026年新主编上任，面临碎片化时代如何抵达更多读者、保持文学内在生命力等命题。\n- 杂志新主编群像对话（潮新闻·钱江晚报记者方涛）：反映传统文学阵地在新时代的转型焦虑与探索。\n\n## 关联',
    '''### 《十月》主编季亚娅访谈（方涛，2026-02-06，观点归作者）
- 提及AI对写作者的冲击引发热议、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野。
- 季亚娅认为文学杂志是小小的"肺"（呼吸与吐纳），2013年《十月》创刊35周年时接手系统梳理历年重要作品；2026年新主编上任，面临碎片化时代如何抵达更多读者、保持文学内在生命力等命题。
- 杂志新主编群像对话（潮新闻·钱江晚报记者方涛）：反映传统文学阵地在新时代的转型焦虑与探索。

### 宁夏西吉县木兰书院与农民作家群体（徐元锋，2026-02-07）
- 西吉县被中华文学基金会授予"文学之乡"称号，有 1600 多名写作者，其中 300 多名是地道农民；史静波返乡创办木兰书院，成为农民作家交流学习的"娘家"。
- 冬天供暖问题由西吉县政府现场办公解决：空气能设备+太阳能光伏板，使文学小院突破季节限制全年开课。
- 关键人物：西吉七中数学老师任建平负责"南麓文学社"；农民作家单小花（反对高价彩礼舞台剧）、李成山；马金莲（固原市文联副主席）参与"文学村BA"直播 25 场，农产品销售额 80 余万元；杨河村大学生马丽（母亲麻巧琴 49 岁写出第一首诗）与母亲、姐姐合作诗歌。
- 体现了新大众文艺在西北边地扎根乡土、持续生长的生动样态。

## 关联''',
    1
)
assert_count(xdzwy, "宁夏西吉县木兰书院与农民作家群体", 1, "xdzwy detail updated")

# --- Fix 6: add 02-07 source entry (after 02-04 source) ---
xdzwy = xdzwy.replace(
    '- [以文学触摸生活的质地（柳冬妩）](http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html)＠ 2026-02-04',
    '''- [以文学触摸生活的质地（柳冬妩）](http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html)＠ 2026-02-04
- [雪原里，有个热腾腾的文学小院（徐元锋）](http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html)＠ 2026-02-07''',
    1
)
assert_count(xdzwy, "雪原里，有个热腾腾的文学小院", 2, "xdzwy src end updated")  # tl + src

write(os.path.join(WIKI, r"主题\新大众文艺.md"), xdzwy)
print("  fixed 主题/新大众文艺.md")

print("Phase 4: Updating index.md...")

wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")

idx = idx.replace(
    "### 统计数据\n- 知识页面总数：641\n- raw 原始文档总数：1379",
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}"
)
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
assert_count(idx, f"raw 原始文档总数：{raw_count}", 1, "idx raw count")

write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")

log_entry = f"""
## 2026-09-07 Ingest 02-07 批次
- 【Ingest】采集 2026-02-07 八关键词数据，新增 1 篇 raw，完成 ingest
- 新建 0 页
- 更新 1 页：主题/新大众文艺（+宁夏西吉县木兰书院农民作家群体徐元锋报道/史静波返乡创办1600+写作者300+农民/文学之乡称号/文学村BA直播助农80万/马金莲南麓文学社；同时修复前序脚本导致的 related 行重复和 pubdate 缺失问题）
- 轻处理 0 篇
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""

lg = lg.replace("- 用递归计数写入真实统计：wiki=641 / raw=1379", "- 用递归计数写入真实统计：wiki=641 / raw=1379" + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-07 ingest completed. wiki={wiki_count}, raw={raw_count}")