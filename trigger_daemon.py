#!/usr/bin/env python3
"""
Phase 5: Trigger Daemon (trigger_daemon.py)
Automated 24-hour background scheduler.
Periodically triggers run_pipeline.py every 24 hours (or configured interval).
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone

INTERVAL_SECONDS = 86400  # 24 hours
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PIPELINE_SCRIPT = os.path.join(BASE_DIR, "run_pipeline.py")

def main():
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else INTERVAL_SECONDS
    hours = interval / 3600
    print(f"==================================================")
    print(f"  HIPPO AI NEWS: 24-HOUR TRIGGER DAEMON")
    print(f"  Cycle Interval: {interval}s ({hours:.1f} hours)")
    print(f"  Start Time: {datetime.now(timezone.utc).isoformat()}")
    print(f"==================================================")

    while True:
        print(f"\n[*] Triggering scheduled run at {datetime.now(timezone.utc).isoformat()}...")
        try:
            res = subprocess.run([sys.executable, PIPELINE_SCRIPT], capture_output=True, text=True, check=False)
            if res.returncode == 0:
                print(f"[+] Scheduled pipeline completed successfully.")
            else:
                print(f"[-] Pipeline run exited with code {res.returncode}", file=sys.stderr)
        except Exception as e:
            print(f"[-] Error executing pipeline: {e}", file=sys.stderr)

        print(f"[*] Sleeping for {interval}s until next scheduled execution...")
        time.sleep(interval)

if __name__ == "__main__":
    main()
