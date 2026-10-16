#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从 OPML 抓取最近24小时 RSS/Atom 文章，生成中文 Markdown 日报。

默认 OPML: https://raw.githubusercontent.com/xiangyugongzuoliu/awesome-rss-feeds/main/feeds/ai-blogs-cn.opml
默认输出目录: D:\\devloper\\project\\myselfProject\\kb\\📥 Inbox

说明：feedparser 只能解析订阅源实际提供的标题、发布时间和摘要；不会把摘要伪装成全文。
若源没有发布时间则跳过，抓取/解析失败的源会单独列在报告末尾。
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import email.utils
import html
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlparse

import feedparser

DEFAULT_OPML_URL = "https://raw.githubusercontent.com/xiangyugongzuoliu/awesome-rss-feeds-list/main/feeds/cn-essays.opml"
DEFAULT_OUTPUT_DIR = r"D:\devloper\project\myselfProject\kb\📥 Inbox"
USER_AGENT = "Mozilla/5.0 (compatible; PersonalAIRSSDigest/1.0)"
TIMEOUT = 20


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
        return response.read()


def parse_opml(data: bytes) -> list[tuple[str, str]]:
    root = ET.fromstring(data)
    feeds: list[tuple[str, str]] = []
    seen: set[str] = set()
    for node in root.iter():
        url = node.attrib.get("xmlUrl") or node.attrib.get("xmlurl")
        if not url:
            continue
        url = url.strip()
        if not url.startswith(("https://", "http://")) or url in seen:
            continue
        seen.add(url)
        name = (node.attrib.get("title") or node.attrib.get("text") or urlparse(url).netloc).strip()
        feeds.append((name, url))
    return feeds


def clean_text(value: str) -> str:
    value = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", value or "")
    value = re.sub(r"(?s)<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def parse_date(entry) -> dt.datetime | None:
    for key in ("published_parsed", "updated_parsed", "created_parsed"):
        value = entry.get(key)
        if value:
            try:
                return dt.datetime.fromtimestamp(time.mktime(value), tz=dt.timezone.utc)
            except (ValueError, OverflowError, OSError):
                pass
    for key in ("published", "updated", "created", "date"):
        value = entry.get(key)
        if value:
            try:
                parsed = email.utils.parsedate_to_datetime(value)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=dt.timezone.utc)
                return parsed.astimezone(dt.timezone.utc)
            except (TypeError, ValueError, OverflowError):
                pass
    return None


def entry_summary(entry) -> str:
    content = entry.get("content")
    if isinstance(content, list):
        for item in content:
            text = clean_text(item.get("value", ""))
            if text:
                return text
    return clean_text(entry.get("summary", "") or entry.get("description", ""))


def classify(title: str, summary: str, source: str) -> str:
    text = f"{title} {summary} {source}".lower()
    if any(k in text for k in ("arxiv", "论文", "paper", "research paper", "研究成果", "benchmark", "学术研究")):
        return "论文"
    if any(k in text for k in ("github", "开源", "工具", "tool", "agent", "sdk", "框架", "插件", "发布库", "workflow")):
        return "工具"
    if any(k in text for k in ("融资", "收购", "营收", "公司", "企业", "投资", "合作", "产品发布", "定价", "市场", "business", "funding")):
        return "产业"
    return "资讯"


def fetch_feed(feed: tuple[str, str], start: dt.datetime, end: dt.datetime) -> dict:
    name, url = feed
    try:
        parsed = feedparser.parse(fetch_bytes(url))
        if getattr(parsed, "bozo", False) and not parsed.entries:
            raise ValueError(str(parsed.get("bozo_exception", "订阅内容解析失败")))
        articles = []
        undated = 0
        for item in parsed.entries:
            published = parse_date(item)
            if published is None:
                undated += 1
                continue
            if not (start <= published <= end):
                continue
            title = clean_text(item.get("title", "")) or "（无标题）"
            link = item.get("link", "") or url
            summary = entry_summary(item)
            articles.append({
                "id": item.get("id") or link or f"{title}:{published.isoformat()}",
                "title": title, "link": link, "published": published,
                "summary": summary, "source": name,
                "category": classify(title, summary, name),
            })
        return {"name": name, "url": url, "articles": articles,
                "total": len(parsed.entries), "undated": undated, "error": None}
    except Exception as exc:
        return {"name": name, "url": url, "articles": [], "error": f"{type(exc).__name__}: {exc}"}


def clip(text: str, limit: int = 220) -> str:
    if not text:
        return "订阅源未提供摘要；请打开原文阅读。"
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def make_report(results: list[dict], now_utc: dt.datetime, hours: int, opml_url: str) -> str:
    start_utc = now_utc - dt.timedelta(hours=hours)
    local_tz = dt.datetime.now().astimezone().tzinfo
    now_local, start_local = now_utc.astimezone(local_tz), start_utc.astimezone(local_tz)
    by_id = {}
    for result in results:
        for article in result["articles"]:
            by_id.setdefault(article["id"], article)
    articles = sorted(by_id.values(), key=lambda a: a["published"], reverse=True)
    failed = [r for r in results if r["error"]]
    successful = [r for r in results if not r["error"]]

    lines = [
        f"# AI 中文日报｜{now_local:%Y-%m-%d}", "",
        f"> 时间窗口：{start_local:%Y-%m-%d %H:%M} 至 {now_local:%Y-%m-%d %H:%M}（本机时区）",
        f"> 生成时间：{now_local:%Y-%m-%d %H:%M:%S %Z}",
        f"> OPML：{opml_url}",
        f"> 实际抓取且通过时间过滤：**{len(articles)} 篇**；订阅源 {len(results)} 个，失败 {len(failed)} 个。", "",
        "## 今日摘要（基于 RSS 实际提供的信息）", ""
    ]
    # 用最多约500字的合并摘要，保留可核查的标题和链接，不虚构未抓取内容。
    if articles:
        budget = 500
        for a in articles:
            if budget <= 0:
                break
            title = a["title"]
            desc = a["summary"] or "RSS 未提供摘要，需阅读原文确认内容。"
            allowance = max(35, min(150, budget - min(len(title), 90) - 12))
            excerpt = clip(desc, allowance)
            lines.append(f"- **[{title}]({a['link']})**：{excerpt}（{a['source']}）")
            budget -= min(len(title), 90) + len(excerpt) + 8
    else:
        lines.append("最近 24 小时没有抓取到带有效发布时间的文章。请查看下方源状态；本报告不会用猜测内容填充。")

    for category in ("论文", "工具", "产业", "资讯"):
        group = [a for a in articles if a["category"] == category]
        lines.extend(["", f"## {category}（{len(group)}）", ""])
        if not group:
            lines.append("- 本时段未抓取到可确认归入该主题的文章。")
            continue
        for a in group:
            published = a["published"].astimezone(local_tz).strftime("%m-%d %H:%M")
            lines.append(f"- **[{a['title']}]({a['link']})** — {published} · {a['source']}")
            lines.append(f"  - 摘要：{clip(a['summary'])}")
            if not a["summary"]:
                lines.append("  - 注：RSS 未提供摘要，未对文章内容作推断。")

    lines.extend(["", "## 订阅源抓取状态", "",
                  f"- 成功响应并解析：{len(successful)} 个；失败：{len(failed)} 个。",
                  "- 成功解析不代表抓取了全文；日报摘要只使用订阅源实际返回的内容。",
                  "- 无发布时间的条目被跳过，避免把旧文误计为最近24小时。", ""])
    for r in results:
        if r["error"]:
            lines.append(f"- ❌ **{r['name']}** — [{r['url']}]({r['url']})：`{r['error']}`")
        else:
            lines.append(f"- ✅ **{r['name']}** — 扫描 {r['total']} 条，命中 {len(r['articles'])} 条，无有效发布时间而跳过 {r['undated']} 条。")
    lines.extend(["", "## 口径说明", "",
                  "- 分类使用标题、摘要和源名称的关键词规则，可能存在误分。",
                  "- 500字摘要是基于 RSS 摘要的压缩汇总，不等于逐篇阅读全文后的深度总结。",
                  "- 若要对全文进行约500字的综合分析，可在此脚本基础上接入你选定的模型 API。", ""])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="生成最近24小时 AI 中文 RSS 日报")
    parser.add_argument("--opml-url", default=DEFAULT_OPML_URL, help="OPML URL")
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR, help="Markdown 输出目录")
    parser.add_argument("--hours", type=int, default=24, help="时间窗口小时数，默认24")
    parser.add_argument("--workers", type=int, default=12, help="并发抓取数，默认12")
    args = parser.parse_args()
    if args.hours < 1 or args.workers < 1:
        parser.error("--hours 和 --workers 必须大于0")

    now = dt.datetime.now(dt.timezone.utc)
    print(f"下载 OPML：{args.opml_url}")
    try:
        feeds = parse_opml(fetch_bytes(args.opml_url))
    except Exception as exc:
        print(f"OPML 下载或解析失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        print("没有生成日报。请检查网络，或使用 --opml-url 指定可访问的 OPML。", file=sys.stderr)
        return 2
    if not feeds:
        print("OPML 中没有找到 xmlUrl 订阅地址。", file=sys.stderr)
        return 2

    print(f"发现 {len(feeds)} 个订阅源，抓取最近 {args.hours} 小时文章……")
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = [executor.submit(fetch_feed, feed, now - dt.timedelta(hours=args.hours), now) for feed in feeds]
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            results.append(result)
            if result["error"]:
                print(f"[失败] {result['name']}: {result['error']}")
            else:
                print(f"[成功] {result['name']}: 命中 {len(result['articles'])} 篇")

    report = make_report(results, now, args.hours, args.opml_url)
    output_dir = Path(args.output_dir).expanduser()
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{now.astimezone():%Y-%m-%d}-AI日报.md"
        output_file.write_text(report, encoding="utf-8")
    except Exception as exc:
        print(f"写入日报失败：{type(exc).__name__}: {exc}", file=sys.stderr)
        return 3
    print(f"\n日报已保存：{output_file}")
    print(f"文章 {sum(len(r['articles']) for r in results)} 篇；失败源 {sum(bool(r['error']) for r in results)} 个。")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
