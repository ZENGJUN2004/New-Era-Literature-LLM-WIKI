# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-04 batch (16 raw files, 1 update, 15 light)."""
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
xdzwy_fm = '    pubdate: 2026-01-26\nrelated: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]\ntags: [新大众文艺, 工人文学, 乡村振兴, 清溪村]'
assert_count(xdzwy, xdzwy_fm, 1, "xdzwy fm")
xdzwy_tl = '- **2026-01-29**：姚苏平（江苏第二师范学院）发表《新大众文艺之江苏儿童文学新实践》——新大众文艺打破传统儿童文学'
assert_count(xdzwy, xdzwy_tl, 1, "xdzwy tl")
xdzwy_src_end = '- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02'
assert_count(xdzwy, xdzwy_src_end, 1, "xdzwy src end")
xdzwy_detail_end = '- **政策坐标**：「十五五」规划纲要将「繁荣互联网条件下新大众文艺」纳入国家文化发展战略部署。'
assert_count(xdzwy, xdzwy_detail_end, 1, "xdzwy detail end")

# --- index.md anchors ---
idx = read(INDEX)
idx_stat = """### 统计数据
- 知识页面总数：641
- raw 原始文档总数：1321"""
assert_count(idx, idx_stat, 1, "idx stat")

# --- log.md anchor ---
lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1321"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")

print("Phase 2: No new pages.")

print("Phase 3: Updating existing pages...")

# ====== 主题/新大众文艺.md ======
# 3a. Append source to frontmatter
new_src_fm = """  - id: raw/markdown/2026/2026-02-04_1000040659386.md
    url: http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html
    pubdate: 2026-02-04
related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]"""

old_src_fm = 'related: [../人物/范雨素.md, ../人物/袁凌.md, ../人物/施洪丽.md, ../人物/小海.md, ../人物/李文丽.md, ../人物/麦家.md, ../人物/王玉珍.md, ../人物/瑛子.md]'
xdzwy = xdzwy.replace(old_src_fm, new_src_fm, 1)
assert_count(xdzwy, 'pubdate: 2026-02-04', 1, "xdzwy fm updated")

# 3b. Append timeline entry
new_tl_entry = """- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地》，评花城出版社"新大众文艺丛书"六部东莞新大众写作者作品集（瑛子/章新宏/易翔/曾为民/沈汉炎/温雄珍），称东莞为"打工文学"策源地之一，六位作者均为"新莞人"，以不同行业视角书写城市化进程中的平民史诗。

## 关联"""

old_tl_end = """## 关联"""
xdzwy = xdzwy.replace(new_tl_entry, new_tl_entry, 0)  # no-op check
# Use actual insertion: after last timeline entry, before "## 详细内容"
xdzwy = xdzwy.replace(
    '（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n\n## 详细内容',
    '（39 岁起在「屋顶上的樱园」写作工坊习作，详见下节）。\n- **2026-02-04**：柳冬妩发表《以文学触摸生活的质地》，评花城出版社"新大众文艺丛书"六部东莞新大众写作者作品集（瑛子/章新宏/易翔/曾为民/沈汉炎/温雄珍），称东莞为"打工文学"策源地之一，六位作者均为"新莞人"，以不同行业视角书写城市化进程中的平民史诗。\n\n## 详细内容',
    1
)
assert_count(xdzwy, "- **2026-02-04**：柳冬妩发表", 1, "xdzwy tl updated")

# 3c. Append detail section
new_detail_section = """

### 新大众文艺丛书·东莞六位新大众写作者（柳冬妩，2026-02-04，观点归作者）
- 花城出版社"新大众文艺丛书"收入东莞六位新大众写作者的六部诗文集：瑛子（清洁女工）《擦亮高楼》、章新宏（体育老师）《从江右到岭南》、易翔（讲台诗人）《东莞时间》、曾为民（石材厂工人）《赶石头的人》、沈汉炎（渔村诗人）《有些光不会消失》、温雄珍（烧烤店服务员）《在炭火上安居》。
- 东莞是"打工文学"的策源地之一，六位作者均为"新莞人"，从全国各地来到东莞，以不同职业视角书写城市化进程。
- 诗文特点：瑛子以细腻笔触记录清洁女工生活；曾为民以手机写作、短章为主，聚焦石材厂日常与石头意象；温雄珍在烟火气中写诗，以微尘般的光芒呈现底层经验；沈汉炎以老屋/故乡意象完成对传统乡愁书写的超越；易翔以东莞地理为叙事载体，记录从仓皇到从容的人生变迁；章新宏以情感皈依立场记录与东莞的缘分。

## 关联"""

old_detail_end = '- **政策坐标**：「十五五」规划纲要将「繁荣互联网条件下新大众文艺」纳入国家文化发展战略部署。\n\n## 关联'
xdzwy = xdzwy.replace(old_detail_end, new_detail_section.strip() + "\n\n## 关联", 1)
assert_count(xdzwy, "新大众文艺丛书·东莞六位新大众写作者", 1, "xdzwy detail updated")

# 3d. Append source entry at end
new_src_line = '- [以文学触摸生活的质地（柳冬妩）](http://www.chinawriter.com.cn/n1/2026/0204/c404030-40659386.html)＠ 2026-02-04'
xdzwy = xdzwy.replace(
    '- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02',
    '- [从田间诗作到外卖文学 山东两会代表委员热议素人创作新潮（王采怡 孙婷婷）](http://www.chinawriter.com.cn/n1/2026/0202/c403994-40657905.html)＠ 2026-02-02\n' + new_src_line,
    1
)
assert_count(xdzwy, "以文学触摸生活的质地", 2, "xdzwy src end updated")  # timeline + src

write(os.path.join(WIKI, r"主题\新大众文艺.md"), xdzwy)
print("  updated 主题/新大众文艺.md")

print("Phase 4: Updating index.md...")

wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")

idx = idx.replace(
    "### 统计数据\n- 知识页面总数：641\n- raw 原始文档总数：1321",
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}"
)
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
assert_count(idx, f"raw 原始文档总数：{raw_count}", 1, "idx raw count")

# Also update timestamp
idx = idx.replace("- 最后更新：2026-09-07", "- 最后更新：2026-09-07", 1)

write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")

log_entry = f"""
## 2026-09-07 Ingest 02-04 批次
- 【Ingest】采集 2026-02-04 八关键词数据，新增 16 篇 raw，完成 ingest
- 新建 0 页
- 更新 1 页：主题/新大众文艺（+花城出版社"新大众文艺丛书"柳冬妩评论/东莞六位新大众写作者：瑛子清洁女工章新宏体育老师易翔讲台诗人曾为民石材厂工人沈汉炎渔村诗人温雄珍烧烤店服务员/打工文学策源地/新莞人城市化进程书写）
- 轻处理 15 篇：访谈1（李浩然小说月报问答/孤独写作）、机构通知1（2026年度中国作协重点作品扶持征集通知/五大主题专项）、新书发布1（王忆《乘风或岛屿》南京发布）、海外交流1（中国青年作家参加第57届开罗国际书展）、报刊作品4（陈福民现代君子上海文学/安琪阿右旗组诗天津文学/周一度量衡北京文学万众写作栏目/上海文学2026年第1期）、文讯活动4（仁怀作协年会/南京摩天书店/2025收获文学榜揭晓苏童好天气吴真暗斗/中国现代文学馆2025捐赠答谢会馆藏100万件）、国际文学2（陈方中俄文学对话/土耳其中国文学读者俱乐部纪红建石一枫）、文学史1（茅盾诞辰130周年回忆录我走过的道路）、网络文学动态1（影响力榜征集/温州交流中心/四川申报/上海网络作协妇联）+作品关键词1篇（已有文档跳过）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""

lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print(f"  log updated")
print(f"DONE: 02-04 ingest completed. wiki={wiki_count}, raw={raw_count}")
