# 新时代文学 LLM Wiki — 可移植运行包

本目录包含「新时代文学 LLM wiki」项目当前完整运行依赖，可直接拷贝到其他电脑使用。

## 目录结构

```
新时代文学LLMWIKI/
├── AGENTS.md            ← Schema 层：采集规则、wiki 规范、每日同步机制
├── index.md             ← 知识页面索引（AI ingest 后自动维护）
├── log.md               ← 变动日志
├── scripts/
│   ├── fetch_api.py     ← 中国作家网检索 API 采集（含限速 + 退避）
│   ├── raw_to_md.py     ← raw/json → markdown 转换
│   ├── gen_ingest_task.py  ← 生成 LLM ingest 任务清单
│   ├── daily_sync.py    ← 一日流水：采集 → 转 md → 生成任务 → 记 log
│   ├── lint_wiki.py     ← 纠错与整理（死链/孤儿/索引不一致/frontmatter 校验等）
│   └── build_wiki.py    ← 自动化 ingest（启发式，复杂内容仍建议 LLM 人工处理）
├── tasks/
│   └── ingest_YYYYMMDD.md   ← 由 gen_ingest_task.py 生成，供 LLM ingest
├── raw/
│   ├── json/                  ← 原始采集结果（Source of Truth，永不修改）
│   └── markdown/
│       └── YYYY/              ← 可读版，命名含日期（YYYY-MM-DD_id.md）
└── wiki/
    ├── 人物/
    ├── 作品/
    ├── 主题/
    ├── 概念/
    ├── 流派/
    ├── 机构/
    ├── 事件/
    └── 时间线/
```

## 前置依赖

- Python ≥ 3.9（标准库即可，无需额外 pip install）
- 网络访问权限（采集目标：`search.people.cn/search-platform/front/searchByType`）

## 常用命令

```bash
cd 新时代文学LLMWIKI

# 每日同步（含采集 + 转 md + 生成待 ingest 清单 + 记 log）
python scripts/daily_sync.py --key 文学 --date 2026-09-06

# 回溯采集多日（单关键词，单日单任务，严守 3~8s 间隔）
python scripts/daily_sync.py --key 文学 --days-back 1   # 仅昨日
python scripts/daily_sync.py --key 文学 --days-back 3   # 近 3 日

# 独立生成待 ingest 清单（ ingest 完成后重跑可发现新遗留）
python scripts/gen_ingest_task.py

# 纠错与整理
python scripts/lint_wiki.py          # 仅报告
python scripts/lint_wiki.py --fix    # 报告 + 自动修复安全项

# 自动 ingest（启发式，适合结构清晰新闻；复杂内容建议人工 ingest）
python scripts/build_wiki.py
```

## 反爬纪律（内置，不可调松）

- 每次请求前随机等待 3~8 秒（`fetch_api.MIN_DELAY`/`MAX_DELAY`）
- 每分钟请求数上限 10 次（`DEFAULT_RPM`）
- 单页失败指数退避重试 3 次（基数 10s/20s/40s），超限跳过
- 大批量请按 `--days-back 1` 切片执行，勿一次性灌满
- 脚本日志以 `[rate] 已达每分钟 10 次上限` 提示限速

## 数据流

```
raw/searchByType API
        │
        ▼
fetch_api.py  ──→  raw/json/<id>.json   （Source of Truth）
        │
        ▼
raw_to_md.py  ──→  raw/markdown/YYYY/YYYY-MM-DD_<id>.md
        │
        ▼
gen_ingest_task.py  ──→  tasks/ingest_YYYYMMDD.md   （待 LLM 处理清单）
        │
        ▼
LLM ingest / build_wiki.py  ──→  wiki/*.md  +  index.md + log.md
        │
        ▼
lint_wiki.py  ──→  纠错与整理
```

## 权限说明

- 所有采集均来自中国作家网公开检索 API，无需登录；如网站变更接口，需更新 `fetch_api.py` 中的 `API_URL`、`DOMAIN` 与 UA 字段。
- 期刊转载与会员投稿作品仅作元数据索引，正文二次利用需另行确认授权。

## 维护人

Agnes（Sapiens AI），基于 AGENTS.md Schema 层规范运行。
