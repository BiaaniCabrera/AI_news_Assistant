#!/usr/bin/env python3
"""
Layer 2 Orchestrator: run_pipeline.py
Coordinates Layer 3 tools to execute the complete B.L.A.S.T. ingestion cycle.
Returns 0 on success with structured output metrics.
"""

import os
import sys
import subprocess
import time
import json
from datetime import datetime, timezone

STEPS = [
    ("Ingest: Ben's Bites", [sys.executable, "tools/fetch_bens_bites.py"]),
    ("Ingest: The Rundown AI", [sys.executable, "tools/fetch_rundown.py"]),
    ("Normalize: Deduplication & 24h Filter", [sys.executable, "tools/normalize_articles.py"]),
    ("Persistence: Sync Storage", [sys.executable, "tools/sync_storage.py"]),
]

def run_step(step_name: str, cmd: list) -> bool:
    print(f"\n[>>>] Running: {step_name}...")
    start = time.time()
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        elapsed = time.time() - start
        if res.stdout:
            for line in res.stdout.strip().splitlines():
                print(f"      {line}")
        print(f"[OK] {step_name} completed in {elapsed:.2f}s")
        return True
    except subprocess.CalledProcessError as e:
        elapsed = time.time() - start
        print(f"[ERR] {step_name} failed with exit code {e.returncode} in {elapsed:.2f}s", file=sys.stderr)
        if e.stderr:
            print(f"      STDERR: {e.stderr.strip()}", file=sys.stderr)
        return False

def main():
    print(f"==================================================")
    print(f"  AI NEWS TRACKING PIPELINE: Ingestion & Sync")
    print(f"  Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"==================================================")

    all_ok = True
    for step_name, cmd in STEPS:
        success = run_step(step_name, cmd)
        if not success:
            all_ok = False
            # Check if non-critical step: we continue normalize even if one source failed
            if "Ingest" not in step_name:
                print(f"\n[-] Fatal error during critical pipeline step: {step_name}. Halting.", file=sys.stderr)
                sys.exit(1)

    # Read final summary
    storage_path = "data/articles.json"
    if os.path.exists(storage_path):
        with open(storage_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            total = data.get("total_articles", 0)
            fresh = sum(1 for a in data.get("articles", []) if a.get("is_last_24h"))
            saved = sum(1 for a in data.get("articles", []) if a.get("is_saved"))
            print(f"\n==================================================")
            print(f"  PIPELINE EXECUTION COMPLETE")
            print(f"  Total Articles in Store: {total}")
            print(f"  Last 24 Hours: {fresh}")
            print(f"  Saved Bookmarks: {saved}")
            print(f"==================================================")

    sys.exit(0 if all_ok else 1)

if __name__ == "__main__":
    main()
