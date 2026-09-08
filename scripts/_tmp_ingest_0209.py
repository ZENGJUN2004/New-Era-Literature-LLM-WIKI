# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-09 batch (17 raw files, 2 updates, 15 light)."""
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
dlwg = read(os.path.join(WIKI, r"主题\大文学观.md"))

assert_count(xdzwy, 'pubdate: 2026-02-07', 1, "xdzwy fm")
assert_count(xdzwy, "宁夏西吉县木兰书院与农民作家群体", 1, "xdzwy tl")
assert_count(xdzwy, "- [雪原里，有个热腾腾的文学小院（徐元锋）](http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html)＠ 2026-02-07", 1, "xdzwy src end")

assert_count(dlwg, 'pubdate: 2026-02-06', 1, "dlwg fm")
assert_count(dlwg, '- [以"文学+"为抓手，打造中国文学多元发展新图景（罗建森）](http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html)＠ 2026-02-06', 1, "dlwg src end")

idx = read(INDEX)
assert_count(idx, "- 知识页面总数：641", 1, "idx stat")

lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1381"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")
print("Phase 2: No new pages.")
print("Phase 3: Updating existing pages...")

# ====== 主题/新大众文艺.md ======
xdzwy = xdzwy.replace(
    '    pubdate: 2026-02-07\nrelated:',
    '''    pubdate: 2026-02-07
  - id: raw/markdown/2026/2026-02-09_1000040662667.md
    url: http://www.chinawriter.com.cn/n1/2026/0209/c403993-40662667.html
    pubdate: 2026-02-09
related:''',
    1
)
assert_count(xdzwy, 'pubdate: 2026-02-09', 1, "xdzwy fm updated")

xdzwy = xdzwy.replace(
    '- **2026-02-07**：徐元锋发表《雪原里，有个热腾腾的文学小院》，报道宁夏西吉县木兰书院农民作家剧本创作培训班——史静波返乡创办，1600多名写作者、300多名农民作者；马金莲负责南麓文学社；农民作家单小花、李成山参与舞台剧；西吉县获中华文学基金会"文学之乡"称号；"文学村BA"直播25场助农销售80多万元（详见下节）。\n\n### 北京皮村新工人文学小组',
    '''- **2026-02-07**：徐元锋发表《雪原里，有个热腾腾的文学小院》，报道宁夏西吉县木兰书院农民作家剧本创作培训班——史静波返乡创办，1600多名写作者、300多名农民作者；马金莲负责南麓文学社；农民作家单小花、李成山参与舞台剧；西吉县获中华文学基金会"文学之乡"称号；"文学村BA"直播25场助农销售80多万元（详见下节）。
- **2026-02-09**：中国作协联合抖音发起2026春节长图文征集大赛，以"好好过年养好老己"为主题，鼓励大众记录新春百态。活动由《文艺报》社、《人民文学》杂志社、中国作家网承办，旨在为大众搭建表达真情的书写平台，让新大众文艺在烟火年味中绽放光彩（详见下节）。''',
    1
)
assert_count(xdzwy, "2026-02-09", 3, "xdzwy tl+detail+src updated")

xdzwy = xdzwy.replace(
    '### 宁夏西吉县木兰书院与农民作家群体（徐元锋，2026-02-07）',
    '''### 抖音×中国作协春节长图文征集大赛（2026-02-09）
- 中国作协联合抖音发起2026春节长图文征集大赛，以"好好过年养好老己"为主题，邀请大众用文字记录新春百态。活动由《文艺报》社、《人民文学》杂志社、中国作家网承办。
- 抖音长图文功能支持8000字创作、30张配图及背景音乐，莫言、余华等知名作家已尝试此体裁。2025年素人写作案例（如"56岁阿姨祝薪雁重新养自己"、张河清怀念大学室友）持续出圈，"用作文回顾我的2025"播放量超6亿，引发"白描文学""老辈子文学"等讨论。
- 长图文作为新大众文艺的新载体，降低了创作门槛，让素人写作在短视频时代找到新的表达空间。

### 宁夏西吉县木兰书院与农民作家群体（徐元锋，2026-02-07）''',
    1
)
assert_count(xdzwy, "抖音×中国作协春节长图文征集大赛", 1, "xdzwy detail updated")

xdzwy = xdzwy.replace(
    '- [雪原里，有个热腾腾的文学小院（徐元锋）](http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html)＠ 2026-02-07',
    '''- [雪原里，有个热腾腾的文学小院（徐元锋）](http://www.chinawriter.com.cn/n1/2026/0207/c403994-40661415.html)＠ 2026-02-07
- [中国作协联合抖音，喊你来写春节作文啦！（刘越）](http://www.chinawriter.com.cn/n1/2026/0209/c403993-40662667.html)＠ 2026-02-09''',
    1
)
assert_count(xdzwy, "中国作协联合抖音，喊你来写春节作文啦", 1, "xdzwy src end updated")

write(os.path.join(WIKI, r"主题\新大众文艺.md"), xdzwy)
print("  updated 主题/新大众文艺.md")

# ====== 主题/大文学观.md ======
dlwg = dlwg.replace(
    '    pubdate: 2026-02-06\nrelated:',
    '''    pubdate: 2026-02-06
  - id: raw/markdown/2026/2026-02-09_1000040662127.md
    url: http://www.chinawriter.com.cn/n1/2026/0209/c403994-40662127.html
    pubdate: 2026-02-09
  - id: raw/markdown/2026/2026-02-09_1000040662436.md
    url: http://www.chinawriter.com.cn/n1/2026/0209/c403994-40662436.html
    pubdate: 2026-02-09
related:''',
    1
)
assert_count(dlwg, 'pubdate: 2026-02-09', 2, "dlwg fm updated")

dlwg = dlwg.replace(
    '- ⬜ 人物/韩少功.md（待建）；⬜ 人物/林森.md（待建）；⬜ 主题/新时代现实主义.md（待建）\n\n## 来源',
    '''- ⬜ 人物/韩少功.md（待建）；⬜ 人物/林森.md（待建）；⬜ 主题/新时代现实主义.md（待建）

### 《红岩》杂志焕新与"大文学观"（赵欣 刘名扬，2026-02-09，观点归作者）
- 重庆唯一公开出版发行的文学期刊《红岩》创刊75周年，2月5日在重庆文学会客厅举办新刊发布会。
- 主题定为"'大文学观'与文学刊物的'破圈'路径"，多位作者代表与会探讨文学杂志如何在大文学观视野下实现创新表达。
- 《红岩》推出"中国诗集""国际诗集""中国文存""中国叙事"等栏目，被誉为"中国西部的精神岩石"。

### 关仁山《太阳照在滹沱河上》的大文学观阐释（肖煜，2026-02-09，观点归作者）
- 河北省著名作家关仁山在2026北京图书订货会访谈中指出，《太阳照在滹沱河上》"以更广阔的大文学观，为土地与人这一永恒主题注入了全新的时代内涵"。
- 小说描绘滹沱河畔小村庄从1982年至今40余年发展历程，深耕燕赵沃土、紧扣时代脉搏。

## 来源''',
    1
)
assert_count(dlwg, "《红岩》杂志焕新与\"大文学观\"", 1, "dlwg detail updated")
assert_count(dlwg, "关仁山《太阳照在滹沱河上》", 1, "dlwg detail 2 updated")

dlwg = dlwg.replace(
    '- [以"文学+"为抓手，打造中国文学多元发展新图景（罗建森）](http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html)＠ 2026-02-06',
    '''- [以"文学+"为抓手，打造中国文学多元发展新图景（罗建森）](http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html)＠ 2026-02-06
- [开启新征程，《红岩》文学杂志新年焕新（赵欣 刘名扬）](http://www.chinawriter.com.cn/n1/2026/0209/c403994-40662127.html)＠ 2026-02-09
- [河北文学精品创作竞绽芳华（肖煜）](http://www.chinawriter.com.cn/n1/2026/0209/c403994-40662436.html)＠ 2026-02-09''',
    1
)
assert_count(dlwg, "《红岩》文学杂志新年焕新", 1, "dlwg src end updated")
assert_count(dlwg, "河北文学精品创作竞绽芳华", 1, "dlwg src end 2 updated")

write(os.path.join(WIKI, r"主题\大文学观.md"), dlwg)
print("  updated 主题/大文学观.md")

print("Phase 4: Updating index.md...")
wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")
idx = idx.replace(
    "### 统计数据\n- 知识页面总数：641\n- raw 原始文档总数：1381",
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}"
)
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")
log_entry = f"""
## 2026-09-07 Ingest 02-09 批次
- 【Ingest】采集 2026-02-09 八关键词数据，新增 17 篇 raw，完成 ingest
- 新建 0 页
- 更新 2 页：主题/新大众文艺（+中国作协×抖音春节长图文征集大赛/素人写作/白描文学老辈子文学/8000字长图文约稿超6亿播放量）；主题/大文学观（+《红岩》杂志75周年焕新发布会大文学观与破圈路径/关仁山《太阳照在滹沱河上》大文学观阐释）
- 轻处理 15 篇：访谈1（戴来夏商写作是心里的恋人）、机构通知1（中国作协联合抖音春节征文）、文学评论3（评徐祯霞牛背梁上望长安散文集凌先有/西海固文学如何讲故事赵炳鑫/俄国文学为什么大于文学张晓东）、新作品5（边疆文学2026年第2期张永权/北京文学2026年第1期马拉诗歌文猛土生土长/广西文学2026年第1期林湛青苔）、文讯活动4（河北文学院第十七届签约作家推进活动/刘亮程当选新疆文联主席/长篇报告文学迎春花开首发深圳/红岩杂志新刊发布会）、儿童文学1（新时代儿童文学主题创作探微）、期刊目录1（边疆文学2026年第2期）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-09 ingest completed. wiki={wiki_count}, raw={raw_count}")