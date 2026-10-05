# Findings & Research Log

## 1. Project Context
- **Workspace:** `/Users/biaanicabrera/Tracking_AI_news`
- **Objective:** Deterministic, self-healing automation for tracking AI news using B.L.A.S.T. protocol & A.N.T. architecture.
- **Operating Environment:** macOS (zsh), Python 3.
- **Client Requirements:**
  - News sources: Newsletters (*Ben's Bites*, *The AI Rundown*), with Reddit expandability.
  - Frequency: 24h cycle (articles from the last 24 hours prioritized) + on-demand run.
  - Storage: In-app local persistence (JSON/SQLite) with zero loss of saved bookmarks on reload; structured for future Supabase migration.
  - UI/UX: Gorgeous, modern, interactive dashboard (dark mode, glassmorphism, responsive filters, search, bookmarking).

---

## 2. Source Ingestion Research & Findings

### 2.1 Ben's Bites
- **Endpoint:** `https://bensbites.substack.com/feed` (RSS 2.0 XML)
- **Status:** Verified live and accessible.
- **Data Extracted:**
  - `title`: e.g. "OpenAI DevDay 2026", "Sonnet 5.5 is worth a try"
  - `link`: Direct URL to newsletter edition
  - `pubDate`: RFC 822 format (e.g., `Thu, 01 Oct 2026 13:30:36 GMT`)
  - `description` / `content:encoded`: Rich summary, headline bullets, links
  - `enclosure`: Image preview URL

### 2.2 The Rundown AI
- **Endpoint:** `https://www.therundown.ai/archive` (HTML Next.js render) & `https://www.therundown.ai/articles`
- **Status:** Verified live and accessible.
- **Data Extracted:**
  - Card selector: `div[data-archive-results="true"] a.group`
  - Link: `/articles/[slug]` -> `https://www.therundown.ai/articles/[slug]`
  - Category Badge: `span` (e.g. "AI", "Tech", "Robotics")
  - Title: `h3` text
  - Meta: author name & reading time (e.g. `Zach Mink • 7 minutes`)
  - Thumbnail: `img[src]`
  - Content details: individual article pages fetchable for deep summary

### 2.3 Reddit (Expansion Source)
- **Endpoint:** `https://www.reddit.com/r/MachineLearning/hot.json?limit=25` or `r/artificial/hot.json`
- **Status:** Standard public JSON API with customized `User-Agent: AI-News-Tracker/1.0` header.

---

## 3. Brand & Visual Design Profile
- **Logo:** `DesignGuidelines/designlogo.png` - Blue stylized hippo mascot, incorporated into navigation brand header and favicon.
- **Palette (Brand Guidelines):**
  - Primary Pink: `#FFB9CD`
  - Secondary Plum: `#664A52`
  - Accent Pink Glow: `#FFB9CD`
  - Canvas / Background: Deep Obsidian Dark Canvas (`#0B0E14` / `#111622`) with Plum accents (`#1A131A`), plus clean light-mode token support (`#FFFFFF`).
  - Text: Contrast White (`#FFFFFF`), Soft Cream (`#F5E6EB`), Text Primary (`#000000`).
  - Links & Subtle Badges: `#FFE6E5`.
- **Typography:** Friendly geometric rounded typography (`'CrumblSansFont', 'Outfit', 'Plus Jakarta Sans', sans-serif`).
- **UI Architecture (from `designinspo.png`):**
  - **3-Panel Master Layout:**
    1. **Left Nav Rail:** Sleek floating pill sidebar with brand logo at top, active view icons (Grid, News, Heart/Bookmarks, Archive, Settings), and expand/collapse control at the bottom.
    2. **Center News Feed Canvas:**
       - Search Pill Bar with instant filtering and live sync indicator.
       - Hero Spotlight Banner with smooth gradient mesh and daily AI digest CTA.
       - Source Filter Avatar Row (Ben's Bites, The AI Rundown, Reddit).
       - Category tabs (All, Last 24 Hours, Saved, Hot/Trending).
       - Multi-column article cards with thumbnail, timer/date pill, source chip, title, and quick-save heart toggle.
    3. **Right Inspector Panel (Featured Layered Stack):**
       - Distinctive layered tilted-card stack preview highlighting the currently active or top breaking AI story.
       - Full metadata breakdown (Publication time, reading minutes, author, source badge).
       - Action buttons ("Read Full Story", "Save to Bookmarks").

---

## 4. Architecture & Tech Decisions
- **Backend / Scraper Engine (Layer 3 Tools):**
  - Modular, atomic Python scripts:
    - `fetch_bens_bites.py`: Fetches and parses RSS feed into `RawArticle` JSON.
    - `fetch_rundown.py`: Fetches and parses archive into `RawArticle` JSON.
    - `normalize_articles.py`: Deduplicates by URL hash, calculates `is_last_24h` relative to run time, assigns tags, reading time, and prepares `ArticlePayload`.
    - `sync_storage.py`: Merges incoming articles with persisted database (`data/articles.json`), preserving bookmarks (`is_saved`).
- **Dashboard Frontend (Layer 4 Stylize):**
  - Modern web application served with a lightweight local Python HTTP API or Node/Vite server.
  - Pixel-perfect recreation of the aesthetics in `designinspo.png` tailored to AI news tracking and the user's pink/plum brand theme.

