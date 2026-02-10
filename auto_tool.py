import re
from typing import Optional, Dict

# Simple heuristics for automatic tool selection
SEARCH_KEYWORDS = r"\b(latest|current|today|news|price|forecast|who|what|when|where|how)\b"
FETCH_KEYWORDS = r"\b(pdf|report|article|doc|download|link)\b"
EXEC_KEYWORDS = r"\b(run|execute|script|bash|python)\b"

def decide_tool(user_msg: str) -> Optional[Dict[str, str]]:
    """Return a dict describing the chosen tool, or None if no tool needed.
    The dict can be fed directly to the appropriate function call.
    """
    msg = user_msg.lower()
    if re.search(SEARCH_KEYWORDS, msg):
        return {"tool": "web_search", "query": user_msg}
    if re.search(FETCH_KEYWORDS, msg):
        # try to extract a URL from the message
        words = user_msg.split()
        for w in words:
            if w.startswith('http://') or w.startswith('https://'):
                return {"tool": "web_fetch", "url": w}
        # fallback – treat whole message as a URL placeholder
        return {"tool": "web_fetch", "url": user_msg}
    if re.search(EXEC_KEYWORDS, msg):
        parts = user_msg.split(None, 1)
        cmd = parts[1] if len(parts) > 1 else ""
        return {"tool": "exec", "command": cmd}
    return None

if __name__ == "__main__":
    import sys, json
    user_input = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else ""
    decision = decide_tool(user_input)
    print(json.dumps(decision, ensure_ascii=False))
