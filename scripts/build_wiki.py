#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_wiki.py — 自动 Ingest：从 raw markdown 提取实体，生成/更新 wiki 页面
========================================================================
功能：
1. 读取 tasks/ingest_YYYYMMDD.md 任务清单（或由 --file 指定）
2. 对每篇 raw 文档，提取关键实体（人物、作品、事件、主题、机构、概念）
3. 判断是新建还是更新 wiki 页面
4. 生成符合 AGENTS.md 规范的 Markdown 页面
5. 更新 index.md 和 log.md

注意：实体识别采用启发式规则（关键词+模式匹配），对于复杂内容
建议由 LLM 人工 ingest；本脚本适用于结构清晰的新闻/报告类文档。
"""

import argparse
import os
import re
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

BJT = timezone(timedelta(hours=8))

# ─────────────────────────────────────────────
# 常量
# ─────────────────────────────────────────────
ROOT = Path(__file__).parent.parent.resolve()
RAW_MD_DIR = ROOT / "raw" / "markdown"
WIKI_DIR = ROOT / "wiki"
INDEX_PATH = ROOT / "index.md"
LOG_PATH = ROOT / "log.md"
TASKS_DIR = ROOT / "tasks"

# 实体类型目录映射
TYPE_DIR_MAP = {
    "人物": "人物",
    "作品": "作品",
    "事件": "事件",
    "主题": "主题",
    "概念": "概念",
    "流派": "流派",
    "机构": "机构",
}

# 常见人物姓名模式（姓氏+双字名，或单字名）
CHINESE_NAME_PATTERNS = [
    r"([一-龥]{2,3})[：:\s]+(?:表示|说|认为|指出|介绍|回忆|提到|强调)",
    r"(?:作家|作者|评论家|学者|教授|主编|主编|院长|主席|副主席|副院长|党组书记|专职副主席|副主席|主编)[：:\s]*([一-龥]{2,3})",
    r"([一-龥]{2,3})[，,、；;]?\s*(?:是|中国|当代|著名|当代著名)",
    r"(?:的)?([一-龥]{2,3})(?:的)?(?:报告|讲话|发言|文章|访谈|散文)",
]

# 常见作品名模式
WORK_PATTERN = r"《([^》]+)》"

# 常见机构名模式
ORG_PATTERNS = [
    r"([中国][协会学会联合会杂志报社出版社刊社网台]+(?:研究院|中心|文学院|文学馆|作家协会|文联|作协|出版社|杂志|期刊|大学|学院|研究所|编辑部))",
    r"([省市区县][省市区县市州盟]+(?:作协|文学院|文学馆|文联|出版社|杂志))",
    r"(鲁迅文学院|花城文学院|潮州文学院|广东文学院|天津文学院|黑龙江文学院|浙江文学院|湖南毛泽东文学院|重庆文学院|广西文学院|上海文学院)",
]

# 常见事件名模式（更精确）
EVENT_PATTERNS = [
    # 特定会议/奖项
    r"([第代][一二三四五六七八九十百零零〇\d]+届?[鲁迅文学奖|作代会|文代会|全国代表大会|理事会议|峰会|论坛|年会|评奖|表彰]+(?:\（扩大\）)?)+",
    # 包含日期和地点的会议描述
    r"([一二两][0-9]{3}[年/-][0-9]{1,2}[月/-][0-9]{1,2}[日]+(?:至[一二两][0-9]{1,2}[月/-][0-9]{1,2}[日]+)?(?:在[^\n，,。；;]+)?(?:会议|大会|召开|举行))",
    # 全国性会议/活动
    r"((?:全国|中国|国际)[^，,。；;\n]{2,30}?(?:大会|会议|论坛|活动|盛典|评奖|表彰大会|年会))",
]

# 常见主题/概念词
THEME_KEYWORDS = [
    "新时代现实主义", "社会主义文学", "文学制度", "新大众文艺", "大文学观",
    "农村能人", "工业题材", "天津题材", "非虚构写作", "网络文学",
    "人工智能人文学", "数字人文", "双百方针", "百花齐放", "百家争鸣",
    "社会主义新人", "文艺为人民服务", "文艺为社会主义服务", "文学讲习所",
    "公式化概念化", "自然主义", "文学副刊", "文学创作", "文学队伍",
    "少数民族文学", "儿童文学", "戏剧文学", "电影文学",
]

# ─────────────────────────────────────────────
# 工具函数
# ─────────────────────────────────────────────

def parse_frontmatter(content: str) -> dict:
    """解析 Markdown frontmatter，返回字典。"""
    fm = {}
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                key, val = line.split(":", 1)
                fm[key.strip()] = val.strip()
    return fm


def extract_pubdate(fm: dict) -> str:
    """从 frontmatter 提取发布日期（YYYY-MM-DD）。"""
    pd = fm.get("pubdate", "")
    m = re.search(r"(\d{4}-\d{2}-\d{2})", pd)
    return m.group(1) if m else datetime.now(BJT).strftime("%Y-%m-%d")


def extract_url(fm: dict) -> str:
    return fm.get("url", "")


def extract_author(fm: dict) -> str:
    return fm.get("author", "")


def strip_html_tags(text: str) -> str:
    """去除 HTML 标签，保留文本。"""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&\w+;", "", text)
    return text.strip()


def get_body_content(content: str) -> str:
    """提取 frontmatter 之后的正文。"""
    m = re.match(r"^---\s*\n.*?\n---\s*\n", content, re.DOTALL)
    if m:
        return strip_html_tags(content[m.end():])
    return strip_html_tags(content)


def find_existing_wiki_page(name: str, type_: str) -> Path | None:
    """查找是否已有同名 wiki 页面。"""
    dir_name = TYPE_DIR_MAP.get(type_, type_)
    candidate = WIKI_DIR / dir_name / f"{name}.md"
    if candidate.exists():
        return candidate
    # 尝试别名匹配
    for subdir in WIKI_DIR.iterdir():
        if not subdir.is_dir():
            continue
        for fp in subdir.glob("*.md"):
            existing = fp.read_text(encoding="utf-8")
            m = re.search(r"^name:\s*(.+)$", existing, re.MULTILINE)
            if m and m.group(1).strip() == name:
                return fp
    return None


def extract_timeline(body: str, pubdate: str) -> list:
    """从正文提取时间线条目（YYYY-MM-DD 格式的日期事件）。"""
    timeline = []
    # 匹配 YYYY-MM-DD 或 YYYY年M月D日 格式
    date_patterns = [
        r"(\d{4}-\d{2}-\d{2})",
        r"(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?",
    ]
    seen_dates = set()
    lines = body.split("\n")
    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue
        for pat in date_patterns:
            dm = re.search(pat, line)
            if dm:
                if pat == date_patterns[0]:
                    date_str = dm.group(1)
                else:
                    date_str = f"{dm.group(1)}-{dm.group(2).zfill(2)}-{dm.group(3).zfill(2)}"
                if date_str not in seen_dates:
                    # 取日期后的内容作为事件描述，截断过长文本
                    event = line[line.find(date_str) + len(date_str):].strip("：:，, ")
                    # 截断到第一个句号/分号/换行，最多100字
                    event = re.split(r"[。；;\n]", event)[0].strip()[:100]
                    # 跳过纯数字/时间戳等无意义描述
                    if event and len(event) > 2 and not re.fullmatch(r"[\d:：.\s/年月日时]+", event):
                        timeline.append((date_str, event))
                        seen_dates.add(date_str)
                break
    # 附加文档发布日期（如果没有已提取）
    if pubdate and pubdate not in seen_dates:
        timeline.append((pubdate, "文档发布"))
    timeline.sort(key=lambda x: x[0])
    return timeline


def detect_entities(body: str, fm: dict) -> dict:
    """从正文和元数据中检测实体，返回 {type: [names]}。"""
    entities = {"人物": set(), "作品": set(), "事件": set(), "主题": set(), "机构": set(), "概念": set()}
    
    # 提取作品名
    for m in re.finditer(WORK_PATTERN, body):
        entities["作品"].add(m.group(1))

    # 提取机构名
    for pat in ORG_PATTERNS:
        for m in re.finditer(pat, body):
            entities["机构"].add(m.group(1))

    # 提取事件名
    for pat in EVENT_PATTERNS:
        for m in re.finditer(pat, body):
            entities["事件"].add(m.group(1))

    # 提取主题/概念关键词
    for kw in THEME_KEYWORDS:
        if kw in body:
            entities["主题"].add(kw)
            # 如果是双字词且不太常见，也可能是概念
            if len(kw) <= 6 and "文学" in kw or "主义" in kw or "观" in kw:
                entities["概念"].add(kw)

    # 提取人物（通过上下文推断）
    for pat in CHINESE_NAME_PATTERNS:
        for m in re.finditer(pat, body):
            name = m.group(1)
            if len(name) >= 2 and len(name) <= 4:
                entities["人物"].add(name)

    # 从 frontmatter 的 author 提取
    author = extract_author(fm)
    if author:
        entities["人物"].add(author)

    # 从 column 字段提取机构/刊物
    column = fm.get("column", "")
    if column:
        for part in column.split("#"):
            part = part.strip()
            if part and len(part) > 1:
                entities["机构"].add(part)

    # 过滤：过短的名字、常见标点等
    stop_words = {
        "中国", "人民", "国家", "文学", "小说", "报告", "关于", "以及", "可以",
        "一些", "一直", "不再", "成为", "仍然", "能够", "主要", "重点", "首先",
        "其次", "再次", "最后", "同时", "特别", "通过", "进行", "开展", "加强",
        "促进", "推动", "坚持", "围绕", "基于", "结合", "按照", "根据", "对于",
        "为了", "由于", "因此", "从而", "所以", "但是", "然而", "并且", "或者",
        "这些", "这个", "那个", "这样", "那样", "什么", "如何", "怎样", "为什么",
        "可以", "可能", "已经", "仍然", "继续", "充分", "全面", "深刻", "重要",
        "一定", "非常", "更加", "较多", "较大", "较好", "不少", "所有", "全部",
        "以上", "以下", "两者", "一方面", "另一方面", "其中", "此外", "另外",
    }
    # 人名额外过滤：必须是2-3字且以常见姓氏开头
    surnames = set("赵钱孙李周吴郑王冯陈褚卫蒋沈韩杨朱秦尤许何吕施张孔曹严华金魏陶姜戚谢邹喻柏水窦章云苏潘葛奚范彭鲁韦昌马苗凤花方俞任袁柳酆鲍史唐费廉岑薛雷贺倪汤滕殷罗毕郝邬安常乐于时傅皮卞齐康伍余元卜顾孟平黄和穆萧尹姚邵湛汪祁毛禹狄米贝明臧计伏成戴谈宋茅庞熊纪舒屈项祝董梁杜阮蓝闵席季麻强贾路娄危江童颜郭梅盛林刁钟徐邱骆高夏蔡田樊胡凌霍万柯卢莫房缪干解应宗丁宣贲邓郁单杭洪包诸左石崔吉钮龚程嵇邢滑裴陆荣翁荀羊於惠甄曲家封芮羿储靳汲邴糜松井段富巫乌焦巴牧隗山谷车侯宓蓬全郗班仰秋仲伊官宁栾曾武沙居盒向古易慎戈廖庾终暨居衡步都耿满弘匡国文寇广禄阙东欧殳沃利蔚越夔隆师巩厍聂晁勾敖融冷訾辛阚那简饶空曾毋沙乜养利戎祖武符刘景詹束龙叶幸司韶郜黎蓟薄印宿白怀蒲邰从鄂索咸籍赖卓蔺屠蒙池乔阴胥能苍双闻莘党翟谭贡劳逄姬申扶堵冉宰郦雍郤璩桑桂濮牛寿通边扈燕冀郏浦尚农温别庄晏柴瞿阎充慕连茹习宦艾鱼容向古")
    # 事件名噪声过滤：排除含介词/连接词的不完整片段
    event_noise_patterns = [r"[向在从对关于]", r"《", r"\(", r"\)", r"（", r"）"]
    filtered_entities = {}
    for t, names in entities.items():
        if t == "人物":
            filtered = {
                n for n in names
                if len(n) in (2, 3)
                and n[0] in surnames
                and n not in stop_words
                and not re.search(r"[的在了和在与从向到过着会说表示认为指出介绍回忆提到强调]", n)
            }
        elif t in ("主题", "概念"):
            filtered = {n for n in names if len(n) >= 3 and n not in stop_words}
        elif t == "机构":
            filtered = {
                n for n in names
                if len(n) >= 3
                and n not in stop_words
                and not re.match(r"^\d+$", n)
                and not n.startswith("《")
                and not n.startswith("[")
                and "#" not in n
            }
        elif t == "事件":
            # 事件过滤：排除含噪声模式的片段，优先保留短而精确的名称
            filtered = {
                n for n in names
                if len(n) >= 4
                and n not in stop_words
                and not any(re.search(p, n) for p in event_noise_patterns)
                and not n.startswith("「")
                and not n.startswith("『")
            }
        else:
            filtered = {n for n in names if len(n) >= 2 and n not in stop_words}
        if filtered:
            filtered_entities[t] = sorted(filtered)
    return filtered_entities


def build_wiki_page(
    fm: dict,
    body: str,
    entities: dict,
    pubdate: str,
    url: str,
    author: str,
    title: str,
    doc_id: str = "unknown",
) -> tuple:
    """
    根据提取的实体构建 wiki 页面内容。
    返回 (type, name, content) 三元组，type 和 name 用于确定存储路径。
    如果检测到多个实体，优先以「事件」或「人物」为主实体。
    """
    # 优先顺序：事件 > 人物 > 机构 > 主题 > 概念 > 作品
    # 事件/人物候选按「正文出现频次降序 → 名称长度升序」排序，优先取最常见、最精确的名称
    def by_freq(t: str):
        names = sorted(entities.get(t, []))
        return sorted(names, key=lambda n: (-body.count(n), len(n)))

    primary = None
    if entities.get("事件"):
        primary = ("事件", by_freq("事件")[0])
    elif entities.get("人物"):
        primary = ("人物", by_freq("人物")[0])
    elif entities.get("机构"):
        primary = ("机构", by_freq("机构")[0])
    elif entities.get("主题"):
        primary = ("主题", entities["主题"][0])
    elif entities.get("概念"):
        primary = ("概念", entities["概念"][0])
    elif entities.get("作品"):
        primary = ("作品", entities["作品"][0])

    if not primary:
        # 退而求其次：用标题作为概念
        primary = ("概念", title)

    type_, name = primary
    timeline = extract_timeline(body, pubdate)

    # 构建概述
    overview_lines = []
    if type_ == "人物":
        overview_lines.append(f"{name}，{" | ".join(entities.get('人物', [])[:2]) if entities.get('人物') and entities['人物'][0] != name else ''}。")
    elif type_ == "事件":
        overview_lines.append(f"{name}，{pubdate} 发生于相关文献中的事件。")
    elif type_ == "机构":
        overview_lines.append(f"{name}，{pubdate} 相关报道涉及的机构。")
    else:
        overview_lines.append(f"{name}，{pubdate} 相关文献中提及的主题/概念。")
    
    # 从摘要中提取更多信息
    summary_m = re.search(r"内容提要[：:]\s*([^\n]+)", body)
    if summary_m:
        overview_lines.insert(0, summary_m.group(1).strip())

    overview = "\n".join(overview_lines)[:200]

    # 关联页面：只链接已存在的页面；未建实体按 AGENTS.md 记为待建（⬜），避免死链
    related_paths = []   # frontmatter related（相对本页面的路径）
    related_body = []    # 正文「相关实体」行
    seen_links = set()
    for t, names in entities.items():
        if t == type_:
            continue
        dir_name = TYPE_DIR_MAP.get(t, t)
        for n in names:
            key = (t, n)
            if key in seen_links:
                continue
            seen_links.add(key)
            target = WIKI_DIR / dir_name / f"{n}.md"
            if target.exists():
                rel_path = f"../{dir_name}/{n}.md"
                related_paths.append(rel_path)
                related_body.append(f"- [{n}]({rel_path})（{t}）")
            else:
                related_body.append(f"- ⬜ {n}（{t}，待建）")

    # 来源
    source_line = f"[{title}]({url})＠ {pubdate}" if url else f"{title}＠ {pubdate}"

    # 构建 tags
    all_tags = set()
    for t, names in entities.items():
        all_tags.update(names)
    tags = sorted(all_tags)[:10]

    today = datetime.now(BJT).strftime("%Y-%m-%d")

    # 时间线小节
    timeline_section = ""
    if timeline:
        lines = []
        for d, desc in timeline:
            lines.append(f"- **{d}**：{desc}")
        timeline_section = "\n" + "\n".join(lines) + "\n"

    content = f"""---
type: {type_}
name: {name}
aliases: []
created: {today}
updated: {today}
sources:
  - id: raw/json/{doc_id}.json
    url: {url}
    pubdate: {pubdate}
related: [{', '.join(related_paths)}]
tags: [{', '.join(tags)}]
---

# {name}

<!-- 概述：2-3 句说明本实体是什么 -->
{overview}

## 关键信息
- **类型**：{type_}
- **来源文档**：{title}
- **发布时间**：{pubdate}
- **作者**：{author or '未知'}

## 时间线{timeline_section}## 详细内容
（待 LLM ingest 后补充：依据原文提炼关键事实、观点、脉络，按 AGENTS.md 规范组织内容）

### 相关实体
"""
    content += "\n".join(related_body) + "\n"

    content += f"""
## 来源
- {source_line}
"""

    return type_, name, content


def update_index(entities: list):
    """在 index.md 中追加新建条目。entities 为 (type, name) 元组列表。"""
    if not INDEX_PATH.exists() or not entities:
        return
    content = INDEX_PATH.read_text(encoding="utf-8")
    updated = False
    for type_, name in entities:
        dir_name = TYPE_DIR_MAP.get(type_, type_)
        entry = f"✅ {name}（[{dir_name}/{name}.md]({dir_name}/{name}.md)）"
        if entry in content:
            continue
        # 匹配小节标题（兼容「## 机构 / 奖项」这类带后缀的标题）
        m = re.search(rf"## {re.escape(dir_name)}[^\n]*\n", content)
        if not m:
            print(f"  ⚠ index.md 无「{dir_name}」小节，跳过条目：{name}")
            continue
        # 插到小节标题后的条目区末尾（下一个空行/小节前），确保独立成行
        section_start = m.end()
        next_m = re.search(r"\n\s*\n|\n## |\n---", content[section_start:])
        insert_at = section_start + (next_m.start() if next_m else 0)
        prefix = "" if insert_at > 0 and content[insert_at - 1] == "\n" else "\n"
        content = content[:insert_at] + prefix + entry + "\n" + content[insert_at:]
        updated = True
    if updated:
        today = datetime.now(BJT).strftime("%Y-%m-%d")
        content = re.sub(r"最后更新：\d{4}-\d{2}-\d{2}", f"最后更新：{today}", content)
        INDEX_PATH.write_text(content, encoding="utf-8")
        print("  index.md 已更新")


def append_log(entries: list):
    """在 log.md 追加变动记录。entries 为 (action, type, name) 元组列表。"""
    today = datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
    lines = [f"\n## {today}"]
    for action, type_, name in entries:
        dir_name = TYPE_DIR_MAP.get(type_, type_)
        lines.append(f"- 【{action}】wiki/{dir_name}/{name}.md")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def load_task_list(task_file: Path | None = None) -> list:
    """从任务清单加载待 ingest 的文档列表。"""
    if task_file is None:
        # 找最新的任务清单
        if not TASKS_DIR.exists():
            return []
        files = sorted(TASKS_DIR.glob("ingest_*.md"), reverse=True)
        if not files:
            return []
        task_file = files[0]
    if not task_file.exists():
        return []
    docs = []
    content = task_file.read_text(encoding="utf-8")
    for m in re.finditer(r"\[\S+\.md\]\(([^)]+)\)", content):
        rel = m.group(1)
        # 路径可能是 ../raw/markdown/... 或 raw/markdown/...
        cleaned = rel.removeprefix("../")
        full = ROOT / cleaned
        if full.exists():
            docs.append(full)
    return docs


def process_single_doc(doc_path: Path) -> list:
    """处理单个 raw markdown 文档，生成 wiki 页面，返回 (action, type, name) 列表。"""
    content = doc_path.read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    body = get_body_content(content)
    pubdate = extract_pubdate(fm)
    url = extract_url(fm)
    author = extract_author(fm)
    title = fm.get("title", doc_path.stem)
    # raw 文档 id：取文件名末段的数字（如 2026-08-13_1000040779012 → 1000040779012）
    doc_id = doc_path.stem.split("_")[-1]

    entities = detect_entities(body, fm)
    if not any(entities.values()):
        print(f"  ⚠ 未检测到实体，跳过：{doc_path.name}")
        return []

    print(f"  检测到实体：{entities}")
    type_, name, page_content = build_wiki_page(
        fm, body, entities, pubdate, url, author, title, doc_id
    )
    
    dir_name = TYPE_DIR_MAP.get(type_, type_)
    out_path = WIKI_DIR / dir_name / f"{name}.md"
    
    # 判断新建还是更新
    if out_path.exists():
        # 追加 sources 而不是覆盖
        existing = out_path.read_text(encoding="utf-8")
        # 在 sources 块追加新来源
        src_pattern = r"(sources:\n(?:\s*-\s*id:.*?\n)*)"
        new_source = f"  - id: raw/json/{doc_id}.json\n    url: {url}\n    pubdate: {pubdate}\n"
        m = re.search(src_pattern, existing)
        if m:
            new_content = existing[:m.end()] + new_source + existing[m.end():]
        else:
            # 在 frontmatter 末尾追加
            fm_end = re.search(r"\n---\n", existing)
            if fm_end:
                insert = existing[:fm_end.end()] + new_source + existing[fm_end.end():]
                new_content = insert
            else:
                new_content = existing + "\n\n" + new_source
        out_path.write_text(new_content, encoding="utf-8")
        print(f"  📝 更新：{out_path}")
        return [("Update", type_, name)]
    else:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(page_content, encoding="utf-8")
        print(f"  ✨ 新建：{out_path}")
        return [("Create", type_, name)]


def main():
    ap = argparse.ArgumentParser(description="自动 Ingest：从 raw 生成 wiki 页面")
    ap.add_argument("--task", type=Path, help="指定任务清单文件（默认取最新）")
    ap.add_argument("--doc", type=Path, action="append",
                    help="指定单个 raw markdown 文件（可多次指定），跳过任务清单")
    ap.add_argument("--dry-run", action="store_true", help="仅打印不写入")
    args = ap.parse_args()

    if args.doc:
        docs = [d.resolve() for d in args.doc if d.exists()]
    else:
        docs = load_task_list(args.task)
    if not docs:
        print("没有待 ingest 的文档，退出。")
        return 0

    print(f"发现 {len(docs)} 篇待 ingest 文档\n")
    all_entries = []

    for doc_path in docs:
        print(f"处理：{doc_path.name}")
        if args.dry_run:
            # 仅检测实体，不写入
            content = doc_path.read_text(encoding="utf-8")
            fm = parse_frontmatter(content)
            body = get_body_content(content)
            entities = detect_entities(body, fm)
            print(f"  实体：{entities}")
        else:
            entries = process_single_doc(doc_path)
            all_entries.extend(entries)

    if not args.dry_run and all_entries:
        update_index([(t, n) for _, t, n in all_entries])
        append_log(all_entries)
        print(f"\n完成：{len(all_entries)} 个页面操作，已更新 index.md 和 log.md")
    elif args.dry_run:
        print("\n[Dry-run] 以上为检测结果，无实际写入。去掉 --dry-run 执行实际操作。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
