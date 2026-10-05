# Standard Operating Procedure (SOP): Data Ingestion

> **Layer:** Layer 1 (Architecture)  
> **Status:** Active  
> **Target Scripts:** `tools/fetch_bens_bites.py`, `tools/fetch_rundown.py`  

---

## 1. Objective
Deterministically collect the latest published articles and newsletter editions from target AI newsletters (*Ben's Bites*, *The AI Rundown*) and serialize them into raw intermediate files in `.tmp/` adhering to the `RawArticle` JSON schema defined in `gemini.md`.

---

## 2. Ingestion Specifications

### 2.1 Ben's Bites Ingestion
- **Protocol:** RSS 2.0 via HTTP GET.
- **Source URL:** `https://bensbites.substack.com/feed`
- **Output File:** `.tmp/raw_bens_bites.json`
- **Required Headers:**
  - `User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36`
- **Extraction Rules:**
  - `source_id`: `"bens_bites"`
  - `source_name`: `"Ben's Bites"`
  - `title`: Extracted from `<item><title>`. Clean CDATA blocks.
  - `url`: Extracted from `<item><link>` or `<item><guid>`. Strip UTM tags.
  - `published_at`: Parsed from `<item><pubDate>` (RFC 822 / RFC 2822) converted to ISO 8601 UTC.
  - `raw_content`: Concatenation of `<description>` and text-stripped `<content:encoded>` excerpts.
  - `thumbnail_url`: Extracted from `<enclosure url="...">` or first image in content.
  - `author`: Extracted from `<dc:creator>` or fallback to `"Ben Tossell"`.
  - `extracted_at`: Current ISO 8601 UTC timestamp.

### 2.2 The Rundown AI Ingestion
- **Protocol:** Web scraping via HTTP GET.
- **Source URL:** `https://www.therundown.ai/archive` (or `https://www.therundown.ai/articles`)
- **Output File:** `.tmp/raw_rundown.json`
- **Required Headers:** Standard desktop browser user-agent.
- **Extraction Rules:**
  - Card container: `div[data-archive-results="true"] a.group`
  - `source_id`: `"the_ai_rundown"`
  - `source_name`: `"The Rundown AI"`
  - `title`: Extracted from `h3` heading.
  - `url`: `https://www.therundown.ai` + relative `href`.
  - `category`: Badge text (e.g., "AI", "Tech", "Robotics").
  - `published_at`: Extracted directly from individual article `<meta property="article:published_time" content="...">` in ISO 8601 UTC. Fallback to image unix timestamp `?t=[timestamp]` or current ISO 8601 UTC.
  - `thumbnail_url`: Extracted from `img[src]`.
  - `author`: Extracted from author string (e.g. "Zach Mink", "Rowan Cheung").
  - `extracted_at`: Current ISO 8601 UTC timestamp.

---

## 3. Error Handling & Invariants
- **Timeout Limit:** 10 seconds per HTTP request.
- **Fallback Rule:** If one source fails (e.g., 500 error or markup change), log the warning to `.tmp/scraper_errors.log` and write an empty or partial list; never abort other sources or the normalization step.
- **Storage Rule:** All outputs are strictly written to `.tmp/`.
