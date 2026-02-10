import sys, json, subprocess, shlex, pathlib

# Load the decision engine (same logic as auto_tool.py) but expose it as a function

def decide_tool(user_msg: str):
    import re
    SEARCH_KEYWORDS = r"\b(latest|current|today|news|price|forecast|who|what|when|where|how)\b"
    FETCH_KEYWORDS = r"\b(pdf|report|article|doc|download|link)\b"
    EXEC_KEYWORDS = r"\b(run|execute|script|bash|python)\b"
    msg = user_msg.lower()
    if re.search(SEARCH_KEYWORDS, msg):
        return {"tool": "web_search", "query": user_msg}
    if re.search(FETCH_KEYWORDS, msg):
        words = user_msg.split()
        for w in words:
            if w.startswith('http://') or w.startswith('https://'):
                return {"tool": "web_fetch", "url": w}
        return {"tool": "web_fetch", "url": user_msg}
    if re.search(EXEC_KEYWORDS, msg):
        parts = user_msg.split(None, 1)
        cmd = parts[1] if len(parts) > 1 else ""
        return {"tool": "exec", "command": cmd}
    return None

def invoke_tool(decision: dict):
    """Dispatch to the appropriate OpenClaw tool.
    Returns the raw result (string or JSON) and a description.
    """
    tool = decision.get("tool")
    if tool == "web_search":
        # Use the built‑in web_search tool via the OpenClaw API
        query = decision.get("query", "")
        result = subprocess.run(
            ["openclaw", "web_search", "--query", query],
            capture_output=True,
            text=True,
        )
        return {"tool": "web_search", "output": result.stdout}
    if tool == "web_fetch":
        url = decision.get("url", "")
        result = subprocess.run(
            ["openclaw", "web_fetch", "--url", url],
            capture_output=True,
            text=True,
        )
        return {"tool": "web_fetch", "output": result.stdout}
    if tool == "exec":
        cmd = decision.get("command", "")
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        return {"tool": "exec", "stdout": result.stdout, "stderr": result.stderr, "code": result.returncode}
    return {"error": "Unsupported tool"}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: process_message.py <message>"}))
        sys.exit(1)
    user_msg = " ".join(sys.argv[1:])
    decision = decide_tool(user_msg)
    if not decision:
        print(json.dumps({"tool": None, "message": "No tool needed", "original": user_msg}))
        sys.exit(0)
    result = invoke_tool(decision)
    # Append a short log entry to MEMORY.md for traceability
    mem_path = pathlib.Path("MEMORY.md")
    with mem_path.open("a", encoding="utf-8") as f:
        f.write(f"\n- Processed message: '{user_msg}' → {json.dumps(result, ensure_ascii=False)}\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))
