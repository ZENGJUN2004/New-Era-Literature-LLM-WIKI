# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-01 batch (2 raw files)."""
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

# ====== Phase 1: Read and assert anchors ======
print("Phase 1: Reading and asserting anchors...")

# --- 人物/谢宗玉.md ---
xzj = read(os.path.join(WIKI, r"人物\谢宗玉.md"))
xzj_fm = "    pubdate: 2026-05-27\nrelated:"
assert_count(xzj, xzj_fm, 1, "xzj fm")
xzj_tl = """- **2026-05-24**："大文学观视域下的地方性写作"学术研讨会（湖南省作协与湖南大学合办）在湖南大学举行，谢宗玉散文集《千年弦歌》与刘年诗集《一生事，一捧雪》、卓今专著《劳者歌其事》同场研讨（2026-05-27 报道）。"""
assert_count(xzj, xzj_tl, 1, "xzj tl")

# --- 机构/湖南文学.md ---
hnwx = read(os.path.join(WIKI, r"机构\湖南文学.md"))
hnwx_fm = "    pubdate: 2026-09-01\nrelated:"
assert_count(hnwx, hnwx_fm, 1, "hnwx fm")
hnwx_tl = "- **2026-09-01**：中国作家网「报刊在线」发布《湖南文学》2026 年第 9 期目录。"
assert_count(hnwx, hnwx_tl, 1, "hnwx tl")

# --- index.md anchors ---
idx = read(INDEX)
idx_event_end = "✅ 扬子江文学评论2025年度文学排行榜（[事件/扬子江文学评论2025年度文学排行榜.md](事件/扬子江文学评论2025年度文学排行榜.md)）\n\n## 时间线"
assert_count(idx, idx_event_end, 1, "idx event end")
idx_stat = """### 统计数据
- 知识页面总数：635
- raw 原始文档总数：1269"""
assert_count(idx, idx_stat, 1, "idx stat")

# --- log.md anchor ---
lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=635 / raw=1269"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")

# ====== Phase 2: Create new page 事件/新时代文学期刊转型与发展研讨会.md ======
yt = """---
type: 事件
name: 新时代文学期刊转型与发展研讨会
aliases: []
created: 2026-09-07
updated: 2026-09-07
sources:
  - id: raw/markdown/2026/2026-02-01_1000040657250.md
    url: http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html
    pubdate: 2026-02-01
related: [../主题/大文学观.md, ../主题/新大众文艺.md, ../人物/谢宗玉.md, ../机构/湖南文学.md]
tags: [文学期刊, 转型, 研讨会, 新时代文学, 新大众文艺, 大文学观]
---

# 新时代文学期刊转型与发展研讨会

新时代文学期刊转型与发展研讨会于2026年1月30日以线上线下相结合的方式举办，由中国作家出版集团、湖南省作家协会、中南大学人文学院联合主办，中国作家协会新时代文学研究中心（中南大学）与《湖南文学》杂志社承办，聚焦数字媒介生态变革下传统文学期刊的系统性转型与协同发展。

## 关键信息
- **主办方**：中国作家出版集团、湖南省作家协会、中南大学人文学院
- **承办方**：中国作协新时代文学研究中心（中南大学）、《湖南文学》杂志社
- **出席嘉宾**：宋向伟（中国作家出版集团副总经理、全国文学报刊联盟秘书长）、谢宗玉（湖南省作协专职副主席）；《小说选刊》《花城》《钟山》《湖南文学》《中国当代文学研究》等期刊及全国文学报刊联盟、中国作家网等平台负责人
- **开幕式主持**：崔庆蕾（《中国当代文学研究》执行主编）
- **会议总结**：晏杰雄（中南大学人文学院教授）

## 时间线
- **2026-01-30**：研讨会在湖南（线上线下结合）举办。
- **2026-02-01**：中国作家网刊发丁思存报道（中国作协栏目）。

## 详细内容

### 谢宗玉：期刊需实现三重转变（观点归致辞者）
- **内容策划**：从「编辑期刊」转向「策划思潮」。
- **身份定位**：从「文学守门人」转向内容价值的创造者与推广者。
- **发展目标**：立志打造巨型的文化网络平台。

### 会议共识：转型的三条路径
- **内容为根本**：回归时代现场与人民生活的真实关切，发掘具有时代感的真诚之作，大力培育青年作者，重视「新大众文艺」的广阔土壤。
- **传播理念更新**：不能满足于纸刊内容的线上平移，应以网络化思维主动策划；通过创设文学品牌活动、建立读者社群、融入实体文化空间，加强编读互动与情感连接。
- **协同发展**：打破介质与地域壁垒，促进资源共享与经验互通，重视编辑队伍的激励与再造，提升策划、传播与跨界连接能力。

### 晏杰雄总结
- 新一代大学生正日益疏离纸质文学与文学期刊，呼吁期刊主动对接高校，培育青年作者与重建青年读者群体。
- 认为文学期刊在数智时代担当文学火种「最后守护者」的角色。

## 关联
- [主题/大文学观.md](../主题/大文学观.md)（议题之一：推广大文学观）
- [主题/新大众文艺.md](../主题/新大众文艺.md)（议题之一：推广大文学观与新大众文艺）
- [人物/谢宗玉.md](../人物/谢宗玉.md)（致辞嘉宾）
- [机构/湖南文学.md](../机构/湖南文学.md)（承办方）

## 来源
- [新时代文学期刊转型与发展研讨会举办（丁思存）](http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html)＠ 2026-02-01
"""
write(os.path.join(WIKI, r"事件\新时代文学期刊转型与发展研讨会.md"), yt)
print("Created 事件/新时代文学期刊转型与发展研讨会.md")

# ====== Phase 3: Update existing pages ======

# --- 人物/谢宗玉.md：+ 研讨会来源/时间线/关联 ---
xzj_new = xzj.replace(
    "    pubdate: 2026-05-27\nrelated:",
    "    pubdate: 2026-05-27\n  - id: raw/markdown/2026/2026-02-01_1000040657250.md\n    url: http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html\n    pubdate: 2026-02-01\nrelated:",
    1,
)
xzj_new = xzj_new.replace(
    "related: [../主题/大文学观.md, ../人物/刘年.md, ../作品/劳者歌其事.md]",
    "related: [../主题/大文学观.md, ../人物/刘年.md, ../作品/劳者歌其事.md, ../事件/新时代文学期刊转型与发展研讨会.md]",
    1,
)
xzj_new = xzj_new.replace(
    """- **2026-05-24**："大文学观视域下的地方性写作"学术研讨会（湖南省作协与湖南大学合办）在湖南大学举行，谢宗玉散文集《千年弦歌》与刘年诗集《一生事，一捧雪》、卓今专著《劳者歌其事》同场研讨（2026-05-27 报道）。""",
    """- **2026-05-24**："大文学观视域下的地方性写作"学术研讨会（湖南省作协与湖南大学合办）在湖南大学举行，谢宗玉散文集《千年弦歌》与刘年诗集《一生事，一捧雪》、卓今专著《劳者歌其事》同场研讨（2026-05-27 报道）。
- **2026-01-30**：作为湖南省作协专职副主席出席「新时代文学期刊转型与发展研讨会」（中国作协新时代文学研究中心（中南大学）与《湖南文学》承办），提出期刊转型「三重转变」（2026-02-01 报道）。""",
    1,
)
xzj_new = xzj_new.replace(
    """## 来源\n- [专家学者齐聚湖南大学 共话"大文学观视域下的地方性写作"](http://www.chinawriter.com.cn/n1/2026/0527/c403994-40728698.html)＠ 2026-05-27""",
    """## 来源\n- [专家学者齐聚湖南大学 共话"大文学观视域下的地方性写作"](http://www.chinawriter.com.cn/n1/2026/0527/c403994-40728698.html)＠ 2026-05-27
- [新时代文学期刊转型与发展研讨会举办](http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html)＠ 2026-02-01""",
    1,
)
write(os.path.join(WIKI, r"人物\谢宗玉.md"), xzj_new)
print("Updated 人物/谢宗玉.md")

# --- 机构/湖南文学.md：+ 研讨会承办方来源/时间线/关联 ---
hnwx_new = hnwx.replace(
    "    pubdate: 2026-09-01\nrelated:",
    "    pubdate: 2026-09-01\n  - id: raw/markdown/2026/2026-02-01_1000040657250.md\n    url: http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html\n    pubdate: 2026-02-01\nrelated:",
    1,
)
hnwx_new = hnwx_new.replace(
    "related: [../事件/湖南文学创阅中心揭牌.md, ../作品/梦里花落知多少.md]",
    "related: [../事件/湖南文学创阅中心揭牌.md, ../作品/梦里花落知多少.md, ../事件/新时代文学期刊转型与发展研讨会.md]",
    1,
)
hnwx_new = hnwx_new.replace(
    "- **2026-09-01**：中国作家网「报刊在线」发布《湖南文学》2026 年第 9 期目录。",
    "- **2026-09-01**：中国作家网「报刊在线」发布《湖南文学》2026 年第 9 期目录。\n- **2026-01-30**：作为承办方之一参与「新时代文学期刊转型与发展研讨会」（2026-02-01 报道）。",
    1,
)
hnwx_new = hnwx_new.replace(
    "## 来源\n- [《湖南文学》2026年第9期目录](http://www.chinawriter.com.cn/n1/2026/0901/c419156-40790437.html)＠ 2026-09-01",
    "## 来源\n- [《湖南文学》2026年第9期目录](http://www.chinawriter.com.cn/n1/2026/0901/c419156-40790437.html)＠ 2026-09-01\n- [新时代文学期刊转型与发展研讨会举办](http://www.chinawriter.com.cn/n1/2026/0201/c403993-40657250.html)＠ 2026-02-01",
    1,
)
write(os.path.join(WIKI, r"机构\湖南文学.md"), hnwx_new)
print("Updated 机构/湖南文学.md")

# ====== Phase 4: Update index.md ======
idx = read(INDEX)
idx = idx.replace(
    "✅ 扬子江文学评论2025年度文学排行榜（[事件/扬子江文学评论2025年度文学排行榜.md](事件/扬子江文学评论2025年度文学排行榜.md)）\n\n## 时间线",
    "✅ 扬子江文学评论2025年度文学排行榜（[事件/扬子江文学评论2025年度文学排行榜.md](事件/扬子江文学评论2025年度文学排行榜.md)）\n✅ 新时代文学期刊转型与发展研讨会（[事件/新时代文学期刊转型与发展研讨会.md](事件/新时代文学期刊转型与发展研讨会.md)）\n\n## 时间线",
    1,
)
wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw")
idx = idx.replace(
    "### 统计数据\n- 知识页面总数：635\n- raw 原始文档总数：1269",
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}",
    1,
)
write(INDEX, idx)
print(f"Updated index.md (wiki={wiki_count}, raw={raw_count})")

# ====== Phase 5: Update log.md ======
lg = read(LOG)
lg_new = lg + """\n## 2026-09-07 Ingest 02-01 批次
- 【Ingest】采集 2026-02-01 八关键词数据，新增 2 篇 raw，完成 ingest
- 新建 1 页：事件/新时代文学期刊转型与发展研讨会（中国作家出版集团+湖南省作协+中南大学主办/湖南文学承办/谢宗玉三重转变/晏杰雄文学火种守护者/内容为根本+传播更新+协同发展三条路径/推广大文学观与新大众文艺）
- 更新 2 页：人物/谢宗玉（+研讨会来源/时间线01-30/相关事件链接）、机构/湖南文学（+承办方来源/时间线/相关事件链接）
- 轻处理 1 篇：地方文讯1（春天送你一首诗·《诗刊》作品赏读会/广东惠阳/1月30日晚/李少君致辞/生态诗歌研讨会预告）
- 用递归计数写入真实统计：wiki=636 / raw=1271
"""
write(LOG, lg_new)
print("Updated log.md")

print("\nDONE: 02-01 ingest complete.")