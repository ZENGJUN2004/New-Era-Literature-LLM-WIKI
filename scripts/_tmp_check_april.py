import json, os
from pathlib import Path
from datetime import datetime, timedelta
import pickle

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
DATE_FMT = '%Y-%m-%d'
START = '2026-04-01'
END   = '2026-04-30'

target_set = set()
d = datetime.strptime(START, DATE_FMT)
end_d = datetime.strptime(END, DATE_FMT)
while d <= end_d:
    target_set.add(d.strftime(DATE_FMT))
    d += timedelta(days=1)

found_by_date = {ds: [] for ds in sorted(target_set)}

for f in BASE.glob('*.json'):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        continue
    q = data.get('_query', {})
    start = q.get('start', '')[:10]
    end_q = q.get('end', '')[:10]
    for ds in sorted(target_set):
        if start <= ds <= end_q:
            title = data.get('title', '')
            url = data.get('url', '')
            pubdate = data.get('publishTime', '')[:10]
            source = data.get('sourceName', '')
            content = data.get('content', '') or ''
            found_by_date[ds].append({
                'file': f.name,
                'title': title,
                'url': url,
                'pubdate': pubdate,
                'source': source,
                'content': content[:300],
            })
            break

total = 0
for ds in sorted(found_by_date.keys()):
    items = found_by_date[ds]
    total += len(items)
    if items:
        print(f'  {ds}: {len(items)} articles')

print(f'\nApril total: {total} articles across {sum(1 for v in found_by_date.values() if v)} days')

all_articles = []
seen_urls = set()
for ds in sorted(found_by_date.keys()):
    for item in found_by_date[ds]:
        if item['url'] not in seen_urls:
            seen_urls.add(item['url'])
            all_articles.append(item)

with open(r'd:\zjun\新时代文学LLMWIKI\scripts\_tmp_manifest_april.pkl', 'wb') as pf:
    pickle.dump(all_articles, pf)
print(f'Unique articles: {len(all_articles)}')
print('Manifest saved.')
