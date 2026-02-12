# Credibility Scorer

This skill provides a deterministic heuristic to evaluate the trustworthiness of a URL.

## Quick Start
```bash
# Install dependencies (if running locally)
pip install -r requirements.txt

# Example usage (from command line)
echo '{"url": "https://www.nytimes.com/2024/01/15/science/space/"}' | python credibility_scorer.py
```

The script reads a JSON object with a single key `url` from **stdin** and prints a JSON result containing:
- `score` (0‑1)
- `verdict` (High/Medium/Low)
- `details` (breakdown of each weighted signal)

## Integration
Other skills can invoke this scorer by spawning an isolated session and feeding the URL JSON payload, or by using the built‑in `sessions_send` tool.

## Extensibility
- Adjust `WEIGHTS` in `credibility_scorer.py` to fine‑tune importance of each signal.
- Replace placeholder functions with real WHOIS, traffic‑rank, or bias‑rating APIs for higher fidelity.
