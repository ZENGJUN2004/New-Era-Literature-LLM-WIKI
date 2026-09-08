import json
from pathlib import Path
from datetime import datetime, timedelta

BASE = Path(r'd:\zjun\新时代文学LLMWIKI\raw\json')
DATE_FMT = '%Y-%m-%d'

# Check 05-01 ~ 05-25
target_set = set()
d = datetime.strptime('2026-05-01', DATE_FMT)
end_d = datetime.strptime('2026-05-25', DATE_FMT)
while d <= end_d:
    target_set.add(d.strftime(DATE_FMT))
    d += timedelta(days=1)

found = {ds: 0 for ds in sorted(target_set)}
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
            found[ds] += 1
            break

missing = [ds for ds, cnt in found.items() if cnt == 0]
has_data = [ds for ds, cnt in found.items() if cnt > 0]
print(f'05-01~05-25: {len(has_data)} days with data, {len(missing)} missing')
print(f'Missing: {missing}')
print(f'Has data: {has_data}')
