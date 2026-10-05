# Standard Operating Procedure (SOP): Article Normalization & Enrichment

> **Layer:** Layer 1 (Architecture)  
> **Status:** Active  
> **Target Script:** `tools/normalize_articles.py`  

---

## 1. Objective
Ingest all raw outputs from `.tmp/raw_*.json`, perform URL canonicalization and deduplication, calculate 24-hour freshness relative to runtime, assign reading time and topical tags, and output `.tmp/normalized_articles.json` conforming to `ArticlePayload[]`.

---

## 2. Normalization Rules

### 2.1 URL Canonicalization & Deterministic Hashing
1. **URL Sanitization:** Strip all tracking query parameters:
   - `utm_source`, `utm_medium`, `utm_campaign`, `utm_content`, `utm_term`
   - `ref`, `action`, `fbclid`, `gclid`
2. **Canonical Hash:**
   - Compute `hash = sha256(normalized_url.encode('utf-8')).hexdigest()[:16]`
   - This 16-character hexadecimal string is the deterministic `id`.

### 2.2 Freshness Filter (24-Hour Rule)
- Compute `now = datetime.now(timezone.utc)`
- Compare with `published_at`:
  - `time_diff = (now - published_at).total_seconds()`
  - `is_last_24h = (0 <= time_diff <= 86400)`
- Articles published within 24 hours receive priority display and a `NEW` badge.
- Articles older than 24 hours remain accessible in the full stream.

### 2.3 Semantic Tagging & Reading Time
- **Tags Rule:** Deterministic keyword matching against title and content:
  - If matches "agent" or "workflow" -> `"Agents"`
  - If matches "claude" or "gpt" or "gemini" or "llm" or "model" -> `"LLMs"`
  - If matches "robot" or "drone" or "hardware" -> `"Robotics"`
  - If matches "open source" or "github" or "weights" -> `"Open Source"`
  - If matches "safety" or "alignment" or "policy" -> `"AI Safety"`
  - Fallback: Source category or `"AI News"`
- **Reading Time:**
  - `word_count = len(text.split())`
  - `reading_time_mins = max(1, round(word_count / 200))`
- **Release Date Formatting:**
  - `released_date_str`: Human readable date (e.g. `Oct 5, 2026`)
  - `released_time_str`: Time in UTC (e.g. `09:00 UTC`)
  - `released_full_str`: Full timestamp (e.g. `Oct 5, 2026 • 09:00 UTC`)

---

## 3. Output Schema
All items must validate against `ArticlePayload` as defined in `gemini.md` Section 2.2.
Written to `.tmp/normalized_articles.json`.
