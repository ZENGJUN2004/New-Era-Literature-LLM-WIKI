#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
daily_sync.py — 每日同步流水线（采集 → 转换 → 任务清单）
=========================================================
把 fetch_api.py / raw_to_md.py / gen_ingest_task.py 串成一条命令，
用于"中国作家网每日更新 → wiki 增量同步"：

    ① fetch：按关键词 × 精确日期范围增量采集（复用已有的 raw，不重复入库）
    ② raw_to_md：新 json 转 readable Markdown
    ③ gen_task：生成 tasks/ingest_YYYYMMDD.md 待 ingest 清单，交给 LLM 每日处理
    ④ 追加 log.md 记录本次同步

典型用法（Windows 任务计划程序每日定时执行）：
    python scripts/daily_sync.py --key 文学 --date 2026-09-06
    # 若当天未运行，次日自动补采昨天：
    python scripts/daily_sync.py --key 文学 --days-back 1 --auto-fill

反爬纪律（强制）：
- 全程复用同一个 RateLimiter（随机 3~8s 间隔 + 每分钟≤10 次 + 指数退避）
- 单次同步默认只处理 1~2 天，多天用 --days-back 或分批多次运行
"""

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_api            # noqa: E402
import raw_to_md            # noqa: E402
import gen_ingest_task      # noqa: E402

BJT = timezone(timedelta(hours=8))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def date_range(days_back: int) -> list:
    """返回最近 days_back 天的日期串列表（含今天，最新在前）。"""
    today = datetime.now(BJT)
    return [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days_back)]


def sync_one_day(key, date_str, args):
    """对单日执行：采集（增量）→ 转md → 数出新增。返回新增 json 数。"""
    start_ms = fetch_api.to_epoch_ms(date_str)
    end_ms = int((datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=BJT)
                  + timedelta(days=1)).timestamp() * 1000)

    json_dir = os.path.join(ROOT, "raw", "json")
    md_dir = os.path.join(ROOT, "raw", "markdown")

    # 1) 采集（fetch_all 内部已处理限速+退避；limiter 复用全局）
    records = fetch_api.fetch_all(
        key, args.searchType, start_ms, end_ms, args.sortType,
        max_pages=args.max_pages, limiter=args.limiter,
    )
    if not records:
        print(f"  [{date_str}] key={key} 无新结果", file=sys.stderr)
        return 0

    # 2) 转 markdown（仅处理新增 json）
    new_records = fetch_api.save_records(records, json_dir, key, date_str, date_str)
    if not new_records:
        print(f"  [{date_str}] key={key} 均为已有文档，跳过转换", file=sys.stderr)
        return 0
    n_md = 0
    for rec in new_records:
        jf = f"{rec.get('id') or rec.get('contentId') or rec.get('url','').split('/')[-1]}.json"
        with open(os.path.join(json_dir, jf), encoding="utf-8") as f:
            stored = json.load(f)
        dt = stored.get("displayTime")
        year = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y") if dt else "unknown"
        day = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y-%m-%d") if dt else "unknown"
        out_dir = os.path.join(md_dir, year)
        os.makedirs(out_dir, exist_ok=True)
        out_p = os.path.join(out_dir, f"{day}_{jf[:-5]}.md")
        with open(out_p, "w", encoding="utf-8") as f:
            f.write(raw_to_md.to_md(stored))
        n_md += 1
    print(f"  [{date_str}] key={key} 新增 {len(new_records)} json / {n_md} md", file=sys.stderr)
    return len(new_records)


def main():
    ap = argparse.ArgumentParser(description="中国作家网每日同步流水线")
    ap.add_argument("--key", required=True, help="检索关键词（可多次指定）")
    ap.add_argument("--searchType", type=int, default=1,
                    help="0综合/1标题/2全文/3作者, 默认1")
    ap.add_argument("--sortType", type=int, default=2, help="默认2时间倒序")
    ap.add_argument("--date", default=None, help="精确日期 YYYY-MM-DD（优先级最高）")
    ap.add_argument("--days-back", type=int, default=1,
                    help="回溯最近 N 天（含今天），默认1（当天）")
    ap.add_argument("--max-pages", type=int, default=None,
                    help="每关键词最多请求页数，默认不限")
    ap.add_argument("--no-log", action="store_true", help="不写 log.md")
    args = ap.parse_args()

    keys = args.key if isinstance(args.key, list) else [args.key]

    # 全局限速器：整个同步过程共用同一窗口
    args.limiter = fetch_api.RateLimiter()
    dates = [args.date] if args.date else date_range(args.days_back)

    total = 0
    for d in dates:
        for k in keys:
            n = sync_one_day(k, d, args)
            total += n

    # 3) 生成任务清单
    task_path, pending_n = gen_ingest_task.gen_task_file(
        os.path.join(ROOT, "raw", "markdown"),
        os.path.join(ROOT, "tasks"),
    )
    print(f"任务清单：{task_path}（待 ingest {pending_n} 篇）")

    # 4) 追加 log.md
    if not args.no_log:
        stamp = datetime.now(BJT).strftime("%Y-%m-%d %H:%M")
        log_p = os.path.join(ROOT, "log.md")
        with open(log_p, "a", encoding="utf-8") as f:
            f.write(f"\n## {stamp}\n")
            f.write(f"- 【Sync】每日同步：keys={','.join(keys)} dates={','.join(dates)}"
                    f"，新增 raw {total} 篇；任务清单 {os.path.basename(task_path)}"
                    f"（待 ingest {pending_n} 篇）\n")
    print(f"完成：本次新增 {total} 篇 raw")
    return 0


if __name__ == "__main__":
    sys.exit(main())