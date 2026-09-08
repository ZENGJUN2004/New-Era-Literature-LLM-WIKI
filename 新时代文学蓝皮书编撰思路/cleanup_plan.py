# -*- coding: utf-8 -*-
import re, docx
from docx.oxml.ns import qn

PATH = r"D:\zjun\新时代文学LLMWIKI\新时代文学蓝皮书编撰思路\新时代文学蓝皮书编撰方案（问题与解决方案）.docx"

doc = docx.Document(PATH)

# 1) 移除所有内联的【...】来源标记（保留各 run 的字体格式）
for p in doc.paragraphs:
    for run in p.runs:
        if '【' in run.text:
            run.text = re.sub(r'【[^】]*】', '', run.text).strip()
            # 清理可能残留的多个连续空格
            run.text = re.sub(r'\s{2,}', ' ', run.text)

# 2) 删除整段"依据：..."（纯来源说明）以及编制说明中的元注释
to_delete = []
for p in doc.paragraphs:
    txt = p.text.strip()
    if txt.startswith('依据：'):
        to_delete.append(p)
    if '凡方案中标注' in txt:
        to_delete.append(p)

for p in to_delete:
    el = p._element
    el.getparent().remove(el)

# 3) 清理因删除/替换产生的空段落（仅当段落完全为空且无图片等）
empties = [p for p in doc.paragraphs if p.text.strip() == '']
for p in empties:
    # 不删除表格内的；只删正文层空段，且保留段落节点本身以免破坏结构——这里仅跳过
    pass

doc.save(PATH)
print("清理完成。剩余段落数:", len(doc.paragraphs))

# 校验：是否还有【标记
left = [p.text for p in doc.paragraphs if '【' in p.text or p.text.strip().startswith('依据：')]
print("残留来源标记/依据行数:", len(left))
for x in left[:10]:
    print("  -", x[:60])
