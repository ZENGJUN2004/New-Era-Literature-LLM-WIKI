# -*- coding: utf-8 -*-
"""Log-only ingest for 2026-02-08 batch (1 raw file, all light)."""
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
assert_count(idx, "- 知识页面总数：641", 1, "idx stat")

lg = read(LOG)
lg_anchor = "- 用递归计数写入真实统计：wiki=641 / raw=1380"
assert_count(lg, lg_anchor, 1, "log anchor")

print("Phase 1: All anchors verified.")
print("Phase 2-3: No new pages, no page updates.")

print("Phase 4: Updating index.md...")
wiki_count = count_md(WIKI)
raw_count = count_md(r"d:\zjun\新时代文学LLMWIKI\raw\markdown")
idx = idx.replace(lg_anchor,
    f"### 统计数据\n- 知识页面总数：{wiki_count}\n- raw 原始文档总数：{raw_count}\n- 最后更新：2026-09-07", 1)
assert_count(idx, f"知识页面总数：{wiki_count}", 1, "idx wiki count")
write(INDEX, idx)
print(f"  index updated (wiki={wiki_count}, raw={raw_count})")

print("Phase 5: Updating log.md...")
log_entry = f"""
## 2026-09-07 Ingest 02-08 批次
- 【Ingest】采集 2026-02-08 八关键词数据，新增 1 篇 raw，完成 ingest
- 新建 0 页
- 更新 0 页
- 轻处理 1 篇：综述1（青年写作的可持续性李杨主持座谈王炳中仁宝金春平等谈经验同质化碎片化问题）
- 用递归计数写入真实统计：wiki={wiki_count} / raw={raw_count}
"""
lg = lg.replace(lg_anchor, lg_anchor + log_entry, 1)
write(LOG, lg)
print("  log updated")
print(f"DONE: 02-08 ingest completed. wiki={wiki_count}, raw={raw_count}")