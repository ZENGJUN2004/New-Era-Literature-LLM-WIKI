import json, os
from pathlib import Path

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
DATE_FMT = '%Y-%m-%d'
START = '2026-02-21'
END   = '2026-02-28'

target_set = set()
from datetime import datetime, timedelta
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
            title = data.get('title', f)
            found_by_date[ds].append((f.name, title[:50]))
            break

print(f'Dates {START} to {END}:')
total = 0
for ds in sorted(found_by_date.keys()):
    items = found_by_date[ds]
    total += len(items)
    print(f'  {ds}: {len(items)} articles')
    for fname, title in items[:3]:
        print(f'    - {title}')
    if len(items) > 3:
        print(f'    ... and {len(items)-3} more')
print(f'Total: {total}')
