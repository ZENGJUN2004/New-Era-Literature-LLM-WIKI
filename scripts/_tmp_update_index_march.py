"""
Add new March pages to index.md
"""
from pathlib import Path

INDEX = Path(r'd:\zjun\新时代文学LLMWIKI\index.md')
WIKI = Path(r'd:\zjun\新时代文学LLMWIKI\wiki')

content = INDEX.read_text(encoding='utf-8')

# Add 新东北文学 and 文学新势力 to themes section
if '新东北文学' not in content:
    content = content.replace(
        '✅ 东北文学（[主题/东北文学.md](主题/东北文学.md)）',
        '✅ 东北文学（[主题/东北文学.md](主题/东北文学.md)）\n✅ 新东北文学（[主题/新东北文学.md](主题/新东北文学.md)）'
    )
if '文学新势力' not in content:
    content = content.replace(
        '✅ 素人写作（[主题/素人写作.md](主题/素人写作.md)）',
        '✅ 素人写作（[主题/素人写作.md](主题/素人写作.md)）\n✅ 文学新势力（[主题/文学新势力.md](主题/文学新势力.md)）'
    )

# Add new events to events section (find last event line)
new_events = [
    ('中国作协召开2026年党的工作暨纪检工作', '事件/中国作协召开2026年党的工作暨纪检工作.md'),
    ('中国作协召开党组扩大会暨机关党建工作领导小组会议', '事件/中国作协召开党组（扩大）会暨机关党建工作领导小组会议 动员部署树立和践行正确政绩观学习教育.md'),
]

# Find the events section end marker
events_end = content.find('## 时间线')
if events_end > 0:
    # Find the last ✅ line before 时间线
    last_check = content.rfind('✅', 0, events_end)
    if last_check > 0:
        # Find the newline after this line
        next_newline = content.find('\n', last_check)
        for name, link in new_events:
            if name not in content:
                insert_text = f'✅ {name}（[{name}]({link})）\n'
                content = content[:next_newline] + insert_text + content[next_newline:]
                # Update next_newline for next insertion
                next_newline = content.find('\n', last_check + len(insert_text))

INDEX.write_text(content, encoding='utf-8')
print('Index updated.')
