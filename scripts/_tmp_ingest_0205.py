# -*- coding: utf-8 -*-
"""Log-only ingest for 2026-02-05 batch (17 raw files, all light-processing)."""
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

idx = read(INDEX)
idx_stat = """### 统计数据
- 知识页面总数：641
- raw 原始文档总数：1337"""
assert_count(idx, idx_stat, 1, "idx stat")

lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1337"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")

print("Phase 2: No new pages.")
print("Phase 3: No page updates (all light).")

print("Phase 4: Updating index.md...")

wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")

idx = idx.replace(idx_stat, f"""### 统计数据
- 知识页面总数：{wiki_count}
- raw 原始文档总数：{raw_count}""")
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
assert_count(idx, f"raw 原始文档总数：{raw_count}", 1, "idx raw count")
write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")

log_entry = f"""
## 2026-09-07 Ingest 02-05 批次
- 【Ingest】采集 2026-02-05 八关键词数据，新增 17 篇 raw，完成 ingest
- 新建 0 页，更新 0 页（全部轻处理）
- 轻处理 17 篇：报刊作品8（黄亚洲用眼睛写作的诗人/芮晓峰诗边疆文学/李方毅找副业北京文学万众写作栏目素人写作/贾煜科幻洪极广西文学/包苞诗山西文学/安琪阿右旗组诗天津文学）、文讯活动4（知名作家看法院走进台州/宋世兵白河彼岸研讨会/颜丙环迁安出版/贾平凹朗读影像集岳色河声首发）、文学评论2（写出现实的另一面三篇青年作家小说简评黄尚恩/陈翠出海工业题材评论）、科幻动态1（马年科幻春晚5国13位女性作家）、影视艺术1（2026年度重温经典展播作品发布）、征文1（首届花开远方少年儿童文学节启事）、文史1（叶圣陶为何退出语文学习讲座）、期刊目录1（四川文学2026年第2期）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""

lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-05 ingest completed. wiki={wiki_count}, raw={raw_count}")