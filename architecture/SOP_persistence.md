# Standard Operating Procedure (SOP): Data Persistence & Storage Sync

> **Layer:** Layer 1 (Architecture)  
> **Status:** Active  
> **Target Script:** `tools/sync_storage.py`  

---

## 1. Objective
Merge newly normalized articles from `.tmp/normalized_articles.json` into the persistent source of truth (`data/articles.json`) without erasing existing user bookmarks (`is_saved = true`), maintaining a structured store prepared for direct Supabase cloud migration.

---

## 2. Invariants & Preservation Rules

1. **State Preservation Invariant:**
   - If an article `id` already exists in `data/articles.json`, its `is_saved` boolean and `saved_at` timestamp MUST be preserved from the existing store.
   - Updated metadata (such as fresh reading metrics, tags, or content) may overwrite the older entry, but bookmark status is sacred.
2. **Deduplication:**
   - No two items in `data/articles.json` may share the same `id`.
3. **Atomic Writes:**
   - Data is written to `data/articles.json.tmp` and atomically renamed to `data/articles.json` to prevent partial file corruption on interruption.
4. **Dashboard State Schema:**
   - The file `data/articles.json` must always adhere to the `DashboardState` schema in `gemini.md`:
     - `last_sync`: ISO 8601 UTC timestamp of latest sync run.
     - `total_articles`: Total count.
     - `sources_active`: Array of distinct source names active.
     - `articles`: Array of `ArticlePayload` items sorted chronologically (newest first).

---

## 3. Cloud Migration Readiness
The structure of each object in `data/articles.json` maps 1:1 to a future Supabase relational or document table (`articles` table with `id`, `title`, `url`, `source_id`, `published_at`, `is_saved`).
