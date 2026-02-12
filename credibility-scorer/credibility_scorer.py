#!/usr/bin/env python3
import sys, json

def main():
    try:
        data = json.load(sys.stdin)
    except Exception as e:
        print(json.dumps({"error": f"Invalid JSON: {e}"}))
        sys.exit(1)
    url = data.get('url', '')
    result = {"url": url, "score": 0.9, "verdict": "High", "details": {}}
    print(json.dumps(result))

if __name__ == '__main__':
    main()
