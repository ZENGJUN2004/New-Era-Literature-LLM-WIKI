"""
Ingest March 2026: 389 unique articles
Strategy: light processing for journals/catalogs/notices;
create pages only for new people/events/themes.
"""
import json, os, re, pickle
from pathlib import Path
from datetime import datetime

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
WIKI = Path(r'd:\zjun\新时代文学LLMWIKI\wiki')
LOG  = Path(r'd:\zjun\新时代文学LLMWIKI\log.md')
DATE_FMT = '%Y-%m-%d'

def clean_filename(s):
    s = re.sub(r'<em[^>]*>', '', s)
    s = re.sub(r'</em>', '', s)
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    s = re.sub(r'<[^>]+>', '', s)
    return s.strip()

# Load manifest
with open(r'd:\zjun\新时代文学LLMWIKI\scripts\_tmp_manifest_march.pkl', 'rb') as mf:
    articles = pickle.load(mf)

print(f'Total articles to process: {len(articles)}')

# Categorize
new_people = []
new_events = []
new_themes = []
light_count = 0
pages_created = []

for a in articles:
    title = a.get('title', '')
    url = a.get('url', '')
    pubdate = a.get('pubdate', '')
    content = a.get('content', '') or ''

    # Skip journal issue notices
    if re.search(r'《\w+文学》\d{4}年第\d+期[｜|]', title):
        light_count += 1
        continue
    if '目录' in title and '文学' in title:
        light_count += 1
        continue

    # Detect person interviews/profiles
    if '访谈' in title and any(kw in title for kw in ['作家', '文学', '对话', '记', '诗人']):
        person_match = re.search(r'（(.+?)）', title)
        if person_match:
            name = clean_filename(person_match.group(1).strip())
            new_people.append({'name': name, 'title': title, 'url': url, 'pubdate': pubdate})
            continue

    # Detect new events
    if any(kw in title for kw in ['大会', '会议', '成立', '评选', '揭晓', '颁奖', '发布', '座谈会']):
        event_name = re.sub(r'(评选启事|大会|会议|座谈会)$', '', title).strip()
        event_name = clean_filename(event_name)
        if event_name and len(event_name) >= 3 and '启事' not in title and '征集' not in title:
            new_events.append({'name': event_name, 'title': title, 'url': url, 'pubdate': pubdate})
            continue

    # Detect themes/topics
    for kw, theme_name in [('新东北文学', '新东北文学'), ('大文学观', '大文学观'),
                            ('新大众文艺', '新大众文艺'), ('素人写作', '素人写作'),
                            ('文学新势力', '文学新势力')]:
        if kw in title:
            new_themes.append({'name': theme_name, 'title': title, 'url': url, 'pubdate': pubdate})
            break
    else:
        light_count += 1
        continue

print(f'New people: {len(new_people)}, Events: {len(new_events)}, Themes: {len(new_themes)}, Light: {light_count}')

# Create person pages
for p in new_people:
    page_path = WIKI / '人物' / f"{p['name']}.md"
    if page_path.exists():
        continue
    today = datetime.now().strftime(DATE_FMT)
    content = f'''---
type: 人物
name: {p['name']}
aliases: []
created: {today}
updated: {today}
sources:
  - id: raw/json/????.json
    url: {p['url']}
    pubdate: {p['pubdate']}
related: []
tags: [作家]
---

# {p['name']}

## 关键信息
- **时间线**：
  - **{p['pubdate']}**：访谈/报道，来源：[{p['title']}]({p['url']})

## 来源
- [{p['title']}]({p['url']})＠ {p['pubdate']}
'''
    (WIKI / '人物').mkdir(parents=True, exist_ok=True)
    page_path.write_text(content, encoding='utf-8')
    pages_created.append(f'人物/{p["name"]}.md')

# Create event pages
for e in new_events:
    page_path = WIKI / '事件' / f"{e['name']}.md"
    if page_path.exists():
        continue
    today = datetime.now().strftime(DATE_FMT)
    content = f'''---
type: 事件
name: {e['name']}
aliases: []
created: {today}
updated: {today}
sources:
  - id: raw/json/????.json
    url: {e['url']}
    pubdate: {e['pubdate']}
related: []
tags: [事件]
---

# {e['name']}

## 关键信息
- **时间**：{e['pubdate']}
- **来源**：[{e['title']}]({e['url']})

## 来源
- [{e['title']}]({e['url']})＠ {e['pubdate']}
'''
    (WIKI / '事件').mkdir(parents=True, exist_ok=True)
    page_path.write_text(content, encoding='utf-8')
    pages_created.append(f'事件/{e["name"]}.md')

# Create theme pages
for t in new_themes:
    page_path = WIKI / '主题' / f"{t['name']}.md"
    if page_path.exists():
        continue
    today = datetime.now().strftime(DATE_FMT)
    content = f'''---
type: 主题
name: {t['name']}
aliases: []
created: {today}
updated: {today}
sources:
  - id: raw/json/????.json
    url: {t['url']}
    pubdate: {t['pubdate']}
related: []
tags: [主题]
---

# {t['name']}

## 关键信息
- **首次提及**：{t['pubdate']}
- **来源**：[{t['title']}]({t['url']})

## 来源
- [{t['title']}]({t['url']})＠ {t['pubdate']}
'''
    (WIKI / '主题').mkdir(parents=True, exist_ok=True)
    page_path.write_text(content, encoding='utf-8')
    pages_created.append(f'主题/{t["name"]}.md')

# Update log and stats
wiki_count = sum(1 for _ in WIKI.rglob('*.md'))
raw_count = len(list(BASE.glob('*.json')))

log_entry = f"""
## 2026-09-08 补采 03月
- 【Sync】补采 2026-03-01~03-31，新增 raw 389 篇（30天有数据，03-07周日无更新）
- 【Ingest】批量处理 389 篇，轻处理 {light_count} 篇（期刊目录/通知等）
- 【Create】新建页面 {len(pages_created)} 个：{'、'.join(pages_created[:10])}{'...' if len(pages_created)>10 else ''}
- 【Stats】wiki={wiki_count}, raw={raw_count}
"""
with open(LOG, 'a', encoding='utf-8') as f:
    f.write(log_entry)

# Update index stats
idx = Path(r'd:\zjun\新时代文学LLMWIKI\index.md')
content = idx.read_text(encoding='utf-8')
content = re.sub(r'- 知识页面总数：\d+', f'- 知识页面总数：{wiki_count}', content)
content = re.sub(r'- raw 原始文档总数：\d+', f'- raw 原始文档总数：{raw_count}', content)
content = re.sub(r'- 最后更新：\d{4}-\d{2}-\d{2}', '- 最后更新：2026-09-08', content)
idx.write_text(content, encoding='utf-8')

print(f'\nDone. Wiki={wiki_count}, Raw={raw_count}')
print(f'Created: {len(pages_created)} pages')
