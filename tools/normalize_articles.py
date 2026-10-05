#!/usr/bin/env python3
"""
Layer 3 Tool: normalize_articles.py
Normalizes raw article dumps from .tmp/raw_*.json.
Calculates deterministic SHA256 ID, 24-hour freshness, reading time, semantic tags,
and formats into ArticlePayload[] conforming to architecture/SOP_normalization.md and gemini.md.
"""

import os
import sys
import glob
import json
import hashlib
import urllib.parse
from datetime import datetime, timezone

RAW_DIR = ".tmp"
OUTPUT_FILE = ".tmp/normalized_articles.json"

SOURCE_METADATA = {
    "bens_bites": {
        "name": "Ben's Bites",
        "badge_color": "#FFB9CD",  # Brand primary soft pink
        "icon": "⚡"
    },
    "the_ai_rundown": {
        "name": "The AI Rundown",
        "badge_color": "#664A52",  # Brand secondary deep plum
        "icon": "📰"
    },
    "reddit_ai": {
        "name": "Reddit AI",
        "badge_color": "#FFE6E5",
        "icon": "🤖"
    }
}

TAG_KEYWORDS = [
    ("Agents", ["agent", "agents", "manus", "dots", "autonomous", "assistants", "workflow"]),
    ("LLMs", ["gpt", "claude", "gemini", "opus", "sonnet", "sol", "astra", "llm", "frontier", "model"]),
    ("Robotics", ["robot", "robotics", "drone", "hardware", "spacex", "devices", "physical"]),
    ("Open Source", ["open source", "github", "weights", "llama", "hugging face", "open-source"]),
    ("AI Safety", ["safety", "alignment", "insider", "incident", "misalignment", "policy", "regulat"]),
    ("Industry", ["apple", "google", "meta", "openai", "anthropic", "nvidia", "acquisition", "billion"])
]

def canonicalize_url(url: str) -> str:
    if not url:
        return ""
    try:
        parsed = urllib.parse.urlparse(url)
        # Filter out tracking query params
        q_params = urllib.parse.parse_qsl(parsed.query)
        cleaned_params = [
            (k, v) for k, v in q_params 
            if not k.startswith("utm_") and k not in {"ref", "action", "fbclid", "gclid", "source"}
        ]
        new_query = urllib.parse.urlencode(cleaned_params)
        canonical = urllib.parse.urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path.rstrip("/"),
            "",
            new_query,
            ""
        ))
        return canonical
    except Exception:
        return url.split("?")[0].rstrip("/")

def compute_deterministic_id(canonical_url: str, fallback_title: str) -> str:
    key = canonical_url if canonical_url else fallback_title
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:16]

def extract_tags(title: str, content: str, default_cat: str = "") -> list:
    text = f"{title} {content}".lower()
    matched_tags = []
    for tag, keywords in TAG_KEYWORDS:
        if any(kw in text for kw in keywords):
            matched_tags.append(tag)
    if default_cat and default_cat not in matched_tags:
        matched_tags.append(default_cat)
    if not matched_tags:
        matched_tags.append("AI News")
    return matched_tags[:4]

def calculate_reading_time(text: str) -> int:
    word_count = len(text.split())
    mins = round(word_count / 200)
    return max(1, mins)

def clean_summary(text: str, max_chars: int = 240) -> str:
    if not text:
        return "No summary provided."
    # Remove excessive whitespace
    cleaned = " ".join(text.split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[:max_chars].rstrip() + "..."

def main():
    now = datetime.now(timezone.utc)
    raw_files = glob.glob(os.path.join(RAW_DIR, "raw_*.json"))
    if not raw_files:
        print("[-] No raw files found in .tmp/", file=sys.stderr)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        sys.exit(0)

    deduped_articles = {}

    for raw_file in raw_files:
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception as e:
            print(f"[-] Failed reading {raw_file}: {e}", file=sys.stderr)
            continue

        for item in items:
            raw_url = item.get("url", "")
            title = item.get("title", "Untitled").strip()
            canonical_url = canonicalize_url(raw_url)
            art_id = compute_deterministic_id(canonical_url, title)

            pub_str = item.get("published_at", "")
            try:
                pub_dt = datetime.fromisoformat(pub_str)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            except Exception:
                pub_dt = now

            # Check 24-hour freshness (within 86,400 seconds)
            time_diff = (now - pub_dt).total_seconds()
            is_last_24h = (0 <= time_diff <= 86400)

            source_id = item.get("source_id", "bens_bites")
            meta = SOURCE_METADATA.get(source_id, {
                "name": item.get("source_name", "AI News"),
                "badge_color": "#FFB9CD",
                "icon": "⚡"
            })

            content = item.get("raw_content", "")
            tags = extract_tags(title, content, item.get("category", ""))
            reading_time = calculate_reading_time(content)
            thumbnail = item.get("thumbnail_url", "")

            # If already exists, keep freshest or more detailed
            if art_id in deduped_articles:
                existing = deduped_articles[art_id]
                if not existing.get("thumbnail_url") and thumbnail:
                    existing["thumbnail_url"] = thumbnail
                continue

            # Format release dates
            released_date = pub_dt.strftime("%b %d, %Y")
            released_time = pub_dt.strftime("%H:%M UTC")
            released_full = f"{released_date} • {released_time}"

            article_payload = {
                "id": art_id,
                "source": {
                    "id": source_id,
                    "name": meta["name"],
                    "badge_color": meta["badge_color"]
                },
                "title": title,
                "url": canonical_url or raw_url,
                "summary": clean_summary(content),
                "published_at": pub_dt.isoformat(),
                "released_date": released_date,
                "released_time": released_time,
                "released_full": released_full,
                "is_last_24h": is_last_24h,
                "tags": tags,
                "reading_time_mins": reading_time,
                "thumbnail_url": thumbnail,
                "author": item.get("author", meta["name"]),
                "is_saved": False,
                "saved_at": None
            }

            deduped_articles[art_id] = article_payload

    normalized_list = list(deduped_articles.values())
    # Sort chronologically, freshest first
    normalized_list.sort(key=lambda x: x["published_at"], reverse=True)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_list, f, indent=2)

    fresh_count = sum(1 for a in normalized_list if a["is_last_24h"])
    print(f"[+] Normalized {len(normalized_list)} total articles ({fresh_count} from last 24h) to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
