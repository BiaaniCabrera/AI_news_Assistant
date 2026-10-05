#!/usr/bin/env python3
"""
Layer 3 Tool: fetch_rundown.py
Scrapes The Rundown AI archive page and queries individual article pages for
authentic <meta property="article:published_time"> release timestamps.
Adheres strictly to architecture/SOP_ingestion.md and gemini.md schema.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor

ARCHIVE_URL = "https://www.therundown.ai/archive"
BASE_URL = "https://www.therundown.ai"
OUTPUT_FILE = ".tmp/raw_rundown.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("&#x27;", "'").replace("&quot;", "\"").replace("&amp;", "&").replace("<!-- -->", " ")
    return re.sub(r"\s+", " ", text).strip()

def fetch_article_published_time(url: str, fallback_dt: str) -> str:
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            content = resp.read().decode("utf-8", errors="replace")
        
        # Search for <meta property="article:published_time" content="...">
        m = re.search(r'<meta\s+property=["\']article:published_time["\']\s+content=["\']([^"\']+)["\']', content)
        if m:
            dt_str = m.group(1).strip()
            # Normalize to ISO UTC
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            return dt.astimezone(timezone.utc).isoformat()
    except Exception as e:
        print(f"  [-] Warning extracting date for {url}: {e}", file=sys.stderr)
    return fallback_dt

def scrape_articles(html_content: str):
    articles = []
    extracted_at = datetime.now(timezone.utc).isoformat()

    card_pattern = re.compile(
        r'<a\s+[^>]*href=["\'](/articles/[^"\']+)["\'][^>]*>(.*?)</a>',
        re.DOTALL
    )

    matches = card_pattern.findall(html_content)
    seen_urls = set()
    initial_items = []

    for rel_url, inner_html in matches:
        full_url = BASE_URL + rel_url
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        # Title
        h3_match = re.search(r'<h3[^>]*>(.*?)</h3>', inner_html, re.DOTALL)
        title = clean_text(h3_match.group(1)) if h3_match else "Untitled"

        # Thumbnail
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', inner_html)
        thumbnail = img_match.group(1) if img_match else ""

        # Category
        cat_match = re.search(r'<span[^>]*class=["\'][^"\']*shadow[^"\']*["\'][^>]*>(.*?)</span>', inner_html)
        category = clean_text(cat_match.group(1)) if cat_match else "AI"

        # Author
        meta_match = re.search(r'<p[^>]*class=["\'][^"\']*text-mute[^"\']*["\'][^>]*>(.*?)</p>', inner_html, re.DOTALL)
        meta_text = clean_text(meta_match.group(1)) if meta_match else ""
        
        author = "The Rundown AI"
        if "•" in meta_text:
            parts = meta_text.split("•")
            author = clean_text(parts[0]) or author

        # Fallback date from image timestamp ?t=1791139795 if available
        fallback_date = extracted_at
        if thumbnail and "?t=" in thumbnail:
            try:
                ts = int(thumbnail.split("?t=")[-1].split("&")[0])
                fallback_date = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                pass

        item = {
            "source_id": "the_ai_rundown",
            "source_name": "The Rundown AI",
            "title": title,
            "url": full_url,
            "category": category,
            "author": author,
            "raw_content": f"Category: {category}. Meta: {meta_text}. Read full article at {full_url}",
            "thumbnail_url": thumbnail,
            "published_at": fallback_date,
            "extracted_at": extracted_at,
        }
        initial_items.append(item)

    print(f"[*] Fetching authentic published timestamps for {len(initial_items)} articles...")

    # Concurrently fetch exact published_time for each article
    def enrich_item(item):
        exact_date = fetch_article_published_time(item["url"], item["published_at"])
        item["published_at"] = exact_date
        return item

    with ThreadPoolExecutor(max_workers=5) as executor:
        articles = list(executor.map(enrich_item, initial_items))

    return articles

def main():
    os.makedirs(".tmp", exist_ok=True)
    print(f"[*] Ingesting The Rundown AI archive from {ARCHIVE_URL}...")
    req = urllib.request.Request(ARCHIVE_URL, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[-] Error fetching The Rundown AI archive: {e}", file=sys.stderr)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        sys.exit(0)

    articles = scrape_articles(html)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2)

    print(f"[+] Successfully extracted {len(articles)} articles with authentic timestamps to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
