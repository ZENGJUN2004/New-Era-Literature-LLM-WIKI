# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-07 batch (1 raw file, 1 update)."""
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
xdzwy_fm = '    pubdate: 2026-02-06\nrelated: [../人物/范雨素.md'
assert_count(xdzwy, xdzwy_fm, 1, "xdzwy fm")
xdzwy_tl = '- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展'
assert_count(xdzwy, xdzwy_tl, 1, "xdzwy tl")
xdzwy_src_end = '＠ 2026-02-06'
assert_count(xdzwy, xdzwy_src_end, 1, "xdzwy src end")
idx = read(INDEX)
assert_count(idx, "知识页面总数：641", 1, "idx stat")
lg = read(LOG)
assert_count(lg, "- 用递归计数写入真实统计：wiki=641 / raw=1379", 1, "log anchor")

print("Phase 1: All anchors verified.")

print("Phase 2: No new pages.")

print("Phase 3: Updating existing pages...")

# 主题/新大众文艺.md
# 3a. frontmatter
new_src_fm = '''  - id: raw/markdown/2026/2026-02-07_1000040661415.md
    url: http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html
    pubdate: 2026-02-07
related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]'''

xdzwy = xdzwy.replace(
    '    pubdate: 2026-02-06\nrelated:',
    new_src_fm,
    1
)
assert_count(xdzwy, 'pubdate: 2026-02-07', 1, "xdzwy fm updated")

# 3b. timeline
xdzwy = xdzwy.replace(
    '- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野；季亚娅谈杂志是小小的"肺"，面向碎片化时代如何抵达更多读者、保持文学内在生命力等命题（详见下节）。\n\n## 详细内容',
    '''- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野；季亚娅谈杂志是小小的"肺"，面向碎片化时代如何抵达更多读者、保持文学内在生命力等命题（详见下节）。
- **2026-02-07**：徐元锋发表《雪原里，有个热腾腾的文学小院》，报道宁夏西吉县木兰书院农民作家剧本创作培训班——史静波返乡创办，1600多名写作者、300多名农民作者；马金莲任教于西吉七中并负责南麓文学社；农民作家单小花、李成山参与舞台剧演出；西吉县获中国作协中华文学基金会"文学之乡"称号；"文学村BA"直播25场助农销售80多万元（详见下节）。''',
    1
)
assert_count(xdzwy, "2026-02-07", 1, "xdzwy tl updated")

# 3c. detail section
xdzwy = xdzwy.replace(
    '（详见 [事件/人民文学人民阅卷活动.md](../事件/人民文学人民阅卷活动.md)）。（王瑛）个案——《擦亮高楼：清洁女工笔记》入选2025年中国作协重点作品扶持项目，2026年成为中国作协新会员（详见 [人物/瑛子.md](../人物/瑛子.md)）。（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n\n## 关联',
    '''（详见 [事件/人民文学人民阅卷活动.md](../事件/人民文学人民阅卷活动.md)）。（王瑛）个案——《擦亮高楼：清洁女工笔记》入选2025年中国作协重点作品扶持项目，2026年成为中国作协新会员（详见 [人物/瑛子.md](../人物/瑛子.md)）。（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。
- **宁夏西吉县木兰书院与农民作家群体**（徐元锋，2026-02-07）：西吉县被中华文学基金会授予"文学之乡"称号，有 1600 多名写作者，其中 300 多名是地道农民。史静波返乡创办木兰书院，成为农民作家交流学习的"娘家"，冬天冷时有空气能+太阳能取暖设备保障常年开课。西吉七中数学老师任建平负责"南麓文学社"；农民作家单小花、李成山活跃于舞台剧创作；马金莲参与"文学村BA"直播助农 25 场，销售额 80 余万元；杨河村大学生马丽母亲麻巧琴（49 岁）写出第一首诗，母女合作。新大众文艺在西北边地呈现扎根乡土、持续生长的生动样态。

## 关联''',
    1
)
assert_count(xdzwy, "宁夏西吉县木兰书院与农民作家群体", 1, "xdzwy detail updated")

# 3d. source entry
xdzwy = xdzwy.replace(
    '- [《十月》主编季亚娅：呼吸与吐纳，文学杂志是一个小小的"肺"（方涛）](http://www.chinawriter.com.cn/n1/2026/0206/c403994-40660526.html)＠ 2026-02-06',
    '''- [《十月》主编季亚娅：呼吸与吐纳，文学杂志是一个小小的"肺"（方涛）](http://www.chinawriter.com.cn/n1/2026/0206/c403994-40660526.html)＠ 2026-02-06
- [雪原里，有个热腾腾的文学小院（徐元锋）](http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html)＠ 2026-02-07''',
    1
)
assert_count(xdzwy, "雪原里，有个热腾腾的文学小院", 1, "xdzwy src end updated")

write(os.path.join(WIKI, r"主题\新大众文艺.md"), xdzwy)
print("  updated 主题/新大众文艺.md")

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
- 更新 1 页：主题/新大众文艺（+宁夏西吉县木兰书院农民作家群体徐元锋报道/史静波返乡创办1600+写作者300+农民/文学之乡称号/文学村BA直播助农80万/马金莲南麓文学社等）
- 轻处理 0 篇
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""

lg = lg.replace("- 用递归计数写入真实统计：wiki=641 / raw=1379", "- 用递归计数写入真实统计：wiki=641 / raw=1379" + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-07 ingest completed. wiki={wiki_count}, raw={raw_count}")