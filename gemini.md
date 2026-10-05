# Project Constitution: AI News Tracking Automation

> **Status:** Active & Enforced  
> **Methodology:** B.L.A.S.T. Protocol (Blueprint, Link, Architect, Stylize, Trigger)  
> **System Architecture:** A.N.T. 3-Layer Architecture  

---

## 1. Architectural Invariants

1. **Deterministic Execution:** Business logic, deduplication, and parsing must be strictly deterministic Python scripts in `tools/`. LLMs are used for semantic summarization and tagging, never for core routing or primary state mutation.
2. **Strict Layer Separation:**
   - **Layer 1 (Architecture):** `architecture/` contains technical SOPs in Markdown. SOPs must be updated *before* code logic changes.
   - **Layer 2 (Navigation):** System Pilot reasoning and data routing orchestrator.
   - **Layer 3 (Tools):** Atomic, independently executable scripts in `tools/` with parameters and standard exit codes.
3. **Data-First Rule:** No tool or frontend component is written without an approved schema in this document.
4. **Self-Annealing Loop:** On tool or scraping failure: (1) analyze stack trace, (2) patch tool, (3) verify, (4) record fix and rule in SOP.
5. **Ephemeral vs. Persistent Storage:**
   - `.tmp/`: All scratch files, raw HTML/JSON scraper dumps. Ephemeral and discardable.
   - Local DB / JSON Store: Current local Source of Truth (SQLite / `data/articles.json`), ready for clean migration to Supabase.
   - UI State: Client-side saved bookmarks stored deterministically and synchronized with local persistence.

---

## 2. Data Schemas

### 2.1 Raw Ingestion Item (`RawArticle`)
Raw payload returned by Layer 3 scrapers / feed fetchers:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RawArticle",
  "type": "object",
  "required": ["source_id", "title", "url", "published_at", "raw_content", "extracted_at"],
  "properties": {
    "source_id": {
      "type": "string",
      "enum": ["bens_bites", "the_ai_rundown", "reddit_ai"]
    },
    "source_name": { "type": "string" },
    "title": { "type": "string" },
    "url": { "type": "string", "format": "uri" },
    "published_at": { "type": "string", "format": "date-time" },
    "raw_content": { "type": "string" },
    "author": { "type": ["string", "null"] },
    "extracted_at": { "type": "string", "format": "date-time" }
  }
}
```

### 2.2 Processed Article Payload (`ArticlePayload`)
Processed item served to dashboard & storage:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "ArticlePayload",
  "type": "object",
  "required": ["id", "source", "title", "url", "summary", "published_at", "is_last_24h", "tags", "reading_time_mins", "is_saved"],
  "properties": {
    "id": { "type": "string", "description": "Deterministic SHA256(canonical_url)[:16]" },
    "source": {
      "type": "object",
      "required": ["id", "name", "badge_color"],
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "badge_color": { "type": "string" }
      }
    },
    "title": { "type": "string" },
    "url": { "type": "string", "format": "uri" },
    "summary": { "type": "string" },
    "published_at": { "type": "string", "format": "date-time" },
    "is_last_24h": { "type": "boolean" },
    "tags": {
      "type": "array",
      "items": { "type": "string" }
    },
    "reading_time_mins": { "type": "integer", "minimum": 1 },
    "is_saved": { "type": "boolean", "default": false },
    "saved_at": { "type": ["string", "null"], "format": "date-time" }
  }
}
```

### 2.3 Dashboard State Payload (`DashboardState`)
Collection delivered to frontend and synchronized with storage:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "DashboardState",
  "type": "object",
  "required": ["last_sync", "total_articles", "articles", "sources_active"],
  "properties": {
    "last_sync": { "type": "string", "format": "date-time" },
    "total_articles": { "type": "integer" },
    "sources_active": { "type": "array", "items": { "type": "string" } },
    "articles": {
      "type": "array",
      "items": { "$ref": "#/definitions/ArticlePayload" }
    }
  }
}
```

---

## 3. Behavioral Rules

1. **24-Hour Freshness Filter:** Articles published within the last 24 hours relative to run time are prioritized with a `NEW` badge and displayed in the main stream. Older articles remain accessible under filter/archive.
2. **Deduplication:** Normalizes URLs (strips UTM query parameters, tracking fragments) and computes deterministic hash `SHA256(normalized_url)[:16]` as article ID. Identical IDs overwrite with freshest metadata without losing user's `is_saved` status.
3. **Graceful Fallbacks:** If a newsletter site changes markup or throttles, the scraper must degrade gracefully, logging the failure to `.tmp/` and `progress.md` without halting the entire pipeline.
4. **State Persistence:** Saved/bookmarked articles persist in both localStorage and local backend storage (`data/storage.json` / SQLite), surviving refreshes and re-scrapes.
5. **UI & UX Standard (Design Profile & Guidelines):**
   - **Color System:**
     - Primary: `#FFB9CD` (Soft Rose Pink)
     - Secondary: `#664A52` (Deep Muted Plum/Cocoa)
     - Accent: `#FFB9CD` / Glow accents
     - Background: Dark glassmorphic canvas (`#0D1117`, `#161B22`, `#1E171B`) with light mode token compatibility (`#FFFFFF`, `#FFF0F4`)
     - Text: `#FFFFFF` / `#F0E6EA` on dark cards, `#000000` on light elements
     - Link & Highlights: `#FFE6E5`
   - **Branding & Assets:**
     - Official Logo: `DesignGuidelines/designlogo.png` (Hippo brand character) featured in the sidebar/navigation header.
     - Typography: Geometric, friendly rounded font system (`'CrumblSansFont', 'Outfit', 'Plus Jakarta Sans', sans-serif`).
   - **Interface Composition (Matched to `designinspo.png`):**
     - **Left Navigation Rail:** Floating glass sidebar with sleek iconography (Dashboard/Grid, Daily News, Saved/Bookmarks, Archive, Settings, Collapse toggle).
     - **Top Search & Status Bar:** Pill search bar ("Search everything..."), live sync status, notifications, and profile.
     - **Hero Spotlight Card:** Gradient hero banner highlighting key AI breakthrough or summary of the day.
     - **Source Avatar Filter Row:** Interactive avatar pills for quick source filtering (Ben's Bites, The AI Rundown, Reddit AI).
     - **Main Multi-Column Grid:** Glass cards featuring thumbnail, category badge, publication countdown/timestamp, title, excerpt, and bookmark toggle.
     - **Right Side Inspector / Featured Reading Drawer:** Layered preview stack displaying the selected/latest article in detail with full reading notes and direct action links.

---

## 4. Maintenance & Evolution Log
- **2026-10-05:** Project Constitution established. Data schemas defined for Ben's Bites & The AI Rundown newsletters.
- **2026-10-05:** Brand Guidelines integrated (`#FFB9CD` / `#664A52`, Hippo logo, `designinspo.png` layout).

