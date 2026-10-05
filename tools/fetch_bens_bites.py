#!/usr/bin/env python3
"""
Layer 3 Tool: fetch_bens_bites.py
Fetches Ben's Bites RSS feed, parses XML, and writes RawArticle array to .tmp/raw_bens_bites.json
Adheres strictly to architecture/SOP_ingestion.md and gemini.md schema.
"""

import os
import sys
import json
import re
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

FEED_URL = "https://www.bensbites.com/feed"
OUTPUT_FILE = ".tmp/raw_bens_bites.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

def clean_html(raw_html: str) -> str:
    if not raw_html:
        return ""
    # Remove HTML tags
    clean = re.sub(r"<[^>]+>", " ", raw_html)
    # Decode basic entities
    clean = clean.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&#8217;", "'").replace("&#8220;", "\"").replace("&#8221;", "\"")
    # Normalize whitespace
    return re.sub(r"\s+", " ", clean).strip()

def parse_date(date_str: str) -> str:
    try:
        dt = parsedate_to_datetime(date_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.isoformat()
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def extract_thumbnail(item: ET.Element) -> str:
    # 1. Enclosure attribute
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("url"):
        return enclosure.get("url")
    
    # 2. Search inside content:encoded or description for <img> tags
    for tag_name in ["{http://purl.org/rss/1.0/modules/content/}encoded", "description"]:
        elem = item.find(tag_name)
        if elem is not None and elem.text:
            m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', elem.text)
            if m:
                return m.group(1)
    return ""

def main():
    os.makedirs(".tmp", exist_ok=True)
    print(f"[*] Ingesting Ben's Bites feed from {FEED_URL}...")
    req = urllib.request.Request(FEED_URL, headers=HEADERS)

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            xml_data = resp.read()
    except Exception as e:
        print(f"[-] Error fetching Ben's Bites feed: {e}", file=sys.stderr)
        # Self-annealing fallback: empty list
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        sys.exit(0)

    try:
        root = ET.fromstring(xml_data)
    except Exception as e:
        print(f"[-] XML parsing error: {e}", file=sys.stderr)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        sys.exit(0)

    articles = []
    extracted_at = datetime.now(timezone.utc).isoformat()
    channel = root.find("channel")
    if channel is None:
        channel = root

    for item in channel.findall("item"):
        title_elem = item.find("title")
        link_elem = item.find("link")
        guid_elem = item.find("guid")
        pub_elem = item.find("pubDate")
        desc_elem = item.find("description")
        content_elem = item.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        creator_elem = item.find("{http://purl.org/dc/elements/1.1/}creator")

        title = title_elem.text.strip() if title_elem is not None and title_elem.text else "Untitled"
        url = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
        if not url and guid_elem is not None and guid_elem.text:
            url = guid_elem.text.strip()

        pub_raw = pub_elem.text.strip() if pub_elem is not None and pub_elem.text else ""
        published_at = parse_date(pub_raw)

        desc_text = desc_elem.text if desc_elem is not None and desc_elem.text else ""
        content_text = content_elem.text if content_elem is not None and content_elem.text else ""
        
        full_text = clean_html(f"{desc_text} {content_text}")
        thumbnail = extract_thumbnail(item)
        author = creator_elem.text.strip() if creator_elem is not None and creator_elem.text else "Ben Tossell"

        raw_item = {
            "source_id": "bens_bites",
            "source_name": "Ben's Bites",
            "title": title,
            "url": url,
            "published_at": published_at,
            "raw_content": full_text[:4000],  # bounded excerpt
            "author": author,
            "thumbnail_url": thumbnail,
            "extracted_at": extracted_at,
        }
        articles.append(raw_item)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2)

    print(f"[+] Successfully extracted {len(articles)} articles from Ben's Bites to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
