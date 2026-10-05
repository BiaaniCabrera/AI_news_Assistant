#!/usr/bin/env python3
"""
Phase 2: Link - Handshake script to verify external newsletter connectivity.
Tests Ben's Bites Substack RSS and The Rundown AI archive endpoints.
"""

import sys
import urllib.request
import urllib.error

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}

ENDPOINTS = [
    ("Ben's Bites (Custom Domain RSS)", "https://www.bensbites.com/feed"),
    ("The Rundown AI Archive", "https://www.therundown.ai/archive"),
]

def test_endpoint(name: str, url: str) -> bool:
    print(f"[*] Testing connection to {name} ({url})...")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=12) as response:
            status = response.getcode()
            content_type = response.headers.get("Content-Type", "Unknown")
            sample = response.read(256)
            print(f"  [+] SUCCESS: Status {status}, Content-Type: {content_type}, Bytes read: {len(sample)}")
            return True
    except urllib.error.HTTPError as e:
        print(f"  [-] HTTP Error {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"  [-] Connection Failed: {e}")
        return False

def main():
    print("=== Phase 2 (Link): Network Handshake Verification ===")
    results = [test_endpoint(name, url) for name, url in ENDPOINTS]
    if all(results):
        print("\n[+] All newsletter endpoints responded successfully.")
        sys.exit(0)
    else:
        print("\n[-] One or more endpoints failed connectivity test.")
        sys.exit(1)

if __name__ == "__main__":
    main()
