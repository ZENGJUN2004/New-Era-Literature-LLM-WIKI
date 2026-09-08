# -*- coding: utf-8 -*-
import io, os, glob
d = r"d:\zjun\新时代文学LLMWIKI\raw\markdown\2026"
fs = sorted(glob.glob(os.path.join(d, "2026-01-26_*.md")))
for f in fs:
    with io.open(f, 'r', encoding='utf-8') as fh:
        head = fh.read(700)
    lines = head.split('\n')
    title = ''
    for ln in lines[:20]:
        if ln.startswith('# ') and not title:
            title = ln[2:].strip()
    print("%s | %s" % (os.path.basename(f)[-20:-3], title[:70]))
