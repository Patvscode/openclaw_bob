# Ongoing Issues: OpenClaw Gateway, Ollama, Telegram

Last updated: 2026-02-10

## Executive Summary

OpenClaw (`openclaw-gateway.service`) is running and listening locally, but user-visible reliability is degraded on Telegram.
The dominant failure mode is: the bot indicates typing (or partial output) and then never delivers a final response.
Logs show a repeating combination of:

- Telegram API calls failing with network errors (`sendChatAction`/`sendMessage`).
- Long-running agent executions timing out at ~20 minutes (`timeoutMs=1200000`), leading to aborted runs.
- Systemd restarts that do not fully clean up child processes (large cgroup with many long-lived subprocesses).
- Secondary configuration issues (invalid/placeholder API keys, invalid Brave token, Gmail watcher disabled due to missing topic).

This document captures the current observed state, evidence, and a prioritized fix/polish backlog.

## Observed Symptoms

- Telegram: "typing…" appears, then no final message arrives.
- Telegram: button interactions sometimes fail later with `answerCallbackQuery ... query is too old`.
- Overall: intermittent responsiveness; sometimes recovers after restart, sometimes not.

## Evidence (From Logs / Runtime)

### Current runtime snapshot (systemd)

- `openclaw-gateway.service` is **active (running)** and is listening on:
  - `ws://127.0.0.1:18789`
  - `ws://[::1]:18789`
- The unit currently has a **very large process tree** (hundreds of tasks) and has shown **very high memory peaks**.
  - This matches the "restart does not clean up child processes" symptom described below.

### Telegram transport failures

Repeated errors of the form:

- `telegram sendChatAction failed: Network request for 'sendChatAction' failed!`
- `telegram sendMessage failed: Network request for 'sendMessage' failed!`
- `telegram final reply failed: HttpError: Network request for 'sendMessage' failed!`
- `answerCallbackQuery failed ... query is too old and response timeout expired`

These correlate with the user-facing "typing but no response" symptom: if OpenClaw cannot reach Telegram reliably, it can compute a response but fail to deliver it.

### Agent execution timeouts / aborted runs

Repeated:

- `embedded run timeout ... timeoutMs=1200000`

This aligns with a hard execution cap around 20 minutes; when hit, the run ends as aborted and the final Telegram response may never be sent.

Configuration reference:

- `/home/pmello/.openclaw/openclaw.json` contains `agents.defaults.timeoutSeconds: 1200` (20 minutes).
- When the agent run times out, Telegram callback interactions can also fail later with `query is too old`.

Example (2026-02-10):

- DM run started at `2026-02-10T21:37:02Z`, then timed out at `2026-02-10T21:57:02Z` (`aborted=true`), followed by `answerCallbackQuery ... query is too old`.

### Group mention gating (Telegram)

Logs also show group traffic being skipped with:

- `skipping group message` with reason `no-mention`

This is expected behavior when group config requires mentions (see Telegram docs troubleshooting).

### Model selection noise / failovers

OpenClaw is configured with:

- Primary: `ollama/gpt-oss:120b-ctx131k`
  - Local Ollama shows a runner process active, so the model service itself appears to be up.

### Systemd restart behavior (resource cleanup)

The service cgroup contains many long-lived child processes (browser renderers, dev servers, etc.).
The unit file uses:

- `/home/pmello/.config/systemd/user/openclaw-gateway.service`: `KillMode=process`

With `KillMode=process`, restarting can leave the majority of the process tree alive, which accumulates load and can degrade responsiveness over time.

## Doc Cross-References (OpenClaw Telegram)

Primary doc: `/home/pmello/.openclaw/workspace/openclaw/docs/channels/telegram.md`

Key points that match observed failures:

- **Draft streaming**: Telegram DMs can stream partial replies via `sendMessageDraft`, then send the final reply as a normal message.
  - Config: `channels.telegram.streamMode` (`off | partial | block`, default `partial`).
  - If delivery is flaky, draft streaming increases outbound API traffic and can make failures feel like "typing forever".
- **Network request failures**: If logs include `HttpError: Network request ... failed`, the doc calls out IPv6/DNS as a common cause:
  - Some hosts resolve `api.telegram.org` to IPv6 first; if IPv6 egress is broken, grammY can get stuck/fail.
  - Suggested fix: enable IPv6 egress or force IPv4 resolution for `api.telegram.org`, then restart the gateway.
- **Group mention behavior**: If the bot doesn't respond in groups, check mention gating and BotFather privacy mode requirements.

## Other Config Items Currently Failing (Polish / Noise)

These do not directly explain Telegram non-delivery, but they generate errors and background retries:

- Memory embeddings sync failing with OpenAI 401 invalid API key:
  - `/home/pmello/.openclaw/openclaw.json`: `agents.defaults.memorySearch.remote.apiKey` (currently a placeholder).
- Web search failing with Brave token invalid (422):
  - `/home/pmello/.openclaw/openclaw.json`: `tools.web.search.provider=brave`, `tools.web.search.apiKey` (currently invalid).
- Gmail watcher not started because a topic is required:
  - `/home/pmello/.openclaw/openclaw.json`: `hooks.gmail` configured but missing a Pub/Sub topic field (log says "gmail topic required").
- Tool execution failures due to environment / permissions:
  - PEP 668 ("externally managed environment") when attempting system Python package installs.
  - Git operations failing because terminal prompts are disabled (no non-interactive auth).
  - Whisper-related paths/venv activation errors.

## Prioritized Fixes

### P0: Telegram delivery reliability

Goal: ensure OpenClaw can consistently reach `api.telegram.org` and complete requests fast enough to not age out callbacks.

Doc-backed checks to run on the host:

```bash
getent hosts api.telegram.org
curl -I https://api.telegram.org
curl -I https://1.1.1.1
```

If Telegram API calls are failing with `Network request ... failed`:

- Per `/home/pmello/.openclaw/workspace/openclaw/docs/channels/telegram.md`, the common cause is **IPv6-first DNS + broken IPv6 egress**.
- Fix by enabling IPv6 egress, or forcing IPv4 resolution for `api.telegram.org` in your OS DNS stack (or `/etc/hosts`), then restart the gateway.

Notes:

- Config knob exists: `channels.telegram.network.autoSelectFamily` (override Node autoSelectFamily), but the docs note the Node 22 default is disabled.
- Consider reducing outbound calls by disabling draft streaming:
  - Set `channels.telegram.streamMode: "off"` to send only final replies (no drafts).

### P0: Prevent long "typing forever" runs

Goal: avoid 20-minute agent runs that end in `aborted=true` and never deliver a final Telegram message.

Options (in order of likely impact):

- Reduce context size for Telegram (history limits) to keep prompts small and inference fast.
- Disable Telegram draft streaming (`channels.telegram.streamMode: "off"`) so users only see final replies.
- Consider switching Telegram to a faster model (or a "fast reply" model) so replies complete well under the timeout.

### P0: Make restarts actually reset the service

Change systemd kill mode so child processes are cleaned up on restart:

- In `/home/pmello/.config/systemd/user/openclaw-gateway.service`:
  - change `KillMode=process` to `KillMode=control-group` (or `mixed`)

This addresses the accumulating "538 tasks" symptom and reduces long-term drift.

### P1: Reduce background errors/noise

- Fix or disable embeddings sync:
  - Update `agents.defaults.memorySearch.remote.apiKey`, or disable remote embeddings/memory sync if not needed.
- Fix or disable Brave search:
  - Update `tools.web.search.apiKey`, or set `tools.web.search.enabled=false`.
- Gmail watcher:
  - Add the required topic config, or disable `hooks.gmail` if unused.

## Security / Operational Hygiene

`/home/pmello/.openclaw/openclaw.json` currently contains API keys and bot tokens, and logging is configured with:

- `logging.redactSensitive: "off"`

Recommend:

- Turn redaction on (`redactSensitive: "on"`) unless there is a strong reason not to.
- Ensure `openclaw.json` stays `0600` and is not copied into repos or shared logs.

## Changes Applied (2026-02-10)

These were applied to reduce Telegram payload size and avoid known model failovers:

- `/home/pmello/.openclaw/openclaw.json`
  - Ollama model `GPT-OSS 120B (ctx131k)` `maxTokens: 2000` (was `8192`).
  - `channels.telegram.textChunkLimit: 3500` (keep outbound messages safely under Telegram limits).
  - Removed the 8k context model from selection to stop predictable failover noise:
    - removed `gpt-oss:120b` from the Ollama model catalog selection
    - removed `ollama/gpt-oss:120b` from `agents.defaults.models`

## Quick Triage Checklist (When It "Stops Responding")

1. Check service status and task count:
   - `systemctl --user --no-pager --full status openclaw-gateway.service`
2. Check last 200 logs for Telegram errors and timeouts:
   - `journalctl --user -u openclaw-gateway.service -n 200 --no-pager`
3. Confirm Ollama is up and a runner is active when expected:
   - `ps -ef | rg \"ollama serve|ollama runner\"`
4. Confirm DNS/egress to Telegram:
   - `getent hosts api.telegram.org && curl -I https://api.telegram.org`
