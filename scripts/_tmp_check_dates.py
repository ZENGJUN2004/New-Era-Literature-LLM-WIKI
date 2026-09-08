import json
from pathlib import Path
from datetime import date, timedelta
from itertools import groupby

ROOT = Path(r'd:\zjun\新时代文学LLMWIKI')
RAW_JSON = ROOT / 'raw' / 'json'

def extract_dates():
    """Extract dates from _query.start and _query.end fields."""
    dates = set()
    for f in RAW_JSON.glob('*.json'):
        try:
            with open(f, 'r', encoding='utf-8') as fp:
                data = json.load(fp)
            query = data.get('_query', {})
            for key in ['start', 'end']:
                val = query.get(key)
                if isinstance(val, str) and len(val) >= 10:
                    try:
                        d = date.fromisoformat(val[:10])
                        dates.add(d)
                    except:
                        pass
        except:
            pass
    return dates

present = extract_dates()

start = date(2026, 1, 1)
end = date(2026, 9, 8)

missing = []
d = start
while d <= end:
    if d not in present:
        missing.append(d)
    d += timedelta(days=1)

total = len(present) + len(missing)
print(f'Total days in range: {total}')
print(f'Present: {len(present)} days')
print(f'Missing: {len(missing)} days ({len(missing)*100//total}%)')
print()

print('=== Missing dates (by month) ===')
for month, days in groupby(missing, lambda dd: (dd.year, dd.month)):
    day_list = sorted(days)
    mname = f'{month[0]}-{month[1]:02d}'
    print(f'{mname}: {len(day_list)} days')
    runs = []
    cs = ce = day_list[0]
    for dd in day_list[1:]:
        if dd - ce == timedelta(days=1):
            ce = dd
        else:
            runs.append((cs, ce))
            cs = ce = dd
    runs.append((cs, ce))
    for s, e in runs:
        sm = s.strftime('%m-%d')
        em = e.strftime('%m-%d')
        if sm == em:
            print(f'  {sm}')
        else:
            print(f'  {sm} ~ {em}')

print()
print('=== Present dates (by month) ===')
for month, days in groupby(sorted(present), lambda dd: (dd.year, dd.month)):
    day_list = sorted(days)
    mname = f'{month[0]}-{month[1]:02d}'
    fmt1 = day_list[0].strftime('%m-%d')
    fmt2 = day_list[-1].strftime('%m-%d')
    print(f'{mname}: {len(day_list)} days  ({fmt1} ~ {fmt2})')
