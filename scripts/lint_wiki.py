#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
lint_wiki.py — Wiki 纠错与整理（对应 AGENTS.md 4.3 Lint 动作）
==============================================================
检查项：
1. 死链接      —— 页面正文与 frontmatter related 中指向不存在 .md 的链接
2. 孤儿页面    —— 没有任何其他 wiki 页面链入的页面
3. 索引不一致  —— index.md 缺条目 / ✅ 条目指向不存在的文件
4. frontmatter —— 缺 type/name/sources/pubdate 等必填字段
5. 时间线缺失  —— 页面缺「时间线」小节
6. raw 引用    —— sources 指向的 raw/json 文件不存在；未被任何页面引用的 raw 文档
7. 日志一致性  —— log.md 中引用已不存在的 wiki 文件

用法：
  python scripts/lint_wiki.py           # 仅报告
  python scripts/lint_wiki.py --fix     # 自动修复安全项：index 补条目 + 更新统计 + 记 log
"""

import argparse
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BJT = timezone(timedelta(hours=8))
ROOT = Path(__file__).parent.parent.resolve()
WIKI_DIR = ROOT / "wiki"
INDEX_PATH = ROOT / "index.md"
LOG_PATH = ROOT / "log.md"
RAW_JSON_DIR = ROOT / "raw" / "json"

TYPE_SECTIONS = ["人物", "作品", "主题", "概念", "流派", "机构", "事件", "时间线"]


# ─────────────────────────────────────────────
# 基础解析
# ─────────────────────────────────────────────

def parse_frontmatter(content: str) -> tuple[dict, str]:
    """返回 (frontmatter 字典, 去掉 frontmatter 的正文)。"""
    fm = {}
    body = content
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if m:
        body = content[m.end():]
        current_key = None
        for line in m.group(1).splitlines():
            stripped = line.strip()
            if re.match(r"^-\s", stripped) and current_key:
                item = stripped[2:].strip()
                val = fm.get(current_key)
                if isinstance(val, list):
                    val.append(item)
                elif val in ("", [], None):
                    fm[current_key] = [item]
                else:  # 原为字符串值，转为列表
                    fm[current_key] = [str(val), item]
            elif current_key and line[:1] in (" ", "\t") and isinstance(fm.get(current_key), list) and fm[current_key]:
                # 列表项的缩进续行（如 sources 下的 url:/pubdate:）
                fm[current_key][-1] += " " + stripped
            elif ":" in line:
                key, val = line.split(":", 1)
                current_key = key.strip()
                fm[current_key] = val.strip()
    return fm, body


def list_wiki_pages() -> dict[Path, dict]:
    """扫描 wiki/ 全部页面，返回 {path: {fm, body}}。"""
    pages = {}
    for fp in sorted(WIKI_DIR.rglob("*.md")):
        content = fp.read_text(encoding="utf-8")
        fm, body = parse_frontmatter(content)
        pages[fp] = {"fm": fm, "body": body}
    return pages


def resolve_link(page_path: Path, link: str) -> Path | None:
    """把页面内的相对链接解析为绝对路径；无法解析返回 None。"""
    link = link.split("#")[0].strip()
    if not link:
        return None
    try:
        return (page_path.parent / link).resolve()
    except OSError:
        return None


def extract_md_links(page_path: Path, fm: dict, body: str) -> list[str]:
    """提取页面所有指向 .md 的链接（正文 markdown 链接 + frontmatter related），去重保序。"""
    links: list[str] = []
    for m in re.finditer(r"\[[^\]]*\]\(([^)]+\.md)\)", body):
        links.append(m.group(1))
    # frontmatter related: 可能是 markdown 链接列表，也可能是裸路径
    related = fm.get("related")
    if isinstance(related, str):
        related = [related]
    for item in related or []:
        text = str(item)
        found = re.findall(r"\]\(([^)]+\.md)\)", text) or \
            re.findall(r"[\w./\\·（\-]+\.md", text)
        links.extend(found)
    # 去重保序
    seen = set()
    return [l for l in links if not (l in seen or seen.add(l))]


# ─────────────────────────────────────────────
# 各项检查
# ─────────────────────────────────────────────

def check_dead_links(pages: dict) -> list[str]:
    issues = []
    for path, info in pages.items():
        for link in extract_md_links(path, info["fm"], info["body"]):
            target = resolve_link(path, link)
            if target is None or not target.exists():
                rel = path.relative_to(ROOT)
                issues.append(f"死链接：{rel} → {link}")
    return issues


def check_orphans(pages: dict) -> list[str]:
    """统计每个页面被其他 wiki 页面（不含 index.md）链入的次数。"""
    inbound: dict[Path, int] = {p: 0 for p in pages}
    for path, info in pages.items():
        seen = set()
        for link in extract_md_links(path, info["fm"], info["body"]):
            target = resolve_link(path, link)
            if target in inbound and target != path and target not in seen:
                inbound[target] += 1
                seen.add(target)
    return [
        f"孤儿页面（无链入）：{p.relative_to(ROOT)}"
        for p, n in inbound.items() if n == 0
    ]


def check_index(pages: dict) -> tuple[list[str], list[Path], list[str]]:
    """返回 (问题列表, 缺失条目的页面, 失效的✅条目名)。"""
    issues = []
    index_links: dict[Path, str] = {}
    missing_entries: list[Path] = []
    stale_entries: list[str] = []

    if not INDEX_PATH.exists():
        return ["index.md 不存在"], missing_entries, stale_entries

    content = INDEX_PATH.read_text(encoding="utf-8")
    for m in re.finditer(r"([✅⬜])\s*(.+?)（\[([^\]]+)\]\(([^)]+)\)）", content):
        status, name, _, link = m.groups()
        # index 条目链接为 wiki/ 下相对路径（如 人物/洪子诚.md）
        target = (WIKI_DIR / link).resolve()
        index_links[target] = name
        if status == "✅" and not target.exists():
            stale_entries.append(name)
            issues.append(f"索引失效✅条目：{name}（文件不存在）")

    for p in pages:
        if p not in index_links:
            missing_entries.append(p)
            issues.append(f"索引缺条目：{p.relative_to(ROOT)}")

    return issues, missing_entries, stale_entries


def check_frontmatter(pages: dict) -> list[str]:
    issues = []
    required = ["type", "name", "sources"]
    for path, info in pages.items():
        fm = info["fm"]
        rel = path.relative_to(ROOT)
        for key in required:
            if key not in fm or fm[key] in ("", [], None):
                issues.append(f"frontmatter 缺 {key}：{rel}")
        # sources 条目应有 id/url/pubdate
        sources = fm.get("sources") or []
        if isinstance(sources, str):
            sources = [sources]
        for s in sources:
            if "pubdate" not in str(s):
                issues.append(f"sources 缺 pubdate：{rel}")
                break
    return issues


def check_timeline(pages: dict) -> list[str]:
    return [
        f"缺「时间线」小节：{p.relative_to(ROOT)}"
        for p, info in pages.items()
        if "## 时间线" not in info["body"] and "时间线" not in (info["fm"].get("tags") or [])
    ]


def check_raw_refs(pages: dict) -> tuple[list[str], list[str]]:
    """返回 (sources 指向不存在 raw 文件的问题, 未被引用的 raw 文档列表)。"""
    issues = []
    referenced: set[str] = set()
    for path, info in pages.items():
        sources = info["fm"].get("sources") or []
        if isinstance(sources, str):
            sources = [sources]
        for s in sources:
            m = re.search(r"raw/json/([\w.\-]+\.json)", str(s))
            if m:
                referenced.add(m.group(1))
                if not (RAW_JSON_DIR / m.group(1)).exists():
                    issues.append(f"raw 引用不存在：{path.relative_to(ROOT)} → raw/json/{m.group(1)}")
    raw_files = {f.name for f in RAW_JSON_DIR.glob("*.json")}
    uningested = sorted(raw_files - referenced)
    return issues, uningested


def check_log(pages: dict) -> list[str]:
    if not LOG_PATH.exists():
        return []
    issues = []
    known = {p.resolve() for p in pages}
    for m in re.finditer(r"wiki[/\\]+[\w./\\·（）()\-]+\.md", LOG_PATH.read_text(encoding="utf-8")):
        p = (ROOT / m.group(0)).resolve()
        if p not in known:
            issues.append(f"log.md 引用已不存在的文件：{m.group(0)}")
    return issues


def check_index_stats(pages: dict) -> list[str]:
    issues = []
    if not INDEX_PATH.exists():
        return issues
    content = INDEX_PATH.read_text(encoding="utf-8")
    n_pages = len(pages)
    n_raw = len(list(RAW_JSON_DIR.glob("*.json")))
    m1 = re.search(r"知识页面总数：(\d+)", content)
    m2 = re.search(r"raw 原始文档总数：(\d+)", content)
    if m1 and int(m1.group(1)) != n_pages:
        issues.append(f"统计过期：知识页面总数 {m1.group(1)} → 应为 {n_pages}")
    if m2 and int(m2.group(1)) != n_raw:
        issues.append(f"统计过期：raw 原始文档总数 {m2.group(1)} → 应为 {n_raw}")
    return issues


# ─────────────────────────────────────────────
# 自动修复（--fix）
# ─────────────────────────────────────────────

def fix_index(missing_entries: list[Path]) -> list[str]:
    """向 index.md 补充缺失条目，返回修复描述。"""
    if not missing_entries or not INDEX_PATH.exists():
        return []
    content = INDEX_PATH.read_text(encoding="utf-8")
    fixes = []
    for p in missing_entries:
        name = p.stem
        type_ = p.parent.name
        section = type_ if type_ in TYPE_SECTIONS else None
        if section is None:
            continue
        entry = f"✅ {name}（[{type_}/{name}.md]({type_}/{name}.md)）"
        if entry in content:
            continue
        # 定位小节：## 事件 ... 到下一个 ## 或 ---
        pattern = rf"(## {re.escape(section)}\n)"
        m = re.search(pattern, content)
        if not m:
            continue
        insert_at = m.end()
        content = content[:insert_at] + entry + "\n" + content[insert_at:]
        fixes.append(f"index.md 补条目：{type_}/{name}")
    # 更新统计
    n_pages = len(list(WIKI_DIR.rglob("*.md")))
    n_raw = len(list(RAW_JSON_DIR.glob("*.json")))
    today = datetime.now(BJT).strftime("%Y-%m-%d")
    content = re.sub(r"知识页面总数：\d+", f"知识页面总数：{n_pages}", content)
    content = re.sub(r"raw 原始文档总数：\d+", f"raw 原始文档总数：{n_raw}", content)
    content = re.sub(r"最后更新：\d{4}-\d{2}-\d{2}", f"最后更新：{today}", content)
    INDEX_PATH.write_text(content, encoding="utf-8")
    return fixes


def append_log(lint_summary: list[str], fixes: list[str]):
    now = datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {now}", "- 【Lint】运行 lint_wiki.py"]
    for s in lint_summary:
        lines.append(f"  - {s}")
    for f in fixes:
        lines.append(f"- 【Fix】{f}")
    with open(LOG_PATH, "a", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


# ─────────────────────────────────────────────
# 主流程
# ─────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(description="Wiki Lint 检查（AGENTS.md 4.3）")
    ap.add_argument("--fix", action="store_true", help="自动修复安全项（index 条目/统计）")
    args = ap.parse_args()

    pages = list_wiki_pages()
    print(f"扫描 wiki/：{len(pages)} 个页面\n")

    dead = check_dead_links(pages)
    orphans = check_orphans(pages)
    idx_issues, missing_entries, stale = check_index(pages)
    fm_issues = check_frontmatter(pages)
    tl_issues = check_timeline(pages)
    raw_issues, uningested = check_raw_refs(pages)
    log_issues = check_log(pages)
    stat_issues = check_index_stats(pages)

    def report(title: str, items: list[str]):
        print(f"== {title}：{len(items)} 项")
        for it in items:
            print(f"  - {it}")
        print()

    report("死链接", dead)
    report("孤儿页面", orphans)
    report("索引不一致", idx_issues)
    report("frontmatter 问题", fm_issues)
    report("时间线缺失", tl_issues)
    report("raw 引用问题", raw_issues)
    report("log 一致性", log_issues)
    report("统计过期", stat_issues)
    print(f"== 未被任何页面引用的 raw 文档：{len(uningested)} 篇")
    for u in uningested:
        print(f"  - {u}")

    total = len(dead) + len(orphans) + len(idx_issues) + len(fm_issues) + \
        len(tl_issues) + len(raw_issues) + len(log_issues) + len(stat_issues)
    print(f"\n共 {total} 项待处理。")

    fixes = []
    if args.fix:
        fixes = fix_index(missing_entries)
        summary = [
            f"死链接 {len(dead)}、孤儿 {len(orphans)}、索引 {len(idx_issues)}、"
            f"frontmatter {len(fm_issues)}、时间线缺失 {len(tl_issues)}、"
            f"raw 引用 {len(raw_issues)}、log {len(log_issues)}、统计过期 {len(stat_issues)}",
            f"未引用 raw 文档 {len(uningested)} 篇",
        ]
        append_log(summary, fixes)
        print(f"--fix 已执行：{len(fixes)} 项修复，已记入 log.md")
    elif total > 0:
        print("提示：加 --fix 可自动修复索引条目与统计数字（其余需人工/LLM 处理）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
