# -*- coding: utf-8 -*-
"""Ingest script for 2026-02-09 batch - dlwg补跑版 (xdzwy already updated)."""
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

dlwg = read(os.path.join(WIKI, r"主题\大文学观.md"))

assert_count(dlwg, 'pubdate: 2026-02-06', 1, "dlwg fm")
assert_count(dlwg, '- [以"文学+"为抓手，打造中国文学多元发展新图景（罗建森）](http://www.chinawriter.com.cn/n1/2026/0206/c403993-40660649.html)＠ 2026-02-06', 1, "dlwg src end")
assert_count(dlwg, 'pubdate: 2026-02-09', 0, "dlwg no 0209 yet")
assert_count(dlwg, "《红岩》杂志焕新", 0, "dlwg no redrock yet")
assert_count(dlwg, "- ⬜ 人物/韩少功.md（待建）", 1, "dlwg anchor")

idx = read(INDEX)
assert_count(idx, "- 知识页面总数：641", 1, "idx stat")

lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1381"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")
print("Phase 2: No new pages.")
print("Phase 3: Updating existing pages...")

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
log_entry = """
## 2026-09-07 Ingest 02-09 批次（补跑 dlwg）
- 【Ingest】补跑 2026-02-09 批次中 dlwg 未写入的更新
- 更新 1 页：主题/大文学观（+《红岩》杂志75周年焕新发布会大文学观与破圈路径/关仁山《太阳照在滹沱河上》大文学观阐释）
- xdzwy 已在本次会话首次运行中更新，此处仅补跑 dlwg
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
""".format(wiki_count=wiki_count, raw_count=raw_count)
lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-09 dlwg补跑 completed. wiki={wiki_count}, raw={raw_count}")
