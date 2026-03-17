#!/usr/bin/env python3
"""Page type detection for stream-crawler."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

SHELL_TEXT_THRESHOLD = 300
RICH_TEXT_THRESHOLD = 2000
SPA_RATIO_THRESHOLD = 0.5
HYBRID_RATIO_THRESHOLD = 0.85
CHUNK_SCRIPT_THRESHOLD = 3
LIST_MARKER_THRESHOLD = 6

STRATEGY_MAP: dict[str, str] = {
    "static_or_ssr": "curl",
    "hybrid": "Playwright DOM (hydration 後保存)",
    "spa_csr": "Playwright wait + DOM 取得",
}


def _fetch_url_curl(url: str, timeout: int = 15) -> str:
    result = subprocess.run(
        [
            "curl",
            "-sL",
            "--max-time",
            str(timeout),
            "-H",
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0",
            url,
        ],
        capture_output=True,
        text=True,
        timeout=timeout + 5,
    )
    if result.returncode != 0:
        raise RuntimeError(f"curl failed (exit {result.returncode}): {result.stderr[:200]}")
    return result.stdout


def _html_to_text(html: str) -> str:
    s = re.sub(r"<script[^>]*>[\s\S]*?</script>", " ", html, flags=re.IGNORECASE)
    s = re.sub(r"<style[^>]*>[\s\S]*?</style>", " ", s, flags=re.IGNORECASE)
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def analyze_html(html: str, url: str | None = None) -> dict:
    text = _html_to_text(html)
    root_id_pattern = r"(?:root|app|react-root|__nuxt|__next)"
    parsed = urlparse(url or "")
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").lower()

    has_empty_root = bool(
        re.search(rf'<div\s+id=["\']{root_id_pattern}["\']>\s*</div>', html, re.IGNORECASE)
    )
    article_count = len(re.findall(r"<article\b", html, re.I))
    card_class_count = len(
        re.findall(
            r'class=["\'][^"\']*(?:^|[\s_-])(card|result|feed|post|story|product|grid|tile|pin)(?:[\s_-]|$)[^"\']*["\']',
            html,
            re.I,
        )
    )
    load_more_count = len(
        re.findall(r"(load more|もっと見る|さらに表示|show more|see more|next page)", text, re.I)
    )
    infinite_keyword_count = len(
        re.findall(r"(infinite scroll|lazy load|intersectionobserver|timeline|feed|pagination)", html, re.I)
    )
    doc_keyword_count = len(
        re.findall(
            r"(table of contents|TOC|breadcrumb|aria-label=[\"']table of contents[\"']|markdown-body|articleBody)",
            html,
            re.I,
        )
    )
    doc_url_hint = bool(
        re.search(r"/(docs|doc|wiki|article|articles|readme|package|repository|blob|manual)(/|$)", path)
    ) or host.endswith("wikipedia.org") or host.endswith("developer.mozilla.org") or host.endswith("npmjs.com")
    list_url_hint = bool(
        re.search(r"/(search|tag|tags|topics|news|feed|home|discover|explore|mysteries)(/|$)", path)
    ) or host.endswith("news.google.com") or host.endswith("pinterest.com") or host.endswith("zenn.dev") or host.endswith("qiita.com")

    return {
        "host": host,
        "path": path,
        "body_text_len": len(text),
        "html_len": len(html),
        "has_empty_root": has_empty_root,
        "has_nuxt": bool(re.search(r'id=["\']__nuxt["\']', html)),
        "has_root_app": bool(re.search(rf'id=["\']{root_id_pattern}["\']', html)),
        "has_next_data": "__NEXT_DATA__" in html,
        "data_server_rendered": (
            'data-server-rendered="true"' in html
            or "data-server-rendered='true'" in html
        ),
        "script_chunk_count": len(
            re.findall(
                r'<script[^>]+src=["\'][^"\']*(?:chunk|entry|app|bundle|vendor|main)[^"\']*\.js',
                html,
                re.I,
            )
        ),
        "placeholder_count": len(
            re.findall(r"該当\s*count?\s*[：:]\s*[-–—]\s*件|[-–—]\s*件", text)
        ),
        "has_pagination": bool(
            re.search(
                r'class=["\'][^"\']*pagination[^"\']*["\']'
                r'|aria-label=["\']pagination["\']',
                html,
                re.I,
            )
        ),
        "article_count": article_count,
        "card_class_count": card_class_count,
        "load_more_count": load_more_count,
        "infinite_keyword_count": infinite_keyword_count,
        "doc_keyword_count": doc_keyword_count,
        "doc_url_hint": doc_url_hint,
        "list_url_hint": list_url_hint,
    }


def classify(clues: dict, playwright_text_len: int | None = None) -> tuple[str, list[str], list[str]]:
    reasons: list[str] = []
    behaviors: list[str] = []
    score_static = 0
    score_spa = 0
    body_len = clues["body_text_len"]
    listiness = 0
    docness = 0

    if clues["has_empty_root"] and body_len < SHELL_TEXT_THRESHOLD:
        reasons.append(f"Initial HTML is only a shell (empty root element + text {body_len} chars)")
        _detect_behaviors(clues, behaviors)
        return "spa_csr", reasons, behaviors

    if playwright_text_len is not None and playwright_text_len > 0:
        ratio = body_len / playwright_text_len
        if ratio < SPA_RATIO_THRESHOLD:
            score_spa += 3
            reasons.append(
                f"curl/Playwright text ratio = {ratio:.2f} (< {SPA_RATIO_THRESHOLD}) -> dependent on JS"
            )
        elif ratio < HYBRID_RATIO_THRESHOLD:
            score_spa += 1
            score_static += 1
            reasons.append(
                f"curl/Playwright text ratio = {ratio:.2f} -> supplemented by JS (hybrid candidate)"
            )
        else:
            score_static += 2
            reasons.append(f"curl/Playwright text amounts are similar (ratio {ratio:.2f}) -> leaning towards static_or_ssr")

    if body_len >= RICH_TEXT_THRESHOLD:
        score_static += 2
        reasons.append(f"Rich body text ({body_len} chars) -> has main content")
    elif body_len >= SHELL_TEXT_THRESHOLD:
        score_static += 1
        reasons.append(f"Has body text ({body_len} chars)")
    else:
        score_spa += 2
        reasons.append(f"Little body text ({body_len} chars) -> possible shell")

    if clues["has_nuxt"]:
        reasons.append("framework hint: Nuxt (SSR/CSR/hybrid are all possible)")
        if clues["placeholder_count"] > 0:
            score_spa += 2
            reasons.append("Nuxt + placeholders -> this page leans towards CSR")

    if clues["has_root_app"] and body_len < RICH_TEXT_THRESHOLD:
        score_spa += 1
        reasons.append('id="app"/"root" + little text content')

    if clues["has_next_data"]:
        score_static += 1
        reasons.append("framework hint: __NEXT_DATA__ (Next.js SSR)")

    if clues["data_server_rendered"]:
        score_static += 1
        reasons.append("framework hint: data-server-rendered")

    if clues["script_chunk_count"] >= CHUNK_SCRIPT_THRESHOLD:
        score_spa += 1
        reasons.append(f"Many JS chunks/bundles ({clues['script_chunk_count']} 本)")

    if clues["placeholder_count"] > 0 and not clues["has_nuxt"]:
        score_spa += 1
        reasons.append("countplaceholderspresent -> list is fetched via JS")

    if clues["article_count"] >= 3:
        listiness += 2
        reasons.append(f"Multiple article elements ({clues['article_count']}) -> leaning towards list/feed")
    elif clues["article_count"] == 1:
        docness += 1
        reasons.append("Single article element -> leaning towards article page")

    if clues["card_class_count"] >= LIST_MARKER_THRESHOLD:
        listiness += 2
        reasons.append(f"card/item/result classes are abundant ({clues['card_class_count']}) -> leaning towards list")

    if clues["load_more_count"] > 0:
        listiness += 2
        reasons.append("Load more wording present -> leaning towards additional loading")

    if clues["infinite_keyword_count"] > 0:
        listiness += 1
        reasons.append("infinite/lazy/feed keywords present")

    if clues["doc_keyword_count"] > 0:
        docness += 2
        reasons.append("TOC/markdown/articleBody markers present -> leaning towards document")

    if clues["doc_url_hint"]:
        docness += 2
        reasons.append("URL is docs/wiki/article/package related")

    if clues["list_url_hint"]:
        listiness += 2
        reasons.append("URL is search/news/feed/home/discover related")

    if clues["has_pagination"] and listiness == 0:
        listiness += 1
        reasons.append("pagination マーカーあり -> leaning towards list")

    if listiness > docness:
        score_spa += 1
    if docness >= listiness + 2:
        score_static += 1

    _detect_behaviors(clues, behaviors)

    has_ssr_marker = clues["has_next_data"] or clues["data_server_rendered"]
    has_rich_body = body_len >= RICH_TEXT_THRESHOLD

    if listiness >= 3 and "infinite_scroll" not in behaviors:
        behaviors.append("infinite_scroll")

    if docness >= 3 and "document_page" not in behaviors:
        behaviors.append("document_page")

    if has_ssr_marker and score_spa > score_static:
        return "hybrid", reasons, behaviors

    if has_rich_body and clues["script_chunk_count"] >= CHUNK_SCRIPT_THRESHOLD:
        reasons.append("Has initial content + many JS chunks -> hybrid (SSR + hydration)")
        return "hybrid", reasons, behaviors

    if listiness >= 3 and score_static >= score_spa:
        reasons.append("Strong clues for list/feed; stream-crawler does not lean entirely to static")
        return "hybrid", reasons, behaviors

    if docness >= 3 and score_static >= score_spa:
        reasons.append("Strong clues for document/article page")
        return "static_or_ssr", reasons, behaviors

    if score_static > score_spa:
        return "static_or_ssr", reasons, behaviors

    return "spa_csr", reasons, behaviors


def _detect_behaviors(clues: dict, behaviors: list[str]) -> None:
    if clues["placeholder_count"] > 0 or clues.get("has_empty_root"):
        if "infinite_scroll" not in behaviors:
            behaviors.append("infinite_scroll")
    if clues["has_pagination"]:
        if "pagination" not in behaviors:
            behaviors.append("pagination")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Page Type Detection: content_delivery_type + behavior (for fetching strategy)",
    )
    parser.add_argument("--url", type=str, help="URL to detect (fetched via curl)")
    parser.add_argument("--curl-html", type=str, metavar="PATH", help="Path to existing curl fetched HTML file")
    parser.add_argument(
        "--playwright-json",
        type=str,
        metavar="PATH",
        help="Path to page_0001.json fetched by Playwright (improves accuracy through relative comparison if present)",
    )
    parser.add_argument("--timeout", type=int, default=15, help="URL fetch timeout in seconds")
    args = parser.parse_args()

    if args.curl_html:
        path = Path(args.curl_html)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        html = path.read_text(encoding="utf-8", errors="replace")
    elif args.url:
        try:
            html = _fetch_url_curl(args.url, timeout=args.timeout)
        except Exception as exc:
            print(f"Error fetching URL: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Error: either --url or --curl-html is required", file=sys.stderr)
        sys.exit(1)

    clues = analyze_html(html, url=args.url)

    playwright_text_len = None
    if args.playwright_json:
        path = Path(args.playwright_json)
        if not path.exists():
            print(f"Error: file not found: {path}", file=sys.stderr)
            sys.exit(1)
        payload = json.loads(path.read_text(encoding="utf-8"))
        playwright_text_len = int(payload.get("observation", {}).get("text_len", 0))

    content_type, reasons, behaviors = classify(clues, playwright_text_len)
    result = {
        "content_delivery_type": content_type,
        "behaviors": behaviors,
        "reasons": reasons,
        "strategy_hint": STRATEGY_MAP.get(content_type),
        "curl": clues,
        "playwright_text_len": playwright_text_len,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
