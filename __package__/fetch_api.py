#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中国作家网数据采集脚本（fetch_api.py）
=======================================
利用 chinawriter 全站检索 API 按关键词 + 精确日期范围采集原文，存入 raw/。

核心能力：支持按 年-月-日（甚至时刻）范围精确筛选。
用法示例：
    # 检索标题含"非虚构"的文章，时间范围 2024-01-01 ~ 2024-01-31
    python scripts/fetch_api.py --key 非虚构 --searchType 1 \
        --start 2024-01-01 --end 2024-01-31 --output raw/json

    # 检索作者=莫言的全部文章（不限时间，回溯至2009）
    python scripts/fetch_api.py --key 莫言 --searchType 3 --output raw/json

依赖：requests  (pip install requests)

⚠️ 反爬纪律（默认即严格，不可轻易调松）：
- 每次请求前随机等待 3~8 秒（--min-delay / --max-delay 可调，默认值已足够保守）
- 每分钟请求数上限 10 次（--rpm，默认严格）
- 单页失败按指数退避重试，最多 MAX_RETRIES 次，超限跳过该页不再硬顶
- 大批量采集请按日期切分多次执行，勿一次性灌满；用 --max-pages 限制单次规模
"""

import argparse
import collections
import json
import os
import random
import sys
import time
from datetime import datetime, timezone, timedelta

import requests

API_URL = "https://search.people.cn/search-platform/front/searchByType"
DOMAIN = "www.chinawriter.com.cn"
REFERER = "https://so.chinawriter.com.cn/"
BJT = timezone(timedelta(hours=8))  # 北京时间

# 反爬默认值（严格模式，勿轻易调松）
MIN_DELAY = 3.0      # 每次请求最小间隔（秒）
MAX_DELAY = 8.0      # 每次请求最大间隔（秒）
DEFAULT_RPM = 10     # 每分钟最大请求数
MAX_RETRIES = 3      # 单页失败最大重试次数
BACKOFF_BASE = 10.0  # 指数退避基数（秒）：10, 20, 40 ...

# 常用 UA，随机轮换以降低反爬风险
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
    "(KHTML, like Gecko) Version/17.0 Safari/605.1.15",
]


class RateLimiter:
    """双重限速：随机间隔 + 每分钟请求数上限。"""

    def __init__(self, min_delay=MIN_DELAY, max_delay=MAX_DELAY, rpm=DEFAULT_RPM):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.rpm = rpm
        self._calls = collections.deque()  # 最近 60s 内的请求时间戳

    def wait(self):
        # 1) 基础随机间隔（每次请求前强制等待）
        time.sleep(random.uniform(self.min_delay, self.max_delay))
        # 2) rpm 窗口限制：若 60s 内已达上限，等到最旧请求滑出窗口
        if self.rpm:
            now = time.time()
            while self._calls and now - self._calls[0] >= 60:
                self._calls.popleft()
            while len(self._calls) >= self.rpm:
                wait = 60 - (now - self._calls[0])
                if wait > 0:
                    print(f"  [rate] 已达每分钟 {self.rpm} 次上限，等待 {wait:.0f}s...",
                          file=sys.stderr)
                    time.sleep(wait)
                now = time.time()
                while self._calls and now - self._calls[0] >= 60:
                    self._calls.popleft()
            self._calls.append(time.time())


def to_epoch_ms(date_str: str) -> int:
    """把 'YYYY-MM-DD' 转成北京时间当日 00:00 的毫秒时间戳。"""
    dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=BJT)
    return int(dt.timestamp() * 1000)


def build_payload(key, search_type, start_ms, end_ms, limit, page, sort_type):
    payload = {
        "domain": DOMAIN,
        "key": key,
        "searchType": search_type,          # 0综合/1标题/2全文/3作者
        "limit": limit,
        "page": page,
        "sortType": sort_type,              # 2时间倒序/1时间正序/3相关度
    }
    if start_ms is not None:
        payload["startTime"] = start_ms     # Long 毫秒时间戳，传字符串会400
    if end_ms is not None:
        payload["endTime"] = end_ms
    return payload


def search_page(key, search_type, start_ms, end_ms, limit, page, sort_type, limiter=None):
    """请求单页，失败按指数退避重试（最多 MAX_RETRIES 次）。
    返回 (records[], total, pages)；重试耗尽返回 (None, 0, 0)，由调用方决定跳过。"""
    payload = build_payload(key, search_type, start_ms, end_ms, limit, page, sort_type)
    for attempt in range(1, MAX_RETRIES + 1):
        headers = {
            "Content-Type": "application/json",
            "Referer": REFERER,
            "User-Agent": random.choice(USER_AGENTS),
            "Origin": "https://so.chinawriter.com.cn",
        }
        try:
            r = requests.post(API_URL, json=payload, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            inner = data.get("data", data)
            hits = inner.get("hits") or inner.get("list") or inner.get("records") or []
            total = int(inner.get("total", 0) or inner.get("count", 0) or 0)
            pages = int(inner.get("pages", 0) or 0)
            return hits, total, pages
        except Exception as e:  # noqa: BLE001
            if attempt >= MAX_RETRIES:
                print(f"  [error] 第{page}页第{attempt}次仍失败: {e}", file=sys.stderr)
                return None, 0, 0
            backoff = BACKOFF_BASE * (2 ** (attempt - 1)) + random.uniform(0, 5)
            print(f"  [retry] 第{page}页失败({type(e).__name__})，"
                  f"退避 {backoff:.0f}s 后重试 ({attempt}/{MAX_RETRIES-1})...", file=sys.stderr)
            time.sleep(backoff)
    return None, 0, 0


def fetch_all(key, search_type, start_ms, end_ms, sort_type, max_pages=None,
              min_delay=MIN_DELAY, max_delay=MAX_DELAY, rpm=DEFAULT_RPM,
              limiter=None):
    """翻页抓取全部结果，限速 + 指数退避，返回记录列表。

    可传入外部 limiter 以在多次 fetch_all 之间复用同一个限速窗口
    （daily_sync.py 每日同步时多关键词连续采集，必须共用限速）。"""
    if limiter is None:
        limiter = RateLimiter(min_delay, max_delay, rpm)
    all_records = []
    page = 1
    limit = 20  # 每页条数取保守值，宁可多几页也不一次拉大
    while max_pages is None or page <= max_pages:
        limiter.wait()  # 每次请求前强制限速
        hits, total, _ = search_page(
            key, search_type, start_ms, end_ms, limit, page, sort_type, limiter
        )
        if hits is None:
            print(f"  [skip] 第{page}页多次失败，跳过该页（不硬顶）", file=sys.stderr)
            break
        if not hits:
            break
        all_records.extend(hits)
        print(f"  已抓取 {len(all_records)} / {total} 条...", file=sys.stderr)
        if len(all_records) >= total or page * limit >= total:
            break
        page += 1
    return all_records


def save_records(records, output_dir, key, start_str, end_str):
    """每条记录存为一个 json 文件，原始字段原样保留（Source of Truth）。
    返回新增保存的记录列表（跳过已存在的）。"""
    os.makedirs(output_dir, exist_ok=True)
    saved = []
    for rec in records:
        url = rec.get("url") or ""
        # 从 url 提取稳定 ID 作为文件名
        content_id = rec.get("id") or rec.get("contentId") or url.split("/")[-1]
        fname = f"{content_id}.json"
        path = os.path.join(output_dir, fname)
        if os.path.exists(path):
            continue  # 已存在不覆盖
        rec.setdefault("_query", {"key": key, "start": start_str, "end": end_str})
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        saved.append(rec)
    return saved


def main():
    ap = argparse.ArgumentParser(description="中国作家网检索采集（严格限速版）")
    ap.add_argument("--key", required=True, help="检索关键词")
    ap.add_argument("--searchType", type=int, default=1,
                    help="0综合/1标题/2全文/3作者, 默认1(标题)")
    ap.add_argument("--start", default=None, help="起始日期 YYYY-MM-DD")
    ap.add_argument("--end", default=None, help="结束日期 YYYY-MM-DD")
    ap.add_argument("--sortType", type=int, default=2,
                    help="2时间倒序(默认)/1时间正序/3相关度")
    ap.add_argument("--output", default="raw/json", help="输出目录")
    ap.add_argument("--max-pages", type=int, default=None,
                    help="最多请求页数（页大小20）；大批量请按日期切片并限制此值")
    ap.add_argument("--min-delay", type=float, default=MIN_DELAY,
                    help=f"请求最小间隔秒（默认{MIN_DELAY}，勿轻易调小）")
    ap.add_argument("--max-delay", type=float, default=MAX_DELAY,
                    help=f"请求最大间隔秒（默认{MAX_DELAY}）")
    ap.add_argument("--rpm", type=int, default=DEFAULT_RPM,
                    help=f"每分钟最大请求数（默认{DEFAULT_RPM}）")
    args = ap.parse_args()

    start_ms = to_epoch_ms(args.start) if args.start else None
    # end 传 'YYYY-MM-DD' 时含当天：转成次日 00:00（左闭右开）
    end_ms = None
    if args.end:
        end_day = datetime.strptime(args.end, "%Y-%m-%d").replace(tzinfo=BJT)
        end_ms = int((end_day + timedelta(days=1)).timestamp() * 1000)

    range_desc = ""
    if start_ms is not None and end_ms is not None:
        range_desc = f"  [{args.start} ~ {args.end}]"
    print(f"开始检索: key={args.key} type={args.searchType} 日期范围{range_desc}")
    print(f"限速: 每请求 {args.min_delay}~{args.max_delay}s, "
          f"每分钟≤{args.rpm}次, 失败退避重试≤{MAX_RETRIES}次", file=sys.stderr)

    records = fetch_all(args.key, args.searchType, start_ms, end_ms, args.sortType,
                        max_pages=args.max_pages,
                        min_delay=args.min_delay, max_delay=args.max_delay, rpm=args.rpm)
    print(f"共获取 {len(records)} 条", file=sys.stderr)

    # 预览前2条，确认时间字段可用
    for rec in records[:2]:
        dt = rec.get("displayTime")
        if dt:
            dts = datetime.fromtimestamp(dt / 1000, tz=BJT).strftime("%Y-%m-%d %H:%M:%S")
            print(f"  样例: [{dts}] {rec.get('title','')[:40]}")
        print(f"        栏目: {rec.get('originNodeRname','')}")

    saved = save_records(records, args.output, args.key, args.start, args.end)
    print(f"新增保存 {len(saved)} 条 -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
