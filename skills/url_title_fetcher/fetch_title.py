#!/usr/bin/env python3
import sys, json, requests, re

def fetch_title(url):
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "OpenClawSkill/0.1"})
        if resp.status_code != 200:
            return None
        m = re.search(r"<title>(.*?)</title>", resp.text, re.IGNORECASE | re.DOTALL)
        return m.group(1).strip() if m else None
    except Exception:
        return None

if __name__ == "__main__":
    payload = json.load(sys.stdin)
    url = payload.get('url')
    title = fetch_title(url) if url else None
    print(json.dumps({"url": url, "title": title}))
