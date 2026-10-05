# Task Plan: AI News Tracking Automation

## Project Status: PHASE 1 (Blueprint & Discovery) - Plan Pending Approval

---

## 🎯 Protocol & Methodology
- **Protocol:** B.L.A.S.T. (Blueprint, Link, Architect, Stylize, Trigger)
- **Architecture:** A.N.T. 3-Layer (Architecture SOPs, Navigation / System Pilot, Tools)
- **Core Standard:** Deterministic execution, self-annealing repair loops, strict data schemas.

---

## 📋 Checklist by Phase

### Protocol 0: Initialization
- [x] Create project memory files (`task_plan.md`, `findings.md`, `progress.md`)
- [x] Initialize Project Constitution (`claude.md` / `gemini.md`)
- [x] Create directory scaffolding (`architecture/`, `tools/`, `.tmp/`)
- [x] Halt execution on `tools/` until Discovery, Data Schema, and Blueprint are approved

### Phase 1: B - Blueprint (Vision & Logic)
- [x] **Discovery**: Clarified with user (Sources: Ben's Bites & The Rundown AI; Source of Truth: local storage ready for Supabase; Delivery: 24h refresh + dashboard; Bookmarks persistent; Gorgeous interactive UI).
- [x] **Data-First Schema**: Defined schemas in `gemini.md` & `claude.md` (`RawArticle`, `ArticlePayload`, `DashboardState`).
- [x] **Blueprint Approval**: Present Implementation Plan artifact to user and receive approval. (Approved)

### Phase 2: L - Link (Connectivity)
- [x] Implement atomic handshake script `tools/test_links.py` to verify network access to feeds/archives.
- [x] Verify HTTP response headers, content types, and rate limits. (Both endpoints 200 OK)

### Phase 3: A - Architect (The 3-Layer Build)
- [x] **Layer 1 (Architecture)**: Write Technical SOPs in `architecture/`:
  - `SOP_ingestion.md`: How scrapers collect and parse feeds into `.tmp/raw_*.json`.
  - `SOP_normalization.md`: How articles are deduplicated, filtered for 24h freshness, and transformed into `ArticlePayload`.
  - `SOP_persistence.md`: How local store updates while preserving bookmarks.
- [x] **Layer 3 (Tools)**:
  - `tools/fetch_bens_bites.py` (Substack RSS scraper)
  - `tools/fetch_rundown.py` (Web archive scraper)
  - `tools/normalize_articles.py` (URL canonicalization, SHA256 ID, 24h freshness)
  - `tools/sync_storage.py` (Deduplication, atomic write, bookmark preservation)
- [x] **Layer 2 (Navigation)**: Build orchestrator script `run_pipeline.py`.
- [x] **Self-Annealing Verification**: Verified pipeline end-to-end and confirmed bookmark preservation invariant.

### Phase 4: S - Stylize (Refinement & UI)
- [x] Design and implement interactive web dashboard:
  - Modern dark-mode glassmorphic theme with glowing accents.
  - Tabs: "All Articles", "🔥 Last 24 Hours", "⭐ Saved Articles", "Agents", "LLMs", "Robotics".
  - Search bar with instant client-side filtering and `⌘K` shortcut.
  - Source filter tags (Ben's Bites, The AI Rundown, Reddit AI).
  - Bookmark toggle button with instant feedback, persisted across reloads.
  - "Sync Now" trigger button with live loading state.
  - 3-panel layout faithful to `designinspo.png` with Hippo mascot logo.
- [x] Backend HTTP server and REST API (`server.py` on port 8080).

### Phase 5: T - Trigger (Deployment)
- [x] Configure trigger mechanisms (`trigger_daemon.py` 24h scheduler + UI on-demand sync).
- [x] Validate persistence across browser refreshes and daemon runs.
- [x] Finalize Maintenance Log in `gemini.md` / `claude.md`.
