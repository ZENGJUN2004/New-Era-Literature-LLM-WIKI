#!/usr/bin/env python3
"""build_cockpit.py — 扫描 wiki/ 全部页面，提取元数据，生成自包含驾驶舱 HTML。

Usage:
    python scripts/build_cockpit.py [--wiki-dir wiki] [--out wiki/cockpit.html]

产出：
    wiki/cockpit.html — 暗色主题驾驶舱，内嵌 JSON 数据，Vanilla JS 交互。
"""

import re, os, sys, json, html as html_mod
from pathlib import Path
from collections import defaultdict

# ── CLI ──────────────────────────────────────────────────────────────
import argparse
ap = argparse.ArgumentParser()
ap.add_argument("--wiki-dir", default="wiki")
ap.add_argument("--out", default="wiki/cockpit.html")
args = ap.parse_args()

WIKI = Path(args.wiki_dir)
OUT = Path(args.out)

# ── 1. 扫描全部 wiki 页面，提取 YAML frontmatter ───────────────────
FM_RE = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
TYPE_RE  = re.compile(r"^type:\s*(.+)", re.M)
NAME_RE  = re.compile(r"^name:\s*(.+)", re.M)
TAGS_RE  = re.compile(r"^tags:\s*\[(.*?)\]", re.M | re.DOTALL)
SOURCES_RE = re.compile(r"^\s*- id:\s*", re.M)
PUBDATE_RE = re.compile(r"pubdate:\s*(\d{4}-\d{2})", re.M)
REL_RE   = re.compile(r"^related:\s*\[(.*?)\]", re.M | re.DOTALL)

pages = []  # list of dicts

for md_path in WIKI.rglob("*.md"):
    if md_path.name in ("index.md", "log.md", "cockpit.html"):
        continue
    rel = md_path.relative_to(WIKI)
    parts = rel.parts  # e.g. ("人物","莫言.md")
    if len(parts) != 2:
        continue
    cat = parts[0]
    if cat not in ("人物","作品","主题","概念","流派","机构","事件"):
        continue
    try:
        text = md_path.read_text(encoding="utf-8")
    except Exception:
        continue
    m = FM_RE.search(text)
    if not m:
        continue
    fm = m.group(1)
    tp = (TYPE_RE.search(fm) or TYPE_RE.search("type: " + cat)).group(1).strip()
    name_m = NAME_RE.search(fm)
    name = name_m.group(1).strip() if name_m else md_path.stem
    tags_m = TAGS_RE.search(fm)
    tags = [t.strip() for t in tags_m.group(1).split(",") if t.strip()] if tags_m else []
    src_count = len(SOURCES_RE.findall(fm))
    # 聚合 pubdate
    pdates = PUBDATE_RE.findall(fm)
    min_pd = min(pdates) if pdates else ""
    max_pd = max(pdates) if pdates else ""
    rel_m = REL_RE.search(fm)
    related = [r.strip().strip("'\"") for r in rel_m.group(1).split(",") if r.strip()] if rel_m else []
    # 提取 description (标题后第一个非空段落，跳过 ## 标题)
    desc = ""
    dm = re.search(r"^# [^\n]+\n\s*\n(.+?)(?=\n\s*\n|\Z)", text, re.M | re.S)
    if dm:
        _d = dm.group(1).strip()
        if not _d.startswith("##"):
            desc = _d[:300]
    # 提取时间线条目
    timeline = []
    tl_section = re.search(r"## 时间线\s*\n(.*?)(?=\n## |\Z)", text, re.S)
    if tl_section:
        for tl in re.findall(r"\*\*(\d{4}(?:-\d{2}(?:-\d{2})?)?)\*\*[：:]\s*(.+)", tl_section.group(1)):
            timeline.append({"date": tl[0], "text": tl[1].strip()[:200]})
    # 提取来源清单（url + pubdate 成对）
    sources_list = []
    for blk in re.findall(r"^\s*- id:.*?(?=\n\s*- id:|\Z)", fm, re.M | re.S):
        u = re.search(r"url:\s*(http\S+)", blk)
        if u:
            p = re.search(r"pubdate:\s*(\d{4}-\d{2}-\d{2})", blk)
            sources_list.append({"url": u.group(1).strip(), "pubdate": p.group(1) if p else ""})
    # 提取正文小节（二级/三级标题及其要点，用于综述生成）
    sections = []
    BODY_SKIP = {"关键信息", "时间线", "关联", "来源", "详细内容"}
    if m:
        body_part = text[m.end():]
        for sm in re.finditer(r"^#{2,3}\s+([^\n]+)\n(.*?)(?=^#{2,3}\s+|\Z)", body_part, re.M | re.S):
            st = sm.group(1).strip()
            if st in BODY_SKIP:
                continue
            sb = sm.group(2).strip()
            if sb:
                sections.append({"title": st, "body": sb[:400]})
    pages.append({
        "file": str(rel).replace("\\", "/"),
        "type": tp,
        "name": name,
        "cat": cat,
        "tags": tags,
        "src_count": src_count,
        "min_pd": min_pd,
        "max_pd": max_pd,
        "timeline": timeline,
        "desc": desc,
        "related": related,
        "sources_list": sources_list,
        "sections": sections,
    })

print(f"扫描到 {len(pages)} 个 wiki 页面")

# ── 1b. 构建关系图谱数据 ────────────────────────────────────────────
# 建立 file -> page 映射
file_map = {}
for p in pages:
    file_map[p["file"]] = p

# 节点和边
graph_nodes = {}  # key=file, value={id,name,cat,src_count,degree}
graph_edges = []  # [{source, target}]

CATEGORY_COLORS = {
    "人物": "#4ecdc4", "作品": "#ff6b6b", "主题": "#6c5ce7",
    "概念": "#e17055", "流派": "#a29bfe", "机构": "#00b894",
    "事件": "#ffd93d",
}

def resolve_related(src_file, rel_entries):
    """将 ../类别/名称.md 相对路径解析为目标 file 路径"""
    results = []
    for entry in rel_entries:
        entry = entry.strip()
        if not entry:
            continue
        # 格式: ../类别/名称.md 或 ./类别/名称.md
        target = entry.lstrip(".")
        if target.startswith("/"):
            target = target[1:]
        # 规范化分隔符
        target = target.replace("\\", "/")
        # 确保是 两层
        parts = target.split("/")
        if len(parts) == 2:
            # 检查目标文件是否存在
            cand = f"{parts[0]}/{parts[1]}"
            if cand in file_map:
                results.append(cand)
            else:
                # 尝试不带 .md 后缀再试
                cand2 = cand
                if not cand2.endswith(".md"):
                    cand2 += ".md"
                # 也检查 stem 匹配
                stem = parts[1].replace(".md", "")
                for fp, pg in file_map.items():
                    if pg["name"] == stem or fp.endswith(f"{stem}.md"):
                        results.append(fp)
                        break
    return results

for p in pages:
    if not p.get("related"):
        continue
    src_file = p["file"]
    targets = resolve_related(src_file, p["related"])
    if src_file not in graph_nodes:
        graph_nodes[src_file] = {
            "id": src_file,
            "name": p["name"],
            "cat": p["cat"],
            "src_count": p["src_count"],
            "degree": 0,
        }
    for t in targets:
        if t in file_map and t != src_file:
            tp = file_map[t]
            if t not in graph_nodes:
                graph_nodes[t] = {
                    "id": t,
                    "name": tp["name"],
                    "cat": tp["cat"],
                    "src_count": tp["src_count"],
                    "degree": 0,
                }
            graph_nodes[src_file]["degree"] += 1
            graph_nodes[t]["degree"] += 1
            graph_edges.append({"source": src_file, "target": t})

# 去重边
edge_set = set()
unique_edges = []
for e in graph_edges:
    key = tuple(sorted([e["source"], e["target"]]))
    if key not in edge_set:
        edge_set.add(key)
        unique_edges.append(e)
graph_edges = unique_edges

print(f"关系图谱: {len(graph_nodes)} 节点, {len(graph_edges)} 边")

# ── 2. 统计数据 ────────────────────────────────────────────────────
by_type = defaultdict(int)
by_month = defaultdict(int)
by_year = defaultdict(int)

for p in pages:
    by_type[p["type"]] += 1
    if p["min_pd"]:
        ym = p["min_pd"][:7]
        by_month[ym] += 1
        by_year[p["min_pd"][:4]] += 1

# raw 目录计数
raw_dir = Path("raw/json")
raw_count = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0

stats = {
    "total_pages": len(pages),
    "total_raw": raw_count,
    "by_type": dict(sorted(by_type.items())),
    "by_month": dict(sorted(by_month.items())),
    "by_year": dict(sorted(by_year.items())),
}

# ── 3. 重要现象与问题（人工策划，附动态数据） ──────────────────────
PHENOMENA = [
    {
        "name": "大文学观",
        "category": "理论争鸣",
        "color": "#4ecdc4",
        "wiki": "主题/大文学观.md",
        "description": "李明泉提出三层结构论、张柠论AI背景下的文学转型、谢有顺论文学的三重扩容。核心命题：文学从「纯文学」向「大文学」的范式转型。",
        "keywords": ["大文学观", "文学转型", "纯文学"],
    },
    {
        "name": "新大众文艺",
        "category": "创作现象",
        "color": "#ff6b6b",
        "wiki": "主题/新大众文艺.md",
        "description": "皮村文学小组、清溪村新山乡巨变、西吉文学志愿服务、东莞职工文学等多点涌现。情绪共同体、底层叙事、素人写作为核心议题。",
        "keywords": ["新大众文艺", "皮村", "清溪村", "素人写作", "工人文学"],
    },
    {
        "name": "第九届鲁迅文学奖",
        "category": "重要奖项",
        "color": "#ffd93d",
        "wiki": "事件/第九届鲁迅文学奖.md",
        "description": "2026年7月揭晓，7个门类共35部作品获奖。8月28日首次在上海颁奖，永久落户。新时代文学最高荣誉奖的标志性事件。",
        "keywords": ["鲁迅文学奖", "文学奖项", "中国文学盛典"],
    },
    {
        "name": "文学读者接受",
        "category": "文学场域",
        "color": "#6c5ce7",
        "wiki": "主题/文学读者.md",
        "description": "韩松刚主持「文学读者在哪里」专题，从传统文学、网络文学、儿童文学三个维度探讨读者缺席与重塑问题。",
        "keywords": ["读者", "阅读", "接受美学", "读者研究"],
    },
    {
        "name": "县域文学",
        "category": "文学场域",
        "color": "#00b894",
        "wiki": "主题/县域文学.md",
        "description": "练韬提出「县域文学」概念：县域是都市的起点与乡村的尽头，日常生活诗性伦理。新时代城市文学的新空间。",
        "keywords": ["县域文学", "城市文学", "日常生活", "中国式现代化"],
    },
    {
        "name": "AI与文学",
        "category": "理论争鸣",
        "color": "#e17055",
        "wiki": "主题/AI与文学.md",
        "description": "人工智能对文学创作、批评、传播的全方位冲击。涉及AI写作版权、人机协作、文学主体性等前沿议题。",
        "keywords": ["AI", "人工智能", "ChatGPT", "文学主体性"],
    },
    {
        "name": "素人写作",
        "category": "创作现象",
        "color": "#fdcb6e",
        "wiki": "",
        "description": "非职业作家的文学创作现象，范雨素、王计兵（外卖诗人）等为代表。打破专业/业余界限，重新定义「文学」的边界。",
        "keywords": ["素人写作", "范雨素", "王计兵", "外卖诗人"],
    },
    {
        "name": "网络文学",
        "category": "文学场域",
        "color": "#a29bfe",
        "wiki": "",
        "description": "网络文学经典化、茅盾新人奖·网络文学奖、IP改编等持续成为年度热点。",
        "keywords": ["网络文学", "IP改编", "茅盾新人奖·网络文学奖"],
    },
    {
        "name": "现实主义",
        "category": "理论争鸣",
        "color": "#55a3f5",
        "wiki": "主题/现实主义.md",
        "description": "赵炎秋论中国现实主义文学的真实性问题，从生活真实、主观观念、表现方式、形象世界四个维度展开。",
        "keywords": ["现实主义", "真实性", "文学创作方法"],
    },
    {
        "name": "乡村振兴与文学书写",
        "category": "创作现象",
        "color": "#2ecc71",
        "wiki": "",
        "description": "清溪村「新山乡巨变」专题创作、乡土文学转型、脱贫攻坚叙事等持续涌现。",
        "keywords": ["乡村振兴", "山乡巨变", "乡土文学"],
    },
    {
        "name": "生态文学",
        "category": "创作现象",
        "color": "#1abc9c",
        "wiki": "",
        "description": "生态主题创作持续活跃，自然书写与生态文明理念深度融合。",
        "keywords": ["生态文学", "自然书写", "生态文明"],
    },
    {
        "name": "科幻文学",
        "category": "创作现象",
        "color": "#9b59b6",
        "wiki": "",
        "description": "冷湖科幻文学奖、鲲鹏青少年科幻文学奖、贺财霖科幻文学奖持续推动科幻创作繁荣。",
        "keywords": ["科幻", "冷湖", "鲲鹏", "贺财霖"],
    },
    {
        "name": "非虚构写作",
        "category": "创作现象",
        "color": "#e67e22",
        "wiki": "",
        "description": "非虚构写作热潮延续，报告文学与非虚构文学的边界、方法论持续讨论。",
        "keywords": ["非虚构", "报告文学", "纪实"],
    },
    {
        "name": "历史虚无主义",
        "category": "舆情现象",
        "color": "#c0392b",
        "wiki": "",
        "description": "⚠️ 数据待补充 — 当前 Wiki 中暂未收录与「历史虚无主义」直接相关的文艺思潮讨论。",
        "keywords": ["历史虚无主义", "虚无主义"],
    },
    {
        "name": "极端女权主义",
        "category": "舆情现象",
        "color": "#c0392b",
        "wiki": "",
        "description": "⚠️ 数据待补充 — 当前 Wiki 中暂未收录与「极端女权主义」相关的文艺舆情内容。",
        "keywords": ["极端女权", "性别争议"],
    },
    {
        "name": "鉴抄事件",
        "category": "舆情现象",
        "color": "#c0392b",
        "wiki": "",
        "description": "⚠️ 数据待补充 — 当前 Wiki 中暂未收录与「鉴抄事件」相关的文学舆情内容。",
        "keywords": ["鉴抄", "抄袭争议"],
    },
]

# 为每个现象附加动态数据
for ph in PHENOMENA:
    if ph["wiki"]:
        # 查找匹配页面
        match = [p for p in pages if p["file"] == ph["wiki"]]
        if match:
            ph["page_count"] = len(match)
            ph["source_count"] = match[0]["src_count"]
            ph["min_pd"] = match[0]["min_pd"]
            ph["max_pd"] = match[0]["max_pd"]
        else:
            ph["page_count"] = 0
            ph["source_count"] = 0
            ph["min_pd"] = ""
            ph["max_pd"] = ""
    else:
        # 按关键词搜索
        matches = [p for p in pages if any(k in " ".join(p["tags"]) or k in p["name"] for k in ph["keywords"])]
        ph["page_count"] = len(matches)
        ph["source_count"] = sum(m["src_count"] for m in matches)
        pdates = [m["min_pd"] for m in matches if m["min_pd"]]
        ph["min_pd"] = min(pdates) if pdates else ""
        ph["max_pd"] = max(pdates) if pdates else ""

# ── 4. 大事记：筛选高学术价值事件 ──────────────────────────────────

# 4.1 奖项类事件（完整获奖名单，从 raw 源提取）
AWARD_EVENTS = [
    {
        "name": "第九届鲁迅文学奖",
        "date": "2026-07-15",
        "category": "国家级奖项",
        "wiki": "事件/第九届鲁迅文学奖.md",
        "source_count": 26,
        "description": "中国作协主办，2026年7月15日揭晓，8月28日首次在上海颁奖并永久落户。7个门类共35部作品获奖，覆盖面为历届之最。",
        "awards": [
            {"category": "中篇小说奖", "works": [
                {"title": "秘密", "author": "全勇先"},
                {"title": "父亲和雕像", "author": "肖克凡"},
                {"title": "阳关三叠", "author": "林那北"},
                {"title": "屋檐", "author": "罗伟章"},
                {"title": "猛犸象", "author": "胡性能"},
            ]},
            {"category": "短篇小说奖", "works": [
                {"title": "漫长的季节", "author": "班宇"},
                {"title": "彼此", "author": "哲贵"},
                {"title": "她和她的麦子", "author": "何玉茹"},
                {"title": "不知", "author": "储福金"},
                {"title": "序曲", "author": "艾玛"},
            ]},
            {"category": "报告文学奖", "works": [
                {"title": "穿越人间的象群", "author": "陈启文"},
                {"title": "遵义三日", "author": "胡松涛"},
                {"title": "要有光", "author": "梁鸿"},
                {"title": "西海固笔记", "author": "季栋梁"},
                {"title": "绽放", "author": "丁捷"},
            ]},
            {"category": "诗歌奖", "works": [
                {"title": "又见群山如黛", "author": "梁小斌"},
                {"title": "入海的长笛", "author": "叶玉琳"},
                {"title": "低处飞行", "author": "王计兵"},
                {"title": "大地为万物彻夜生长", "author": "江非"},
                {"title": "我愿埋首人间", "author": "张二棍"},
            ]},
            {"category": "散文杂文奖", "works": [
                {"title": "古灵魂", "author": "张锐锋"},
                {"title": "生活在临终医院", "author": "薛舒"},
                {"title": "人间珍贵", "author": "傅菲"},
                {"title": "天生草原", "author": "艾平"},
                {"title": "有所思", "author": "彭程"},
            ]},
            {"category": "理论评论奖", "works": [
                {"title": "文学的深意", "author": "谢有顺"},
                {"title": "劳者歌其事", "author": "卓今"},
                {"title": "文学的风景与思想的风致", "author": "贺仲明"},
                {"title": "总体性与社会主义文学传统", "author": "杨辉"},
                {"title": "\u201c新红色经典\u201d论", "author": "傅逸尘"},
            ]},
            {"category": "文学翻译奖", "works": [
                {"title": "约翰生传", "author": "蒲隆 译"},
                {"title": "芬尼根的守灵夜", "author": "戴从容 译"},
                {"title": "人类的末日", "author": "张芸 译"},
                {"title": "拉夫尔", "author": "刘洪波 译"},
                {"title": "战争，战争，战争", "author": "袁筱一 译"},
            ]},
        ],
    },
    {
        "name": "第六届茅盾新人奖",
        "date": "2026-06-16",
        "category": "国家级奖项",
        "wiki": "事件/第六届茅盾新人奖颁奖典礼.md",
        "source_count": 1,
        "description": "2026年适逢茅盾诞辰130周年，在其故乡桐乡颁发。含传统文学奖10人、网络文学奖10人、提名奖各10人。",
        "awards": [
            {"category": "茅盾新人奖", "works": [
                {"title": "", "author": "李俊（宝树）"},
                {"title": "", "author": "朱婧"},
                {"title": "", "author": "陈培浩"},
                {"title": "", "author": "邹胜念"},
                {"title": "", "author": "黄平"},
                {"title": "", "author": "于博（秦北）"},
                {"title": "", "author": "王洁（沫沫）"},
                {"title": "", "author": "周明全"},
                {"title": "", "author": "赵勤（七堇年）"},
                {"title": "", "author": "徐刚"},
            ]},
            {"category": "网络文学奖", "works": [
                {"title": "", "author": "丁莹（丁墨）"},
                {"title": "", "author": "王怀誉（三九音域）"},
                {"title": "", "author": "李虎（天蚕土豆）"},
                {"title": "", "author": "张栩（匪迦）"},
                {"title": "", "author": "杜珏璞（杀虫队队员）"},
                {"title": "", "author": "胡炜（狐尾的笔）"},
                {"title": "", "author": "陈思玄（玄色）"},
                {"title": "", "author": "杨郑（青鸾峰上）"},
                {"title": "", "author": "班亮（知白）"},
                {"title": "", "author": "徐文艳（飘荡墨尔本）"},
            ]},
            {"category": "提名奖", "works": [
                {"title": "", "author": "马慧娟"},
                {"title": "", "author": "肖睿"},
                {"title": "", "author": "罗旭（吟光）"},
                {"title": "", "author": "钱幸"},
                {"title": "", "author": "蒋在"},
                {"title": "", "author": "王忆"},
                {"title": "", "author": "陈思"},
                {"title": "", "author": "杨则纬"},
                {"title": "", "author": "梁书正"},
                {"title": "", "author": "潘菊艳（段若兮）"},
            ]},
        ],
    },
    {
        "name": "2022-2024年度赵树理文学奖",
        "date": "2026-01-12",
        "category": "省级奖项",
        "wiki": "事件/赵树理文学奖2022-2024.md",
        "source_count": 1,
        "description": "山西省最高荣誉文学奖项，每三年评选一次。12类奖项，共19部（篇）作品及5位个人获奖。",
        "awards": [
            {"category": "长篇小说奖", "works": [
                {"title": "西口西口", "author": "李爱民"},
                {"title": "沐月记", "author": "李迎兵"},
            ]},
            {"category": "中篇小说奖", "works": [
                {"title": "千年杨家百年河", "author": "岳占东"},
                {"title": "十三根烟囱", "author": "张发"},
            ]},
            {"category": "短篇小说奖", "works": [
                {"title": "我拿什么拯救你", "author": "石国平"},
                {"title": "浮生", "author": "迟迟（韩莉）"},
            ]},
            {"category": "诗歌奖", "works": [
                {"title": "时间的暗伤", "author": "赵建雄"},
                {"title": "时间黄金", "author": "杨丕梁"},
            ]},
            {"category": "散文奖", "works": [
                {"title": "归家之思", "author": "柏川（王百灵）"},
                {"title": "故乡有此", "author": "乔傲龙"},
            ]},
            {"category": "报告文学奖", "works": [
                {"title": "蒲剧文物记忆", "author": "姚阿林"},
                {"title": "绛州澄泥砚", "author": "李云峰"},
                {"title": "东方贞德——华侨民族女英雄李林传", "author": "王宝国"},
            ]},
            {"category": "文学评论奖", "works": [
                {"title": "试论王朝闻文学理论中的\u201c别车杜\u201d影响", "author": "梁贝"},
                {"title": "红色经典的时代之问", "author": "刘照华"},
            ]},
            {"category": "儿童文学奖", "works": [
                {"title": "故宫奇遇记1：寻找神奇咒语", "author": "梁芳（梁芳芳）"},
                {"title": "好忙好忙的巨人", "author": "张旭燕"},
            ]},
            {"category": "网络文学奖", "works": [
                {"title": "开局账号被盗，反手充值一百万", "author": "酒剑仙人（张波）"},
                {"title": "祂们都叫我大师", "author": "梁超"},
            ]},
        ],
    },
    {
        "name": "第八届辽宁省辽宁文学奖",
        "date": "2026-08-08",
        "category": "省级奖项",
        "wiki": "事件/第十一届辽宁文学奖.md",
        "source_count": 2,
        "description": "辽宁文学奖三奖项颁奖典礼在沈阳举行。含文学评论奖、文学翻译奖、文学理论批评奖。",
        "awards": [],
    },
    {
        "name": "第十五届唐弢青年文学研究奖",
        "date": "2026-07-11",
        "category": "学术奖项",
        "wiki": "事件/第十五届唐弢青年文学研究奖.md",
        "source_count": 1,
        "description": "中国现代文学馆主办，在沪颁奖，表彰青年文学研究成果。",
        "awards": [],
    },
    {
        "name": "首届梧州市岭南文学奖",
        "date": "2026-08-20",
        "category": "地市级奖项",
        "wiki": "事件/首届梧州市岭南文学奖.md",
        "source_count": 1,
        "description": "粤桂琼10部（篇）作品获奖，区域文学协作新模式。",
        "awards": [],
    },
    {
        "name": "第二届寿春杯·《小说选刊》年度大奖",
        "date": "2026-08-04",
        "category": "专业奖项",
        "wiki": "事件/寿春杯小说选刊年度大奖.md",
        "source_count": 1,
        "description": "在安徽寿县颁奖，小说选刊年度评选。",
        "awards": [],
    },
]

# 4.2 会议/学术类事件（从高价值事件页提取）
CONFERENCE_KEYWORDS = [
    "研讨会", "论坛", "座谈会", "学术", "发布",
    "中国文学", "新时代", "创作", "批评",
]
CONFERENCE_IMPORTANT = [
    "新时代文学", "中国当代文学", "文学批评", "文学理论",
    "现实主义", "大文学观", "新大众文艺",
]

def score_event(p):
    """给事件页打学术价值分（0-100）"""
    score = 0
    # sources 权重
    score += min(p["src_count"] * 3, 30)
    # 时间线条目数
    score += min(len(p["timeline"]) * 5, 20)
    # 名称含重要关键词
    name = p["name"]
    for kw in CONFERENCE_IMPORTANT:
        if kw in name:
            score += 20
            break
    for kw in CONFERENCE_KEYWORDS:
        if kw in name:
            score += 8
            break
    # 奖项相关
    award_kw = ["奖", "颁奖", "揭晓", "评选", "获奖"]
    for kw in award_kw:
        if kw in name:
            score += 10
            break
    # desc 长度
    score += min(len(p["desc"]) // 20, 15)
    return min(score, 100)

# 筛选事件
event_pages = [p for p in pages if p["type"] == "事件"]
for p in event_pages:
    p["score"] = score_event(p)

# 过滤低分，取 top 80 事件（不含已列入 AWARD_EVENTS 的）
award_names = {e["name"] for e in AWARD_EVENTS}
non_award_events = [p for p in event_pages if p["name"] not in award_names]
high_value_events = sorted(non_award_events, key=lambda x: -x["score"])[:80]

# 构建大事记数据
BIG_EVENTS = []

# 先加入人工策划的奖项事件
for ae in AWARD_EVENTS:
    BIG_EVENTS.append({
        "name": ae["name"],
        "date": ae["date"],
        "category": ae["category"],
        "source_count": ae["source_count"],
        "description": ae["description"],
        "awards": ae.get("awards", []),
        "wiki": ae.get("wiki", ""),
        "score": 100,
    })

# 再加入高价值事件页
for ev in high_value_events[:60]:
    # 日期从 timeline 或 min_pd 取
    date = ""
    if ev["timeline"]:
        date = ev["timeline"][0]["date"]
    elif ev["min_pd"]:
        date = ev["min_pd"]
    # 截取描述
    desc = ev["desc"][:500] if ev["desc"] else ""
    BIG_EVENTS.append({
        "name": ev["name"],
        "date": date,
        "category": "学术活动" if any(kw in ev["name"] for kw in CONFERENCE_KEYWORDS) else "文学事件",
        "source_count": ev["src_count"],
        "description": desc,
        "awards": [],
        "wiki": ev["file"],
        "score": ev["score"],
    })

# 按日期排序
BIG_EVENTS.sort(key=lambda x: x["date"] or "9999", reverse=True)

# ── 4b. 综述引擎：为重要现象与大事记生成结构化综述 ────────────────
REVIEW_DEBATE_KW = ("争鸣", "研讨", "观点", "反思", "质疑", "访谈", "对话", "座谈会", "论坛", "讨论", "论", "评")

def _page_review(page):
    src = list(page.get("sources_list") or [])
    tl = sorted(page.get("timeline") or [], key=lambda t: t["date"])
    debates = [s for s in (page.get("sections") or [])
               if any(k in s["title"] for k in REVIEW_DEBATE_KW)]
    return src, tl, debates

def build_review_for(name, description, keywords, wiki_file):
    """基于 wiki 页面集合生成综述结构"""
    matches = []
    if wiki_file:
        w = [p for p in pages if p["file"] == wiki_file]
        if w:
            matches = [w[0]]
    if not matches:
        for p in pages:
            s = p["name"] + " " + " ".join(p["tags"]) + " " + p["desc"]
            if any(k and k in s for k in keywords):
                matches.append(p)
                if len(matches) >= 40:
                    break
    src_all, tl_all, debate_all, rel = [], [], [], []
    for p in matches:
        s, t, d = _page_review(p)
        src_all.extend(s)
        tl_all.extend(p.get("timeline") or [])
        debate_all.extend(d)
        rel.append({"file": p["file"], "name": p["name"], "cat": p["cat"]})
    tl_all.sort(key=lambda x: x["date"])
    # 去重来源/关联
    seen_url, seen_f = set(), set()
    src_uniq, rel_uniq = [], []
    for s in src_all:
        if s["url"] not in seen_url:
            seen_url.add(s["url"])
            src_uniq.append(s)
    for r in rel:
        if r["file"] not in seen_f:
            seen_f.add(r["file"])
            rel_uniq.append(r)
    return {
        "name": name,
        "overview": description,
        "evolution": tl_all[:60],
        "debate": debate_all[:15],
        "sources": src_uniq,
        "related": rel_uniq,
    }

for ph in PHENOMENA:
    ph["review"] = build_review_for(ph["name"], ph["description"], ph.get("keywords", []), ph.get("wiki", ""))

for ev in BIG_EVENTS:
    ev["review"] = build_review_for(ev["name"], ev["description"], [ev["name"]], ev.get("wiki", ""))

# ── 4c. 类别索引：人物/作品/主题/概念/流派/机构/事件 ───────────────
CATEGORY_ORDER = ["人物", "作品", "主题", "概念", "流派", "机构", "事件"]
categories = {c: [] for c in CATEGORY_ORDER}
for p in pages:
    cat = p["cat"] if p["cat"] in CATEGORY_ORDER else "事件"
    categories[cat].append({
        "file": p["file"],
        "name": p["name"],
        "type": p["type"],
        "tags": p["tags"],
        "desc": p["desc"][:200],
        "src_count": p["src_count"],
        "min_pd": p["min_pd"],
        "max_pd": p["max_pd"],
        "timeline": p["timeline"][:20],
        "sources": (p["sources_list"] or [])[:15],
        "related": p["related"],
    })
for c in CATEGORY_ORDER:
    categories[c].sort(key=lambda x: -x["src_count"])

# ── 5. 生成 HTML ────────────────────────────────────────────────────

# 构建时间线摘要：按年月聚合页面
timeline_months = defaultdict(lambda: defaultdict(int))
for p in pages:
    if p["min_pd"]:
        ym = p["min_pd"][:7]
        timeline_months[ym][p["type"]] += 1

def build_month_chart():
    months = sorted(timeline_months.keys())
    if not months:
        return []
    result = []
    for m in months:
        d = dict(timeline_months[m])
        d["_month"] = m
        result.append(d)
    return result

# HTML 模板
def gen_html(data_json):
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>新时代文学驾驶舱</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
  font-family: -apple-system, "PingFang SC", "Microsoft YaHei", sans-serif;
  background: #0a0e27;
  color: #e0e0e0;
  min-height: 100vh;
}}
/* ── 头部 ── */
.header {{
  background: linear-gradient(135deg, #0d1137 0%, #1a1f4e 100%);
  padding: 20px 30px;
  border-bottom: 2px solid #2a3075;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 15px;
}}
.header h1 {{
  font-size: 22px;
  color: #64b5f6;
  letter-spacing: 2px;
}}
.header .subtitle {{
  font-size: 12px;
  color: #7986cb;
}}
/* ── 控制面板 ── */
.controls {{
  background: #0d1137;
  padding: 12px 30px;
  border-bottom: 1px solid #1a2055;
  display: flex;
  align-items: center;
  gap: 20px;
  flex-wrap: wrap;
}}
.controls label {{
  font-size: 13px;
  color: #90a4ae;
}}
.controls select, .controls input {{
  background: #151a3a;
  color: #e0e0e0;
  border: 1px solid #2a3075;
  padding: 5px 10px;
  border-radius: 4px;
  font-size: 13px;
}}
.controls select:focus, .controls input:focus {{
  outline: none;
  border-color: #4fc3f7;
}}
.view-btns {{
  display: flex;
  gap: 8px;
}}
.view-btns button {{
  background: #1a2055;
  color: #90a4ae;
  border: 1px solid #2a3075;
  padding: 5px 14px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}}
.view-btns button.active {{
  background: #1565c0;
  color: #fff;
  border-color: #1e88e5;
}}
.view-btns button:hover {{
  background: #1e3a5f;
}}
/* ── 主内容 ── */
.main {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 0;
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}}
/* ── 概览卡片 ── */
.overview {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 15px;
  margin-bottom: 25px;
}}
.stat-card {{
  background: linear-gradient(135deg, #111540 0%, #151a3a 100%);
  border: 1px solid #2a3075;
  border-radius: 8px;
  padding: 18px;
  text-align: center;
}}
.stat-card .num {{
  font-size: 28px;
  font-weight: bold;
  color: #4fc3f7;
}}
.stat-card .label {{
  font-size: 12px;
  color: #7986cb;
  margin-top: 5px;
}}
/* ── 时间线图 ── */
.timeline-chart {{
  background: #111540;
  border: 1px solid #2a3075;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 25px;
}}
.timeline-chart h2 {{
  font-size: 16px;
  color: #64b5f6;
  margin-bottom: 15px;
  border-left: 3px solid #4fc3f7;
  padding-left: 10px;
}}
.chart-bars {{
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 120px;
  overflow-x: auto;
  padding-bottom: 20px;
  position: relative;
}}
.chart-bar {{
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 28px;
  position: relative;
}}
.chart-bar .bar {{
  width: 22px;
  background: linear-gradient(180deg, #4fc3f7 0%, #1565c0 100%);
  border-radius: 3px 3px 0 0;
  transition: all 0.3s;
  position: relative;
}}
.chart-bar .bar:hover {{
  background: linear-gradient(180deg, #81d4fa 0%, #42a5f5 100%);
}}
.chart-bar .bar-label {{
  position: absolute;
  top: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #90a4ae;
  white-space: nowrap;
}}
.chart-bar .month-label {{
  font-size: 9px;
  color: #607d8b;
  position: absolute;
  bottom: -18px;
  transform: rotate(-45deg);
  transform-origin: top right;
  white-space: nowrap;
}}
/* ── 分类统计 ── */
.type-stats {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
  margin-bottom: 25px;
}}
.type-chip {{
  background: #111540;
  border: 1px solid #2a3075;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
}}
.type-chip .t-num {{
  font-size: 20px;
  font-weight: bold;
}}
.type-chip .t-label {{
  font-size: 11px;
  color: #7986cb;
  margin-top: 4px;
}}
/* ── 重要现象与问题 ── */
.section-title {{
  font-size: 18px;
  color: #64b5f6;
  margin-bottom: 15px;
  padding-left: 12px;
  border-left: 4px solid #4fc3f7;
}}
.phenomena-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 15px;
  margin-bottom: 30px;
}}
.phenomenon-card {{
  background: linear-gradient(135deg, #111540 0%, #151a3a 100%);
  border: 1px solid #2a3075;
  border-radius: 8px;
  padding: 16px;
  border-top: 3px solid var(--accent);
  transition: transform 0.2s, box-shadow 0.2s;
  cursor: pointer;
}}
.phenomenon-card:hover {{
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(79, 195, 247, 0.15);
}}
.phenomenon-card .ph-head {{
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}}
.phenomenon-card .ph-cat {{
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(255,255,255,0.08);
  color: var(--accent);
}}
.phenomenon-card .ph-name {{
  font-size: 15px;
  font-weight: bold;
  color: #fff;
}}
.phenomenon-card .ph-desc {{
  font-size: 13px;
  color: #b0bec5;
  line-height: 1.6;
  margin-bottom: 10px;
}}
.phenomenon-card .ph-meta {{
  display: flex;
  gap: 15px;
  font-size: 11px;
  color: #607d8b;
}}
.phenomenon-card .ph-meta span {{
  display: flex;
  align-items: center;
  gap: 4px;
}}
/* ── 大事记 ── */
.events-section {{
  margin-bottom: 30px;
}}
.event-list {{
  display: flex;
  flex-direction: column;
  gap: 12px;
}}
.event-card {{
  background: #111540;
  border: 1px solid #2a3075;
  border-radius: 8px;
  padding: 16px 20px;
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 16px;
  align-items: start;
}}
.event-card .ev-date {{
  font-size: 13px;
  color: #4fc3f7;
  font-family: "SF Mono", "Fira Code", monospace;
  padding-top: 2px;
}}
.event-card .ev-body h3 {{
  font-size: 15px;
  color: #fff;
  margin-bottom: 4px;
}}
.event-card .ev-body .ev-cat {{
  font-size: 11px;
  color: #7986cb;
  margin-bottom: 6px;
}}
.event-card .ev-body .ev-desc {{
  font-size: 13px;
  color: #b0bec5;
  line-height: 1.6;
}}
/* ── 获奖名单表格 ── */
.award-table {{
  margin-top: 12px;
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
}}
.award-table th {{
  background: #1a2055;
  color: #90a4ae;
  padding: 6px 10px;
  text-align: left;
  font-weight: normal;
  border-bottom: 1px solid #2a3075;
}}
.award-table td {{
  padding: 5px 10px;
  border-bottom: 1px solid #151a3a;
  color: #cfd8dc;
}}
.award-table tr:hover td {{
  background: #151a3a;
}}
.award-category {{
  font-size: 13px;
  color: #ffd93d;
  margin-top: 12px;
  margin-bottom: 6px;
  font-weight: bold;
}}
/* ── 关系图谱 ── */
.graph-section {{
  margin-bottom: 30px;
}}

/* ── 类别导航 ── */
.cat-nav {{
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 18px;
  padding: 10px 0;
  border-bottom: 1px solid #1a2055;
}}
.cat-chip {{
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  border: 1px solid #2a3075;
  background: #111540;
  color: #90a4ae;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}}
.cat-chip:hover {{
  background: #1a2055;
  color: #e0e0e0;
  border-color: #4fc3f7;
}}
.cat-chip.active {{
  background: #1565c0;
  color: #fff;
  border-color: #1565c0;
}}
.cat-chip .cat-count {{
  font-size: 11px;
  opacity: 0.7;
  margin-left: 4px;
}}

/* ── 遮罩面板 ── */
.overlay {{
  display: none;
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0,0,0,0.7);
  backdrop-filter: blur(4px);
}}
.overlay.open {{ display: flex; justify-content: center; align-items: flex-start; padding: 40px 20px; overflow-y: auto; }}
.overlay-panel {{
  background: #0d1033;
  border: 1px solid #2a3075;
  border-radius: 12px;
  width: 100%;
  max-width: 960px;
  max-height: 85vh;
  overflow-y: auto;
  padding: 28px;
  position: relative;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
}}
.overlay-close {{
  position: absolute;
  top: 14px;
  right: 18px;
  background: none;
  border: none;
  color: #78909c;
  font-size: 24px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
}}
.overlay-close:hover {{ color: #fff; background: rgba(255,255,255,0.08); }}
.overlay-title {{
  font-size: 22px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 6px;
}}
.overlay-subtitle {{
  font-size: 13px;
  color: #78909c;
  margin-bottom: 18px;
}}

/* ── 搜索框 ── */
.search-box {{
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}}
.search-box input {{
  flex: 1;
  background: #151a3a;
  border: 1px solid #2a3075;
  border-radius: 8px;
  padding: 10px 14px;
  color: #e0e0e0;
  font-size: 14px;
  outline: none;
}}
.search-box input:focus {{ border-color: #4fc3f7; }}
.search-box input::placeholder {{ color: #546e7a; }}

/* ── 列表项 ── */
.entity-list {{
  display: flex;
  flex-direction: column;
  gap: 8px;
}}
.entity-item {{
  background: #111540;
  border: 1px solid #1e2555;
  border-radius: 8px;
  padding: 14px 16px;
  cursor: pointer;
  transition: all 0.15s;
}}
.entity-item:hover {{
  background: #151a3a;
  border-color: #4fc3f7;
  transform: translateX(3px);
}}
.entity-item .ei-name {{
  font-size: 15px;
  font-weight: 600;
  color: #e0e0e0;
  margin-bottom: 4px;
}}
.entity-item .ei-tags {{
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}}
.entity-item .ei-tag {{
  font-size: 11px;
  padding: 1px 6px;
  border-radius: 8px;
  background: rgba(79,195,247,0.1);
  color: #4fc3f7;
}}
.entity-item .ei-desc {{
  font-size: 12px;
  color: #78909c;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}}
.entity-item .ei-meta {{
  font-size: 11px;
  color: #546e7a;
  margin-top: 6px;
}}
.list-count {{
  font-size: 12px;
  color: #546e7a;
  margin-bottom: 12px;
}}

/* ── 详情/综述面板 ── */
.review-section {{
  margin-bottom: 20px;
}}
.review-section h3 {{
  font-size: 16px;
  font-weight: 600;
  color: #4fc3f7;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #1a2055;
}}
.review-overview {{
  font-size: 14px;
  color: #b0bec5;
  line-height: 1.7;
}}
.tl-item {{
  display: flex;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid #151a3a;
}}
.tl-date {{
  min-width: 100px;
  font-size: 13px;
  color: #4fc3f7;
  font-family: "SF Mono", "Fira Code", monospace;
}}
.tl-text {{
  font-size: 13px;
  color: #b0bec5;
  line-height: 1.5;
}}
.debate-item {{
  padding: 10px 14px;
  background: #111540;
  border-left: 3px solid #ff9800;
  border-radius: 0 6px 6px 0;
  margin-bottom: 8px;
}}
.debate-item .deb-title {{
  font-size: 13px;
  font-weight: 600;
  color: #ffd93d;
  margin-bottom: 2px;
}}
.debate-item .deb-body {{
  font-size: 12px;
  color: #90a4ae;
  line-height: 1.5;
}}
.src-item {{
  display: flex;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid #0d1033;
  font-size: 12px;
  align-items: baseline;
}}
.src-url {{
  color: #81d4fa;
  text-decoration: none;
  word-break: break-all;
}}
.src-url:hover {{ text-decoration: underline; }}
.src-date {{
  color: #546e7a;
  white-space: nowrap;
  flex-shrink: 0;
}}
.rel-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 8px;
}}
.rel-chip {{
  padding: 8px 12px;
  background: #111540;
  border: 1px solid #1e2555;
  border-radius: 6px;
  font-size: 12px;
  color: #b0bec5;
  cursor: pointer;
  transition: all 0.15s;
}}
.rel-chip:hover {{ border-color: #4fc3f7; color: #e0e0e0; }}
.rel-chip .rc-cat {{
  font-size: 10px;
  color: #546e7a;
  margin-left: 4px;
}}
.graph-container {{
  background: #111540;
  border: 1px solid #2a3075;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}}
.graph-toolbar {{
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  background: #0d1137;
  border-bottom: 1px solid #1a2055;
  flex-wrap: wrap;
}}
.graph-toolbar .cat-btn {{
  font-size: 12px;
  padding: 3px 10px;
  border-radius: 12px;
  border: 1px solid transparent;
  cursor: pointer;
  transition: all 0.2s;
  background: rgba(255,255,255,0.06);
  color: #90a4ae;
}}
.graph-toolbar .cat-btn.active {{
  border-color: var(--c);
  color: var(--c);
  background: rgba(255,255,255,0.12);
}}
.graph-toolbar .graph-info {{
  margin-left: auto;
  font-size: 11px;
  color: #607d8b;
}}
.graph-toolbar input[type=range] {{
  width: 80px;
  accent-color: #4fc3f7;
}}
#graphCanvas {{
  display: block;
  width: 100%;
  height: 500px;
  cursor: grab;
}}
#graphCanvas:active {{ cursor: grabbing; }}
.graph-tooltip {{
  position: absolute;
  background: #1a1f4e;
  border: 1px solid #2a3075;
  border-radius: 6px;
  padding: 10px 14px;
  font-size: 12px;
  color: #e0e0e0;
  pointer-events: none;
  display: none;
  max-width: 280px;
  z-index: 10;
  box-shadow: 0 4px 20px rgba(0,0,0,0.5);
}}
.graph-tooltip .tt-name {{
  font-size: 14px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 4px;
}}
.graph-tooltip .tt-cat {{
  font-size: 11px;
  color: #7986cb;
  margin-bottom: 4px;
}}
.graph-tooltip .tt-deg {{
  font-size: 11px;
  color: #90a4ae;
}}
/* ── footer ── */
.footer {{
  text-align: center;
  padding: 20px;
  color: #546e7a;
  font-size: 11px;
  border-top: 1px solid #1a2055;
}}
/* ── 响应式 ── */
@media (max-width: 768px) {{
  .event-card {{
    grid-template-columns: 1fr;
  }}
  .phenomena-grid {{
    grid-template-columns: 1fr;
  }}
  .controls {{
    flex-direction: column;
    align-items: flex-start;
  }}
}}
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>新时代文学驾驶舱</h1>
    <div class="subtitle">中国作家网文学数据可视化 · 基于 LLM Wiki 知识库</div>
  </div>
  <div class="subtitle" id="clock"></div>
</div>

<div class="controls">
  <label>显示模式：</label>
  <div class="view-btns" id="viewBtns">
    <button class="active" data-view="all">整体总览</button>
    <button data-view="year">按年度</button>
    <button data-view="custom">自定义年限</button>
  </div>
  <div id="yearControls" style="display:none;">
    <label>选择年份：</label>
    <select id="yearSelect"></select>
  </div>
  <div id="customControls" style="display:none;">
    <label>起始：</label>
    <select id="fromYear"></select>
    <label>至</label>
    <select id="toYear"></select>
    <button onclick="applyCustomRange()" style="background:#1565c0;color:#fff;border:none;padding:5px 12px;border-radius:4px;cursor:pointer;font-size:13px;">确定</button>
  </div>
</div>

<!-- 类别导航 -->
<div class="cat-nav" id="catNav"></div>

<!-- 搜索面板 -->
<div class="overlay" id="searchOverlay">
  <div class="overlay-panel">
    <button class="overlay-close" onclick="closeSearch()">×</button>
    <div class="overlay-title" id="searchTitle"></div>
    <div class="overlay-subtitle" id="searchSub"></div>
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="输入关键词搜索…" oninput="filterSearch()">
    </div>
    <div class="list-count" id="searchCount"></div>
    <div class="entity-list" id="searchList"></div>
  </div>
</div>

<!-- 综述/详情面板 -->
<div class="overlay" id="reviewOverlay">
  <div class="overlay-panel">
    <button class="overlay-close" onclick="closeReview()">×</button>
    <div class="overlay-title" id="reviewTitle"></div>
    <div class="overlay-subtitle" id="reviewSub"></div>
    <div id="reviewContent"></div>
  </div>
</div>

<div class="main">
  <div class="overview" id="overview"></div>
  <div class="type-stats" id="typeStats"></div>
  <div class="timeline-chart">
    <h2>月度趋势</h2>
    <div class="chart-bars" id="chartBars"></div>
  </div>
  <div>
    <h2 class="section-title">重要现象与问题</h2>
    <div class="phenomena-grid" id="phenomena"></div>
  </div>
  <div class="events-section">
    <h2 class="section-title">大事记（学术信息与资料价值）</h2>
    <div class="event-list" id="events"></div>
  </div>
  <div class="graph-section" id="graphSection">
    <h2 class="section-title">关系图谱</h2>
    <div class="graph-container">
      <div class="graph-toolbar" id="graphToolbar"></div>
      <canvas id="graphCanvas"></canvas>
      <div class="graph-tooltip" id="graphTooltip"></div>
    </div>
  </div>
</div>

<div class="footer">
  新时代文学驾驶舱 · 基于新时代文学 LLM WIKI 知识库 · 共 {data_json['stats']['total_pages']} 页 · {data_json['stats']['total_raw']} 篇原始文档
</div>

<script>
const DATA = {json.dumps(data_json, ensure_ascii=False)};

// ── 时钟 ──
function updateClock() {{
  const now = new Date();
  document.getElementById('clock').textContent = now.toLocaleString('zh-CN', {{year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}});
}}
updateClock(); setInterval(updateClock, 1000);

// ── 状态 ──
let currentView = 'all';
let currentYear = '';
let customFrom = '';
let customTo = '';

// ── 年份选项 ──
const years = Object.keys(DATA.stats.by_year).sort();
const yearSelect = document.getElementById('yearSelect');
const fromYear = document.getElementById('fromYear');
const toYear = document.getElementById('toYear');
years.forEach(y => {{
  yearSelect.innerHTML += `<option value="${{y}}">${{y}}</option>`;
  fromYear.innerHTML += `<option value="${{y}}">${{y}}</option>`;
  toYear.innerHTML += `<option value="${{y}}">${{y}}</option>`;
}});
if (years.length) {{
  yearSelect.value = years[years.length - 1];
  fromYear.value = years[0];
  toYear.value = years[years.length - 1];
  currentYear = years[years.length - 1];
}}

// ── 过滤 ──
function filterByMonth(months) {{
  // months: ["2026-01","2026-02",...] or null for all
  if (!months) return DATA.events;
  return DATA.events.filter(e => {{
    if (!e.date) return false;
    const ym = e.date.slice(0,7);
    return months.includes(ym);
  }});
}}

function getActiveMonths() {{
  if (currentView === 'all') return null;
  if (currentView === 'year') {{
    return Object.keys(DATA.stats.by_month).filter(m => m.startsWith(currentYear));
  }}
  if (currentView === 'custom') {{
    if (!customFrom || !customTo) return null;
    return Object.keys(DATA.stats.by_month).filter(m => {{
      const y = m.slice(0,4);
      return y >= customFrom && y <= customTo;
    }});
  }}
  return null;
}}

function renderStats(months) {{
  // 计算过滤后的统计
  let totalPages = DATA.stats.total_pages;
  let totalRaw = DATA.stats.total_raw;
  let byType = DATA.stats.by_type;

  if (months) {{
    // 按月统计需要从页面数据推算
    // 简化：按比例估算
    const allMonths = Object.keys(DATA.stats.by_month);
    const filteredCount = months.reduce((s,m) => s + (DATA.stats.by_month[m] || 0), 0);
    const ratio = allMonths.length ? filteredCount / allMonths.length : 1;
    totalPages = Math.round(DATA.stats.total_pages * Math.min(ratio, 1));
    byType = {{}};
    Object.entries(DATA.stats.by_type).forEach(([k,v]) => {{
      byType[k] = Math.round(v * Math.min(ratio, 1));
    }});
  }}

  let html = '';
  html += `<div class="stat-card"><div class="num">${{totalPages}}</div><div class="label">Wiki 页面</div></div>`;
  html += `<div class="stat-card"><div class="num">${{totalRaw}}</div><div class="label">原始文档</div></div>`;
  html += `<div class="stat-card"><div class="num">${{DATA.phenomena.length}}</div><div class="label">重要现象</div></div>`;
  html += `<div class="stat-card"><div class="num">${{DATA.events.length}}</div><div class="label">大事记条目</div></div>`;
  html += `<div class="stat-card"><div class="num">${{years.length}}</div><div class="label">覆盖年份</div></div>`;
  document.getElementById('overview').innerHTML = html;

  // 分类统计
  let typeHtml = '';
  const typeColors = {{'人物':'#4ecdc4','作品':'#ff6b6b','事件':'#ffd93d','主题':'#6c5ce7','机构':'#00b894','概念':'#e17055','流派':'#a29bfe'}};
  Object.entries(byType).sort((a,b) => b[1]-a[1]).forEach(([k,v]) => {{
    const c = typeColors[k] || '#90a4ae';
    typeHtml += `<div class="type-chip"><div class="t-num" style="color:${{c}}">${{v}}</div><div class="t-label">${{k}}</div></div>`;
  }});
  document.getElementById('typeStats').innerHTML = typeHtml;
}}

function renderChart(months) {{
  const allMonths = months || Object.keys(DATA.stats.by_month).sort();
  const maxVal = Math.max(...allMonths.map(m => DATA.stats.by_month[m] || 0), 1);
  let html = '';
  allMonths.forEach(m => {{
    const v = DATA.stats.by_month[m] || 0;
    const h = Math.max((v / maxVal) * 100, 2);
    html += `<div class="chart-bar"><div class="bar" style="height:${{h}}px" title="${{m}}: ${{v}} 页"><div class="bar-label">${{v}}</div></div><div class="month-label">${{m.slice(5)}}</div></div>`;
  }});
  document.getElementById('chartBars').innerHTML = html;
}}

function renderPhenomena() {{
  let html = '';
  DATA.phenomena.forEach((p, i) => {{
    html += `
      <div class="phenomenon-card" style="--accent:${{p.color}}" onclick="openPhenomenon(${{i}})" title="点击查看综述">
        <div class="ph-head">
          <span class="ph-name">${{esc(p.name)}}</span>
          <span class="ph-cat">${{esc(p.category)}}</span>
        </div>
        <div class="ph-desc">${{esc(p.description)}}</div>
        <div class="ph-meta">
          <span>📄 ${{p.source_count}} 条来源</span>
          <span>📅 ${{p.min_pd || '?'}} ~ ${{p.max_pd || '?'}}</span>
          <span style="color:#4fc3f7;">📖 查看综述 →</span>
        </div>
      </div>`;
  }});
  document.getElementById('phenomena').innerHTML = html;
}}

function renderEvents(events) {{
  let html = '';
  events.forEach(ev => {{
    const eidx = DATA.events.findIndex(e => e.name === ev.name);
    let awardHtml = '';
    if (ev.awards && ev.awards.length) {{
      awardHtml = '<div style="margin-top:10px;">';
      ev.awards.forEach(a => {{
        awardHtml += `<div class="award-category">${{esc(a.category)}}（${{a.works.length}} 部/人）</div>`;
        awardHtml += '<table class="award-table"><tr><th>作品/作者</th><th>作者</th></tr>';
        a.works.forEach(w => {{
          if (w.title) {{
            awardHtml += `<tr><td>${{esc(w.title)}}</td><td>${{esc(w.author)}}</td></tr>`;
          }} else {{
            awardHtml += `<tr><td colspan="2">${{esc(w.author)}}</td></tr>`;
          }}
        }});
        awardHtml += '</table>';
      }});
      awardHtml += '</div>';
    }}
    html += `
      <div class="event-card" onclick="openEvent(${{eidx}})" title="点击查看综述" style="cursor:pointer;">
        <div class="ev-date">${{esc(ev.date || '日期待定')}}</div>
        <div class="ev-body">
          <h3>${{esc(ev.name)}}</h3>
          <div class="ev-cat">${{esc(ev.category)}} · ${{ev.source_count}} 条来源 · <span style="color:#4fc3f7;">📖 查看综述 →</span></div>
          <div class="ev-desc">${{esc(ev.description)}}</div>
          ${{awardHtml}}
        </div>
      </div>`;
  }});
  document.getElementById('events').innerHTML = html || '<div style="color:#607d8b;padding:20px;">该时间段暂无大事记数据</div>';
}}

function esc(s) {{
  if (!s) return '';
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}

function render() {{
  const months = getActiveMonths();
  renderStats(months);
  renderChart(months);
  renderPhenomena();
  const events = filterByMonth(months);
  renderEvents(events);
}}

// ── 类别导航 ──
const CAT_ORDER = ['人物', '作品', '主题', '概念', '流派', '机构', '事件'];
const CAT_ICONS = {{'人物': '👤', '作品': '📖', '主题': '🧭', '概念': '💡', '流派': '🏛', '机构': '🏢', '事件': '📅'}};
let currentSearchCat = '';

function renderCatNav() {{
  let html = '<span style="font-size:13px;color:#78909c;align-self:center;">分类检索：</span>';
  html += `<span class="cat-chip" onclick="openSearch(this, '')">🔍 全部 <span class="cat-count">${{totalPageCount()}}</span></span>`;
  CAT_ORDER.forEach(c => {{
    html += `<span class="cat-chip" onclick="openSearch(this, '${{c}}')">${{CAT_ICONS[c] || ''}} ${{c}} <span class="cat-count">${{(DATA.categories[c] || []).length}}</span></span>`;
  }});
  document.getElementById('catNav').innerHTML = html;
}}

// ── 搜索面板 ──
let searchCache = null;
function openSearch(chip, cat) {{
  document.querySelectorAll('.cat-chip').forEach(c => c.classList.remove('active'));
  if (chip) chip.classList.add('active');
  currentSearchCat = cat;
  searchCache = null;
  document.getElementById('searchInput').value = '';
  if (cat === '') {{
    document.getElementById('searchTitle').textContent = '全库检索';
    document.getElementById('searchSub').textContent = '检索全部 ' + totalPageCount() + ' 个重要文学实体';
  }} else {{
    document.getElementById('searchTitle').textContent = (CAT_ICONS[cat] || '') + ' ' + cat + ' 检索';
    const n = (DATA.categories[cat] || []).length;
    document.getElementById('searchSub').textContent = '共 ' + n + ' 个实体，点击查看详情或输入关键词筛选';
  }}
  document.getElementById('searchOverlay').classList.add('open');
  filterSearch();
  document.getElementById('searchInput').focus();
}}
function totalPageCount() {{
  let n = 0;
  CAT_ORDER.forEach(c => n += (DATA.categories[c] || []).length);
  return n;
}}
function closeSearch() {{
  document.getElementById('searchOverlay').classList.remove('open');
}}
function filterSearch() {{
  if (!searchCache) {{
    searchCache = [];
    if (currentSearchCat === '') {{
      CAT_ORDER.forEach(c => {{
        (DATA.categories[c] || []).forEach(it => searchCache.push(Object.assign({{_cat: c}}, it)));
      }});
    }} else {{
      (DATA.categories[currentSearchCat] || []).forEach(it => searchCache.push(Object.assign({{_cat: currentSearchCat}}, it)));
    }}
  }}
  const q = document.getElementById('searchInput').value.trim().toLowerCase();
  let list = searchCache;
  if (q) {{
    list = searchCache.filter(it => {{
      const hay = (it.name || '') + ' ' + (it.desc || '') + ' ' + (it.tags || []).join(' ');
      return hay.toLowerCase().indexOf(q) >= 0;
    }});
  }}
  document.getElementById('searchCount').textContent = '匹配 ' + list.length + ' 条';
  let html = '';
  list.slice(0, 200).forEach((it, i) => {{
    const tagsHtml = (it.tags || []).slice(0, 4).map(t => `<span class="ei-tag">${{esc(t)}}</span>`).join('');
    html += `
      <div class="entity-item" onclick="openEntity('${{esc(it._cat)}}', '${{esc(it.file)}}')">
        <div class="ei-name">${{esc(it.name)}} <span style="font-size:11px;color:#546e7a;">[${{esc(it._cat)}}]</span></div>
        <div class="ei-tags">${{tagsHtml}}</div>
        <div class="ei-desc">${{esc(it.desc)}}</div>
        <div class="ei-meta">📄 ${{it.src_count || 0}} 条来源${{it.min_pd ? ' · 📅 ' + it.min_pd + ' ~ ' + it.max_pd : ''}}</div>
      </div>`;
  }});
  if (!list.length) html = '<div style="color:#607d8b;padding:30px;text-align:center;">未找到匹配实体，尝试其他关键词</div>';
  if (list.length > 200) html += '<div style="color:#546e7a;padding:10px;text-align:center;">…仅显示前 200 条，请用关键词进一步筛选</div>';
  document.getElementById('searchList').innerHTML = html;
}}

// ── 综述/详情面板 ──
function openReview(title, subtitle, html) {{
  document.getElementById('reviewTitle').textContent = title;
  document.getElementById('reviewSub').textContent = subtitle || '';
  document.getElementById('reviewContent').innerHTML = html;
  document.getElementById('reviewOverlay').classList.add('open');
  document.getElementById('reviewOverlay').scrollTop = 0;
}}
function closeReview() {{
  document.getElementById('reviewOverlay').classList.remove('open');
}}

function reviewHtml(name, category, review, extra) {{
  const r = review || {{}};
  let h = '';
  // 导语/概述
  h += '<div class="review-section"><h3>📌 现象概述</h3><div class="review-overview">' + esc(r.overview || '暂无概述') + '</div></div>';
  // 时间线（演变脉络）
  const tl = r.evolution || [];
  if (tl.length) {{
    h += '<div class="review-section"><h3>🕒 来龙去脉（时间线）</h3>';
    tl.slice(0, 40).forEach(t => {{
      h += `<div class="tl-item"><div class="tl-date">${{esc(t.date)}}</div><div class="tl-text">${{esc(t.text)}}</div></div>`;
    }});
    h += '</div>';
  }}
  // 争鸣/理论问题
  const dbs = r.debate || [];
  if (dbs.length) {{
    h += '<div class="review-section"><h3>⚖️ 理论问题与争鸣</h3>';
    dbs.slice(0, 15).forEach(d => {{
      h += `<div class="debate-item"><div class="deb-title">${{esc(d.title)}}</div><div class="deb-body">${{esc(d.body)}}</div></div>`;
    }});
    h += '</div>';
  }}
  // 关联实体
  const rel = r.related || [];
  if (rel.length) {{
    h += '<div class="review-section"><h3>🔗 相关实体</h3><div class="rel-grid">';
    rel.slice(0, 24).forEach(x => {{
      h += `<div class="rel-chip" onclick="openEntity('${{esc(x.cat)}}', '${{esc(x.file)}}')">${{esc(x.name)}}<span class="rc-cat">${{esc(x.cat)}}</span></div>`;
    }});
    h += '</div></div>';
  }}
  // 来源清单
  const srcs = r.sources || [];
  if (srcs.length) {{
    h += '<div class="review-section"><h3>📄 信息来源清单（' + srcs.length + ' 条）</h3>';
    srcs.slice(0, 100).forEach(s => {{
      h += `<div class="src-item"><span class="src-date">${{esc(s.pubdate || '')}}</span><a class="src-url" href="${{esc(s.url)}}" target="_blank" rel="noopener">${{esc(s.url)}}</a></div>`;
    }});
    if (srcs.length > 100) h += '<div style="color:#546e7a;font-size:12px;">…另有 ' + (srcs.length - 100) + ' 条来源，请前往 wiki 页面查看完整清单</div>';
    h += '</div>';
  }}
  if (extra) h += extra;
  return h;
}}

function openPhenomenon(i) {{
  const p = DATA.phenomena[i];
  if (!p) return;
  const catLine = p.category + ' · ' + p.source_count + ' 条来源 · ' + (p.min_pd || '?') + ' ~ ' + (p.max_pd || '?');
  let h = reviewHtml(p.name, p.category, p.review);
  openReview(p.name, catLine, h);
}}

function openEvent(i) {{
  const ev = DATA.events[i];
  if (!ev) return;
  const catLine = (ev.date || '') + ' · ' + ev.category + ' · ' + ev.source_count + ' 条来源';
  let awardHtml = '';
  if (ev.awards && ev.awards.length) {{
    awardHtml = '<div class="review-section"><h3>🏆 获奖名单</h3>';
    ev.awards.forEach(a => {{
      awardHtml += `<div class="award-category">${{esc(a.category)}}（${{a.works.length}} 部/人）</div><table class="award-table"><tr><th>作品/作者</th><th>作者</th></tr>`;
      a.works.forEach(w => {{
        if (w.title) awardHtml += `<tr><td>${{esc(w.title)}}</td><td>${{esc(w.author)}}</td></tr>`;
        else awardHtml += `<tr><td colspan="2">${{esc(w.author)}}</td></tr>`;
      }});
      awardHtml += '</table>';
    }});
    awardHtml += '</div>';
  }}
  openReview(ev.name, catLine, reviewHtml(ev.name, ev.category, ev.review) + awardHtml);
}}

function openEntity(cat, key) {{
  // key 可以是序号索引，也可以是文件名
  const list = DATA.categories[cat] || [];
  let it = null;
  if (typeof key === 'string') {{
    it = list.find(x => x.file === key) || null;
  }} else {{
    it = list[key] || null;
  }}
  if (!it) return;
  const catLine = '[' + cat + '] · ' + (it.src_count || 0) + ' 条来源' + (it.min_pd ? ' · ' + it.min_pd + ' ~ ' + it.max_pd : '');
  const tagsHtml = (it.tags || []).map(t => '<span class="ei-tag">' + esc(t) + '</span>').join(' ');
  let h = '<div class="review-section" style="margin-bottom:6px;">' + tagsHtml + '</div>';
  h += '<div class="review-section"><h3>📌 简介</h3><div class="review-overview">' + esc(it.desc || '暂无简介') + '</div></div>';
  // 时间线
  const tl = it.timeline || [];
  if (tl.length) {{
    h += '<div class="review-section"><h3>🕒 关键时间线</h3>';
    tl.slice(0, 30).forEach(t => {{
      h += `<div class="tl-item"><div class="tl-date">${{esc(t.date)}}</div><div class="tl-text">${{esc(t.text)}}</div></div>`;
    }});
    h += '</div>';
  }}
  // 来源
  const srcs = it.sources || [];
  if (srcs.length) {{
    h += '<div class="review-section"><h3>📄 信息来源清单（' + srcs.length + ' 条）</h3>';
    srcs.forEach(s => {{
      h += `<div class="src-item"><span class="src-date">${{esc(s.pubdate || '')}}</span><a class="src-url" href="${{esc(s.url)}}" target="_blank" rel="noopener">${{esc(s.url)}}</a></div>`;
    }});
    h += '</div>';
  }}
  // 关联
  const rel = it.related || [];
  if (rel.length) {{
    h += '<div class="review-section"><h3>🔗 相关链接</h3><div class="rel-grid">';
    rel.slice(0, 24).forEach(x => {{
      h += `<div class="rel-chip">${{esc(x)}}</div>`;
    }});
    h += '</div></div>';
  }}
  openReview(it.name, catLine, h);
}}

// Esc 键关闭面板
document.addEventListener('keydown', e => {{
  if (e.key === 'Escape') {{ closeSearch(); closeReview(); }}
}});

// ── 视图切换 ──
document.querySelectorAll('.view-btns button').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.view-btns button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    currentView = btn.dataset.view;
    document.getElementById('yearControls').style.display = currentView === 'year' ? 'inline-block' : 'none';
    document.getElementById('customControls').style.display = currentView === 'custom' ? 'inline-flex' : 'none';
    render();
  }});
}});
document.getElementById('yearSelect').addEventListener('change', e => {{
  currentYear = e.target.value;
  render();
}});
function applyCustomRange() {{
  customFrom = document.getElementById('fromYear').value;
  customTo = document.getElementById('toYear').value;
  render();
}}

// ── 关系图谱（力导向图） ──
const graphCanvas = document.getElementById('graphCanvas');
const gctx = graphCanvas.getContext('2d');
const graphTooltip = document.getElementById('graphTooltip');
let activeCat = null;       // null=全部, 或分类名
let minDegree = 1;          // 最小度数过滤
let gNodes = [], gEdges = [];
let gSim = null;
let graphScale = 1;
let graphTranslate = {{x: 0, y: 0}};
let dragging = false, dragStart = null;

// 初始化图谱
function initGraph() {{
  const allNodes = DATA.graph.nodes;
  const allEdges = DATA.graph.edges;
  // 过滤节点 & 边（按分类和最低关联度）
  const filteredIdSet = new Set();
  allNodes.forEach(n => {{
    if (activeCat && n.cat !== activeCat) return;
    if (n.degree < minDegree) return;
    filteredIdSet.add(n.id);
  }});
  gNodes = allNodes.filter(n => filteredIdSet.has(n.id));
  gEdges = allEdges.filter(e => filteredIdSet.has(e.source) && filteredIdSet.has(e.target));

  // 自动提高阈值避免卡顿
  const MAX_RENDER = 1600;
  while (gNodes.length > MAX_RENDER && minDegree < 12) {{
    minDegree++;
    filteredIdSet.clear();
    allNodes.forEach(n => {{
      if (activeCat && n.cat !== activeCat) return;
      if (n.degree < minDegree) return;
      filteredIdSet.add(n.id);
    }});
    gNodes = allNodes.filter(n => filteredIdSet.has(n.id));
    gEdges = allEdges.filter(e => filteredIdSet.has(e.source) && filteredIdSet.has(e.target));
  }}

  // 圆形初始布局
  gSim = gNodes.map((n, i) => {{
    const angle = (2 * Math.PI * i) / Math.max(gNodes.length, 1);
    const r = Math.sqrt(gNodes.length) * 20;
    return {{ ...n, x: r * Math.cos(angle), y: r * Math.sin(angle), vx: 0, vy: 0 }};
  }});
  posMapCache = null;
  gSim.forEach(n => {{
    n.x += (Math.random() - 0.5) * 40;
    n.y += (Math.random() - 0.5) * 40;
  }});

  graphScale = 1;
  graphTranslate = {{x: 0, y: 0}};
  renderGraphToolbar();
  drawGraph();
  requestAnimationFrame(() => {{ graphStep(120); }});
}}

function renderGraphToolbar() {{
  const toolbar = document.getElementById('graphToolbar');
  const cats = Object.keys(DATA.graph.cat_colors);
  let html = `<label style="font-size:12px;color:#90a4ae;">分类：</label>`;
  html += `<button class="cat-btn ${{!activeCat ? 'active' : ''}}" data-cat="" onclick="setCat('')">全部</button>`;
  cats.forEach(c => {{
    const color = DATA.graph.cat_colors[c];
    html += `<button class="cat-btn ${{activeCat === c ? 'active' : ''}}" data-cat="${{c}}" style="--c:${{color}}" onclick="setCat('${{c}}')">${{c}}</button>`;
  }});
  html += `<label style="font-size:12px;color:#90a4ae;margin-left:10px;">最低关联度：</label>`;
  html += `<input type="range" min="1" max="12" value="${{minDegree}}" oninput="this.nextElementSibling.textContent=this.value;setMinDegree(+this.value)">`;
  html += `<span style="font-size:12px;color:#90a4ae;">${{minDegree}}</span>`;
  html += `<span class="graph-info">${{gNodes.length}} 节点 · ${{gEdges.length}} 边 · 拖动查看</span>`;
  toolbar.innerHTML = html;
}}

function setCat(c) {{
  activeCat = c || null;
  initGraph();
}}

function setMinDegree(d) {{
  minDegree = d;
  initGraph();
}}

// 力导向模拟（固定迭代次数后停止）
function graphStep(steps) {{
  if (!gSim.length) {{ drawGraph(); return; }}
  const reps = steps || 4;
  let posMap = null;
  const buildPos = () => {{
    if (!posMap) {{
      posMap = {{}};
      gSim.forEach(n => posMap[n.id] = n);
    }}
    return posMap;
  }};
  for (let iter = 0; iter < reps; iter++) {{
    const pm = buildPos();
    // 斥力（所有节点对）
    for (let i = 0; i < gSim.length; i++) {{
      for (let j = i + 1; j < gSim.length; j++) {{
        const a = gSim[i], b = gSim[j];
        let dx = b.x - a.x, dy = b.y - a.y;
        let d2 = dx * dx + dy * dy;
        if (d2 < 1) d2 = 1;
        const d = Math.sqrt(d2);
        const force = 4000 / d2;
        const f = Math.min(force, 10);
        const fx = (dx / d) * f, fy = (dy / d) * f;
        a.vx -= fx; a.vy -= fy;
        b.vx += fx; b.vy += fy;
      }}
    }}
    // 引力（弹簧）
    const k = 0.02;
    gEdges.forEach(e => {{
      const a = pm[e.source], b = pm[e.target];
      if (!a || !b) return;
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.sqrt(dx * dx + dy * dy) || 1;
      const targetDist = 45;
      const f = (d - targetDist) * k;
      const fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }});
    // 更新位置
    gSim.forEach(n => {{
      n.vx *= 0.85; n.vy *= 0.85;
      n.x += n.vx; n.y += n.vy;
    }});
  }}
  drawGraph();
}}

let posMapCache = null;
function posMapGet(id) {{
  if (!posMapCache) {{
    posMapCache = {{}};
    gSim.forEach(n => posMapCache[n.id] = n);
  }}
  return posMapCache[id];
}}

// 绘制
function drawGraph() {{
  const W = graphCanvas.width, H = graphCanvas.height;
  if (!W || !H || !gSim || !gSim.length) return;
  gctx.clearRect(0, 0, W, H);

  gctx.save();
  gctx.translate(W / 2 + graphTranslate.x, H / 2 + graphTranslate.y);
  gctx.scale(graphScale, graphScale);

  // 边
  gctx.strokeStyle = 'rgba(120, 130, 180, 0.25)';
  gctx.lineWidth = 1;
  gEdges.forEach(e => {{
    const a = posMapGet(e.source), b = posMapGet(e.target);
    if (!a || !b) return;
    gctx.beginPath();
    gctx.moveTo(a.x, a.y);
    gctx.lineTo(b.x, b.y);
    gctx.stroke();
  }});

  // 节点
  const maxDeg = Math.max(...gSim.map(n => n.degree), 1);
  gSim.forEach(n => {{
    const area = 6 + (n.degree / maxDeg) * 22;
    gctx.beginPath();
    gctx.arc(n.x, n.y, Math.sqrt(area * 2.5), 0, Math.PI * 2);
    gctx.fillStyle = n.color;
    gctx.globalAlpha = 0.85;
    gctx.fill();
    gctx.globalAlpha = 1;
  }});

  gctx.restore();
}}

// 交互：缩放（滚轮）
graphCanvas.addEventListener('wheel', e => {{
  e.preventDefault();
  const delta = e.deltaY > 0 ? 0.9 : 1.1;
  graphScale = Math.max(0.2, Math.min(5, graphScale * delta));
  drawGraph();
}}, {{passive: false}});

// 交互：拖拽平移
graphCanvas.addEventListener('mousedown', e => {{
  dragging = true;
  dragStart = {{x: e.clientX, y: e.clientY}};
  graphCanvas.style.cursor = 'grabbing';
}});
window.addEventListener('mousemove', e => {{
  if (dragging) {{
    graphTranslate.x += e.clientX - dragStart.x;
    graphTranslate.y += e.clientY - dragStart.y;
    dragStart = {{x: e.clientX, y: e.clientY}};
    drawGraph();
  }}
}});
window.addEventListener('mouseup', () => {{ dragging = false; graphCanvas.style.cursor = 'grab'; }});

// 交互：悬停提示
graphCanvas.addEventListener('mousemove', e => {{
  if (dragging) return;
  const rect = graphCanvas.getBoundingClientRect();
  const mx = e.clientX - rect.left, my = e.clientY - rect.top;
  const cx = (mx - rect.width / 2 - graphTranslate.x) / graphScale;
  const cy = (my - rect.height / 2 - graphTranslate.y) / graphScale;
  const maxDeg = Math.max(...gSim.map(n => n.degree), 1);
  let hit = null, hitDist = 1e9;
  gSim.forEach(n => {{
    const d = Math.hypot(n.x - cx, n.y - cy);
    const r = Math.sqrt((6 + (n.degree / maxDeg) * 22) * 2.5);
    if (d < r * 1.4 && d < hitDist) {{ hit = n; hitDist = d; }}
  }});
  if (hit) {{
    graphTooltip.style.display = 'block';
    graphTooltip.style.left = (e.clientX - rect.left + 14) + 'px';
    graphTooltip.style.top = (e.clientY - rect.top + 14) + 'px';
    graphTooltip.innerHTML = `<div class="tt-name">${{esc(hit.name)}}</div>` +
      `<div class="tt-cat">${{esc(hit.cat)}} · ${{hit.src_count}} 条来源</div>` +
      `<div class="tt-deg">关联度 ${{hit.degree}} · ${{hit.id}}</div>`;
  }} else {{
    graphTooltip.style.display = 'none';
  }}
}});
graphCanvas.addEventListener('mouseleave', () => {{ graphTooltip.style.display = 'none'; }});

// 画布尺寸自适应
function sizeGraphCanvas() {{
  const rect = graphCanvas.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  if (graphCanvas.width !== Math.round(rect.width * dpr) || graphCanvas.height !== Math.round(rect.height * dpr)) {{
    graphCanvas.width = Math.round(rect.width * dpr);
    graphCanvas.height = Math.round(rect.height * dpr);
    gctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    drawGraph();
  }}
}}
window.addEventListener('resize', sizeGraphCanvas);

// ── 初始渲染 ──
render();
renderCatNav();
sizeGraphCanvas();
initGraph();
</script>
</body>
</html>"""


# ── 构建 JSON 数据并生成 HTML ────────────────────────────────────────
data_json = {
    "stats": stats,
    "phenomena": [{
        "name": p["name"],
        "category": p["category"],
        "color": p["color"],
        "description": p["description"],
        "wiki": p["wiki"],
        "source_count": p["source_count"],
        "page_count": p["page_count"],
        "min_pd": p["min_pd"],
        "max_pd": p["max_pd"],
        "review": p.get("review"),
    } for p in PHENOMENA],
    "events": [{
        "name": e["name"],
        "date": e["date"],
        "category": e["category"],
        "source_count": e["source_count"],
        "description": e["description"],
        "awards": e["awards"],
        "wiki": e["wiki"],
        "score": e["score"],
        "review": e.get("review"),
    } for e in BIG_EVENTS],
    "categories": categories,
    "graph": {
        "nodes": [{
            "id": n["id"],
            "name": n["name"],
            "cat": n["cat"],
            "src_count": n["src_count"],
            "degree": n["degree"],
            "color": CATEGORY_COLORS.get(n["cat"], "#90a4ae"),
        } for n in graph_nodes.values()],
        "edges": graph_edges,
        "cat_colors": CATEGORY_COLORS,
    },
}

html_content = gen_html(data_json)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html_content, encoding="utf-8")
print(f"驾驶舱已生成: {OUT}")
print(f"  Wiki 页面: {stats['total_pages']}")
print(f"  原始文档: {stats['total_raw']}")
print(f"  重要现象: {len(PHENOMENA)} 项")
print(f"  大事记: {len(BIG_EVENTS)} 条")
print(f"  年份覆盖: {', '.join(sorted(stats['by_year'].keys()))}")
