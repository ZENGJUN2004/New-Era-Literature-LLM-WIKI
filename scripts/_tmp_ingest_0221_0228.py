"""
Ingest batch: 2026-02-21 ~ 2026-02-28
Strategy: most articles are journal contents / light processing;
only create pages for genuinely new people/events/themes.
"""
import json, os, re
from pathlib import Path
from datetime import datetime, timedelta

def clean_filename(s):
    """Remove HTML tags and invalid filename chars."""
    s = re.sub(r'<em[^>]*>', '', s)
    s = re.sub(r'</em>', '', s)
    s = re.sub(r'[\\/:*?"<>|]', '', s)
    return s.strip()

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
WIKI = Path(r'd:\zjun\新时代文学LLMWIKI\wiki')
LOG  = Path(r'd:\zjun\新时代文学LLMWIKI\log.md')
INDEX = Path(r'd:\zjun\新时代文学LLMWIKI\index.md')
DATE_FMT = '%Y-%m-%d'

START = '2026-02-21'
END   = '2026-02-28'

# Collect all relevant raw files
target_set = set()
d = datetime.strptime(START, DATE_FMT)
end_d = datetime.strptime(END, DATE_FMT)
while d <= end_d:
    target_set.add(d.strftime(DATE_FMT))
    d += timedelta(days=1)

articles = []
for f in BASE.glob('*.json'):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        continue
    q = data.get('_query', {})
    start = q.get('start', '')[:10]
    end_q = q.get('end', '')[:10]
    for ds in target_set:
        if start <= ds <= end_q:
            articles.append(data)
            break

# Deduplicate by url
seen_urls = set()
unique = []
for a in articles:
    url = a.get('url', '')
    if url and url not in seen_urls:
        seen_urls.add(url)
        unique.append(a)
articles = unique

print(f'Total unique articles: {len(articles)}')

# Categorize
new_people = []
new_events = []
new_themes = []
light_count = 0

for a in articles:
    title = a.get('title', '')
    url = a.get('url', '')
    pubdate = a.get('publishTime', '')[:10]
    source = a.get('sourceName', '')
    content = a.get('content', '') or ''

    # Detect if it's a journal issue notice (catalog)
    if re.search(r'《\w+文学》\d{4}年第\d+期[｜|]', title):
        light_count += 1
        continue
    if '目录' in title and '文学' in title:
        light_count += 1
        continue

    # Detect person interviews / profiles
    if '访谈' in title and any(kw in title for kw in ['作家', '文学', '对话', '记']):
        # Could be a person page
        person_match = re.search(r'（(.+?)）', title)
        if person_match:
            name = person_match.group(1).strip()
            new_people.append({'name': name, 'title': title, 'url': url, 'pubdate': pubdate, 'source': source})
            continue

    # Detect new events
    if any(kw in title for kw in ['大会', '会议', '成立', '评选', '揭晓', '颁奖', '发布']):
        new_events.append({'title': title, 'url': url, 'pubdate': pubdate, 'source': source})
        continue

    # Detect themes/topics
    if any(kw in title for kw in ['新东北文学', '大文学观', '新大众文艺', '素人写作', '文学新势力']):
        new_themes.append({'title': title, 'url': url, 'pubdate': pubdate, 'source': source})
        continue

    # Default: light processing
    light_count += 1

print(f'New people candidates: {len(new_people)}')
print(f'New event candidates: {len(new_events)}')
print(f'New theme candidates: {len(new_themes)}')
print(f'Light processing: {light_count}')

# Create person pages
created_pages = []
for p in new_people:
    name = p['name']
    page_path = WIKI / '人物' / f'{name}.md'
    if page_path.exists():
        print(f'  SKIP (exists): {name}')
        continue
    today = datetime.now().strftime(DATE_FMT)
    page_content = f'''---
type: 人物
name: {name}
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

# {name}

<!-- 概述：待补充 -->

## 关键信息
- **身份**：作家
- **时间线**：
  - **{p['pubdate']}**：接受访谈/报道，来源：[{p['title']}]({p['url']})

## 详细内容
待从原始素材中提炼。

## 关联
待补充

## 来源
- [{p['title']}]({p['url']})＠ {p['pubdate']}
'''
    WIKI.mkdir(parents=True, exist_ok=True)
    (WIKI / '人物').mkdir(parents=True, exist_ok=True)
    page_path.write_text(page_content, encoding='utf-8')
    created_pages.append(f'人物/{name}.md')
    print(f'  CREATED: {name}')

# Create event pages for notable ones
for e in new_events:
    # Parse event name from title
    title = e['title']
    # Remove common suffixes
    event_name = re.sub(r'(评选启事|大会|会议)$', '', title).strip()
    if not event_name or len(event_name) < 3:
        event_name = title
    event_name = clean_filename(event_name)
    # Further clean: remove any remaining HTML tags
    event_name = re.sub(r'<[^>]+>', '', event_name).strip()
    page_path = WIKI / '事件' / f'{event_name}.md'
    if page_path.exists():
        print(f'  SKIP event (exists): {event_name}')
        continue
    # Only create for significant events (not just notices)
    if '启事' in title or '征集' in title:
        light_count += 1
        continue
    today = datetime.now().strftime(DATE_FMT)
    page_content = f'''---
type: 事件
name: {event_name}
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

# {event_name}

## 关键信息
- **时间**：{e['pubdate']}
- **来源**：[{title}]({e['url']})

## 详细内容
待从原始素材中提炼。

## 关联
待补充

## 来源
- [{title}]({e['url']})＠ {e['pubdate']}
'''
    (WIKI / '事件').mkdir(parents=True, exist_ok=True)
    page_path.write_text(page_content, encoding='utf-8')
    created_pages.append(f'事件/{event_name}.md')
    print(f'  CREATED EVENT: {event_name}')

# Create theme pages
for t in new_themes:
    title = t['title']
    # Extract theme name
    if '新东北文学' in title:
        theme_name = '新东北文学'
    elif '大文学观' in title:
        theme_name = '大文学观'
    elif '新大众文艺' in title:
        theme_name = '新大众文艺'
    elif '素人写作' in title:
        theme_name = '素人写作'
    elif '文学新势力' in title:
        theme_name = '文学新势力'
    else:
        theme_name = clean_filename(title[:20])
    page_path = WIKI / '主题' / f'{theme_name}.md'
    if page_path.exists():
        print(f'  SKIP theme (exists): {theme_name}')
        continue
    today = datetime.now().strftime(DATE_FMT)
    page_content = f'''---
type: 主题
name: {theme_name}
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

# {theme_name}

## 关键信息
- **首次提及**：{t['pubdate']}
- **来源**：[{title}]({t['url']})

## 详细内容
待从原始素材中提炼。

## 关联
待补充

## 来源
- [{title}]({t['url']})＠ {t['pubdate']}
'''
    (WIKI / '主题').mkdir(parents=True, exist_ok=True)
    page_path.write_text(page_content, encoding='utf-8')
    created_pages.append(f'主题/{theme_name}.md')
    print(f'  CREATED THEME: {theme_name}')

# Count wiki and raw
wiki_count = sum(1 for _ in WIKI.rglob('*.md'))
raw_count = len(list(BASE.glob('*.json')))

# Update log
log_entry = f"""
## 2026-09-08 补采 02-21~02-28
- 【Sync】补采 2026-02-21~02-28，新增 raw {len(articles)} 篇
- 【Ingest】批量处理 {len(articles)} 篇，其中轻处理 {light_count} 篇（期刊目录/通知等）
- 【Create】新建页面 {len(created_pages)} 个：{', '.join(created_pages)}
- 【Stats】wiki={wiki_count}, raw={raw_count}
"""
with open(LOG, 'a', encoding='utf-8') as f:
    f.write(log_entry)
print(f'\nLog updated.')
print(f'Wiki count: {wiki_count}')
print(f'Raw count: {raw_count}')
print(f'Created pages: {created_pages}')
