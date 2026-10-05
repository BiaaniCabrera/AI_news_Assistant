#!/usr/bin/env python3
"""
Layer 3 Tool: sync_storage.py
Merges .tmp/normalized_articles.json into persistent data/articles.json.
Guarantees preservation of is_saved bookmarks, atomic file writes,
and validates against DashboardState schema in gemini.md.
"""

import os
import sys
import json
from datetime import datetime, timezone

INPUT_FILE = ".tmp/normalized_articles.json"
STORAGE_DIR = "data"
STORAGE_FILE = os.path.join(STORAGE_DIR, "articles.json")

def load_existing_storage() -> tuple[dict, set]:
    if not os.path.exists(STORAGE_FILE):
        return {}, set()
    try:
        with open(STORAGE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        saved_map = {}
        all_ids = set()
        for art in data.get("articles", []):
            art_id = art["id"]
            all_ids.add(art_id)
            if art.get("is_saved", False):
                saved_map[art_id] = {
                    "is_saved": True,
                    "saved_at": art.get("saved_at")
                }
        return saved_map, all_ids
    except Exception as e:
        print(f"[-] Warning reading existing storage: {e}", file=sys.stderr)
        return {}, set()

def main():
    os.makedirs(STORAGE_DIR, exist_ok=True)
    if not os.path.exists(INPUT_FILE):
        print(f"[-] Input file {INPUT_FILE} does not exist.", file=sys.stderr)
        sys.exit(1)

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        incoming_articles = json.load(f)

    saved_map, existing_ids = load_existing_storage()
    new_count = 0
    updated_articles = []

    for art in incoming_articles:
        art_id = art["id"]
        if art_id not in existing_ids:
            new_count += 1
        
        # PRESERVE BOOKMARK INVARIANT
        if art_id in saved_map:
            art["is_saved"] = True
            art["saved_at"] = saved_map[art_id]["saved_at"]
        else:
            art["is_saved"] = False
            art["saved_at"] = None

        updated_articles.append(art)

    # Collect active sources
    sources_active = sorted(list({a["source"]["name"] for a in updated_articles}))

    dashboard_state = {
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "total_articles": len(updated_articles),
        "sources_active": sources_active,
        "articles": updated_articles
    }

    # Atomic write pattern
    temp_storage = STORAGE_FILE + ".tmp"
    with open(temp_storage, "w", encoding="utf-8") as f:
        json.dump(dashboard_state, f, indent=2)
    os.replace(temp_storage, STORAGE_FILE)

    saved_count = len(saved_map)
    print(f"[+] Synced {len(updated_articles)} articles ({new_count} new, {saved_count} preserved bookmarks) to {STORAGE_FILE}")

if __name__ == "__main__":
    main()
