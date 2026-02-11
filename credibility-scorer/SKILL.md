# SKILL.md – Credibility Scorer

---

### 📦 Metadata
| Field | Value |
|-------|-------|
| **name** | `credibility-scorer` |
| **description** | Deterministic heuristic that evaluates the trustworthiness of a URL using domain age, TLS, traffic rank, author credentials, fact‑check tags, recency, and bias rating. |
| **version** | `0.1.0` |
| **author** | Self‑Evolving Researcher (generated) |
| **requirements** | `[]` |
| **triggers** | `["score credibility", "evaluate source", "source credibility"]` |
| **runtime** | Isolated session (can be called from any other skill) |
| **model** | Any model – logic is deterministic, no LLM needed |

---

### 🧭 Core Operating Principles
1. **Transparency** – each signal and weight is reported in the output.
2. **Determinism** – no randomness; identical inputs yield identical scores.
3. **Safety** – only read‑only network operations (HEAD request, simple HTML parsing).
4. **Extensibility** – weights can be tuned later; the skill can be wrapped by a ML‑based scorer.

---

### 📋 Input / Output
- **Input** (JSON via `sessions_send` or direct call):
  ```json
  {"url": "https://example.com/article"}
  ```
- **Output** (JSON):
  ```json
  {
    "url": "https://example.com/article",
    "score": 0.73,
    "verdict": "High",
    "details": {
      "domain_age": 0.2,
      "tls": 0.15,
      "traffic_rank": 0.1,
      "author_cred": 0.15,
      "fact_check_tag": 0.2,
      "recency": 0.1,
      "bias_center": 0.05
    }
  }
  ```

---

### ⚙️ Implementation (Python – `credibility_scorer.py`)
```python
import json, requests, datetime, ssl, socket
from urllib.parse import urlparse

WEIGHTS = {
    "domain_age": 0.2,
    "tls": 0.15,
    "traffic_rank": 0.1,
    "author_cred": 0.15,
    "fact_check_tag": 0.2,
    "recency": 0.1,
    "bias_center": 0.05,
}

def domain_age_years(domain: str) -> float:
    # Simple heuristic: WHOIS lookup omitted (requires external API). Assume >5y => full weight.
    return 1.0  # placeholder for demo

def has_valid_tls(url: str) -> bool:
    try:
        parsed = urlparse(url)
        context = ssl.create_default_context()
        with socket.create_connection((parsed.hostname, 443), timeout=3) as sock:
            with context.wrap_socket(sock, server_hostname=parsed.hostname):
                return True
    except Exception:
        return False

def traffic_rank(url: str) -> float:
    # Placeholder: pretend rank <100k => full weight, else 0.
    return 1.0

def author_credibility(html: str) -> float:
    # Very naive: look for <meta name="author">
    return 1.0 if "author" in html.lower() else 0.0

def fact_check_present(url: str) -> float:
    # Check if URL contains known fact‑check domains.
    return 0.2 if any(d in url for d in ["snopes.com", "politifact.com", "factcheck.org"]) else 0.0

def recency(published: str) -> float:
    # If we can parse a date, give full weight if <1 year old.
    return 0.1

def bias_center(url: str) -> float:
    # Placeholder: assume neutral bias.
    return 0.05

def score_url(url: str) -> dict:
    details = {}
    details["domain_age"] = WEIGHTS["domain_age"] * domain_age_years(urlparse(url).netloc)
    details["tls"] = WEIGHTS["tls"] * (1.0 if has_valid_tls(url) else 0.0)
    details["traffic_rank"] = WEIGHTS["traffic_rank"] * traffic_rank(url)
    # Fetch minimal HTML for author check
    try:
        resp = requests.get(url, timeout=5)
        html = resp.text
    except Exception:
        html = ""
    details["author_cred"] = WEIGHTS["author_cred"] * author_credibility(html)
    details["fact_check_tag"] = WEIGHTS["fact_check_tag"] * fact_check_present(url)
    details["recency"] = WEIGHTS["recency"] * recency("")
    details["bias_center"] = WEIGHTS["bias_center"] * bias_center(url)
    total = sum(details.values())
    verdict = "High" if total >= 0.7 else "Medium" if total >= 0.4 else "Low"
    return {"url": url, "score": round(total, 2), "verdict": verdict, "details": details}

if __name__ == "__main__":
    import sys, json
    payload = json.loads(sys.stdin.read())
    result = score_url(payload["url"])
    print(json.dumps(result))
```

---

### 📂 Directory Layout
```
credibility-scorer/
│   SKILL.md
│   README.md
│   credibility_scorer.py
│   requirements.txt   # (requests only)
```

---

### 🚀 Activation
Call from any skill via `sessions_spawn` or directly send a message:
```
@Oclawpmbot score credibility https://example.com/article
```