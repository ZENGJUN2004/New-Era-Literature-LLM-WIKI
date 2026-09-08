# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-06 batch (25 raw files, 1 update 新大众文艺, 1 update 大文学观, 23 light)."""
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

# --- 主题/新大众文艺.md anchors ---
xdzwy = read(os.path.join(WIKI, r"主题\新大众文艺.md"))
xdzwy_fm = '    pubdate: 2026-02-04\nrelated: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]'
assert_count(xdzwy, xdzwy_fm, 1, "xdzwy fm")
xdzwy_tl = '- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地》，评花城出版社'
assert_count(xdzwy, xdzwy_tl, 1, "xdzwy tl")
xdzwy_src_end = '- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02'
assert_count(xdzwy, xdzwy_src_end, 1, "xdzwy src end")
xdzwy_tl_last = '（详见 [事件/人民文学人民阅卷活动.md](../事件/人民文学人民阅卷活动.md)）。（王瑛）个案——《擦亮高楼：清洁女工笔记》入选2025年中国作协重点作品扶持项目，2026年成为中国作协新会员（详见 [人物/瑛子.md](../人物/瑛子.md)）。（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地'
assert_count(xdzwy, xdzwy_tl_last, 1, "xdzwy tl last entry")

# --- 主题/大文学观.md anchors ---
dlwg = read(os.path.join(WIKI, r"主题\大文学观.md"))
dlwg_src_end = '- [守边界，赴无限：在粤港澳大湾区文学周里读懂新时代"大文学"](http://www.chinawriter.com.cn/n1/2026/0901/c403994-40790435.html)＠ 2026-09-01'
assert_count(dlwg, dlwg_src_end, 1, "dlwg src end")
dlwg_fm = '    pubdate: 2026-02-02\nrelated: [新大众文艺.md, ../机构/中国当代文学研究.md, ../人物/谢宗玉.md, ../人物/刘年.md]'
assert_count(dlwg, dlwg_fm, 1, "dlwg fm")

# --- index.md anchors ---
idx = read(INDEX)
idx_stat = """### 统计数据
- 知识页面总数：641
- raw 原始文档总数：1354"""
assert_count(idx, idx_stat, 1, "idx stat")

# --- log.md anchor ---
lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1354"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")

print("Phase 2: No new pages.")

print("Phase 3: Updating existing pages...")

# ====== 主题/新大众文艺.md ======
# 3a. Append source to frontmatter
new_xdzwy_src_fm = '''  - id: raw/markdown/2026/2026-02-06_1000040661056.md
    url: http://www.chinawriter.com.cn/n1/2026/0206/c419006-40661056.html
    pubdate: 2026-02-06
related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]'''

xdzwy = xdzwy.replace(
    '    pubdate: 2026-02-04\nrelated:',
    new_xdzwy_src_fm,
    1
)
assert_count(xdzwy, 'pubdate: 2026-02-06', 1, "xdzwy fm updated")

# 3b. Append timeline entry (after Feb 4 entry)
xdzwy = xdzwy.replace(
    '（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地》，评花城出版社"新大众文艺丛书"六部东莞新大众写作者作品集（瑛子/章新宏/易翔/曾为民/沈汉炎/温雄珍），称东莞为"打工文学"策源地之一，六位作者均为"新莞人"，以不同行业视角书写城市化进程中的平民史诗。\n\n## 详细内容',
    '''（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地》，评花城出版社"新大众文艺丛书"六部东莞新大众写作者作品集（瑛子/章新宏/易翔/曾为民/沈汉炎/温雄珍），称东莞为"打工文学"策源地之一，六位作者均为"新莞人"，以不同行业视角书写城市化进程中的平民史诗。\n- **2026-02-06**：《十月》主编季亚娅访谈刊出——提及AI对写作者冲击、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野；季亚娅谈杂志是小小的"肺"，面向碎片化时代如何抵达更多读者（详见下节）。''',
    1
)
assert_count(xdzwy, "- **2026-02-06**：《十月》主编季亚娅访谈", 1, "xdzwy tl updated")

# 3c. Append detail section before ## 关联
xdzwy = xdzwy.replace(
    '\n## 关联\n\n## 关联\n- [事件/皮村新工人文学小组.md]',
    '''\n### 《十月》主编季亚娅访谈（方涛，2026-02-06，观点归作者）
- 提及AI对写作者的冲击引发热议、新大众文艺蓬勃发展、大文学观倡导更开放包容的文学视野。
- 季亚娅认为文学杂志是小小的"肺"（呼吸与吐纳），2013年《十月》创刊35周年时接手系统梳理历年重要作品；2026年新主编上任，面临碎片化时代如何抵达更多读者、保持文学内在生命力等命题。
- 杂志新主编群像对话（潮新闻·钱江晚报记者方涛）：反映传统文学阵地在新时代的转型焦虑与探索。

## 关联

## 关联
- [事件/皮村新工人文学小组.md]''',
    1
)
assert_count(xdzwy, "《十月》主编季亚娅访谈", 2, "xdzwy detail updated")  # tl + detail

# 3d. Append source entry
xdzwy = xdzwy.replace(
    '- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02',
    '''- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02
- [《十月》主编季亚娅：呼吸与吐纳，文学杂志是一个小小的"肺"（方涛）](http://www.chinawriter.com.cn/n1/2026/0206/c403994-40660526.html)＠ 2026-02-06''',
    1
)
assert_count(xdzwy, "《十月》主编季亚娅：呼吸与吐纳", 1, "xdzwy src end updated")

write(os.path.join(WIKI, r"主题\新大众文艺.md"), xdzwy)
print("  updated 主题/新大众文艺.md")

# ====== 主题/大文学观.md ======
dlwg = dlwg.replace(
    '    pubdate: 2026-02-02\nrelated:',
    '''    pubdate: 2026-02-02
  - id: raw/markdown/2026/2026-02-06_1000040660649.md
    url: http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html
    pubdate: 2026-02-06
related:''',
    1
)
assert_count(dlwg, 'pubdate: 2026-02-06', 1, "dlwg fm updated")

dlwg = dlwg.replace(
    '- [守边界，赴无限：在粤港澳大湾区文学周里读懂新时代"大文学"](http://www.chinawriter.com.cn/n1/2026/0901/c403994-40790435.html)＠ 2026-09-01',
    '''- [守边界，赴无限：在粤港澳大湾区文学周里读懂新时代"大文学"](http://www.chinawriter.com.cn/n1/2026/0901/c403994-40790435.html)＠ 2026-09-01
- [以"文学+"为抓手，打造中国文学多元发展新图景（罗建森）](http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html)＠ 2026-02-06''',
    1
)
assert_count(dlwg, '以"文学+"为抓手', 1, "dlwg src end updated")

write(os.path.join(WIKI, r"主题\大文学观.md"), dlwg)
print("  updated 主题/大文学观.md")

print("Phase 4: Updating index.md...")

wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")

idx = idx.replace(
    "### 统计数据\n- 知识页面总数：641\n- raw 原始文档总数：1354",
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}"
)
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
assert_count(idx, f"raw 原始文档总数：{raw_count}", 1, "idx raw count")

write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")

log_entry = f"""
## 2026-09-07 Ingest 02-06 批次
- 【Ingest】采集 2026-02-06 八关键词数据，新增 25 篇 raw，完成 ingest
- 新建 0 页
- 更新 2 页：主题/新大众文艺（+《十月》主编季亚娅访谈AI冲击/新大众文艺蓬勃发展/大文学观开放视野/杂志是小小的肺；+2026-02-06 条目）；主题/大文学观（+以文学为抓手打造多元发展新图景罗建森/十五五开局之年跨界共生）
- 轻处理 23 篇：报刊作品10（黄亚洲用眼睛写作的诗人/作品2026年第2期目录/李海洲重庆的饭局作家/赵小平那年征兵边疆文学/晨田洞潜广西文学/周荣池三十六湖秋水福建文学/王柳云快乐的狗尾草北京文学万众写作素人诗歌/刘家芳荒芜的风四川文学/山西文学包苞和一只青蛙谈一场盛大恋爱/安徽文学2026年第2期目录）、文讯活动8（萧红张莉随笔集活动张莉邱华栋/马伯庸刘勃历史小说播客对谈/舒晋瑜重回盛宴访谈录/知名作家看法院台州阎晶明刘醒龙等/宋世兵白河彼岸研讨会/颜丙环迁安出版泰安/贾平凹朗读影像集岳色河声首发/山东省作协黄河大集新春季/姜明八千年的凝视研讨会文学表达/余华文城旅社海盐/长篇报告文学穿越人间的象群研讨阎晶明陈启文/十月主编季亚娅访谈）、世界文坛2（宋莉华中国小说西传影响美学重构/刘建军拜占庭文学审美样态）、文学评论2（申霞艳曾莉雯历史化21世纪传记文学/韩步华牛建哲开裂人类演化简史文学图谱）、科幻动态1（马年科幻春晚5国13位女性作家奔跑的我）、文史1（林建法主编当代作家评论赵慧平回忆）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""

lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-06 ingest completed. wiki={wiki_count}, raw={raw_count}")