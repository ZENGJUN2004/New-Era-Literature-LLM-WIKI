import json
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
DATE_FMT = '%Y-%m-%d'

# Check all months
months = []
for m in range(1, 10):
    for d in range(1, 32):
        try:
            ds = f'2026-{m:02d}-{d:02d}'
            datetime.strptime(ds, DATE_FMT)
        except ValueError:
            continue
        if ds > '2026-09-08':
            break
        months.append(ds)

found_by_date = {ds: 0 for ds in months}
for f in BASE.glob('*.json'):
    try:
        with open(f, 'r', encoding='utf-8') as fh:
            data = json.load(fh)
    except Exception:
        continue
    q = data.get('_query', {})
    start = q.get('start', '')[:10]
    end_q = q.get('end', '')[:10]
    for ds in months:
        if start <= ds <= end_q:
            found_by_date[ds] += 1
            break

missing = [ds for ds, cnt in found_by_date.items() if cnt == 0]
total_missing = len(missing)
print(f'Total missing days: {total_missing}')
for ds in sorted(missing):
    print(f'  {ds}')
