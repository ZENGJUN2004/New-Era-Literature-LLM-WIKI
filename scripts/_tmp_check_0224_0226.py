import json, os
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
WIKI = Path(r'd:\zjun\新时代文学LLMWIKI\wiki')
LOG  = Path(r'd:\zjun\新时代文学LLMWIKI\log.md')
INDEX = Path(r'd:\zjun\新时代文学LLMWIKI\index.md')
DATE_FMT = '%Y-%m-%d'

START = '2026-02-24'
END   = '2026-02-26'

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
                'content': content[:500],
            })
            break

for ds in sorted(found_by_date.keys()):
    items = found_by_date[ds]
    print(f'\n=== {ds} ({len(items)} articles) ===')
    for i, item in enumerate(items):
        print(f'  [{i+1}] {item["title"][:60]}')
        print(f'      source={item["source"]} | {item["url"]}')
        # Print first 200 chars of content for analysis
        ct = item['content'][:300].replace('\n', ' ')
        print(f'      content: {ct}')

# Save manifest for manual ingest script
import pickle
with open(r'd:\zjun\新时代文学LLMWIKI\scripts\_tmp_manifest_0224_0226.pkl', 'wb') as pf:
    pickle.dump(found_by_date, pf)
print('\nManifest saved.')
