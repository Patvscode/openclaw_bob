// src/agent/utils.ts
/**
 * Utility helpers for dealing with agent files and metadata.
 *
 * The original project expects the following public symbols:
 *   - `getAgentIdFromPath(path: string): string`
 *   - `readAgentMeta(dir: string): Promise<AgentMeta>`
 *   - `isAgentEnabled(meta: AgentMeta): boolean`
 *   - `loadAgentInfo(dir: string): Promise<[string, AgentMeta] | null>`
 *
 * They are used by the gateway, the UI and the auto‑reply subsystem to
 * locate agents, read their `_meta.json` files and decide whether the
 * agent should be considered active.
 */

import { promises as fs } from "node:fs";
import * as path from "node:path";

export interface AgentMeta {
  /** Unique identifier for the agent – usually a UUID string */
  id: string;
  /** Human‑readable name displayed in the UI */
  name: string;
  /** If true the agent is loaded by the gateway */
  enabled?: boolean;
  /** Arbitrary extra fields that agents may store */
  [key: string]: unknown;
}

/**
 * Extract the agent‑id from a file system path.
 *
 * The convention used throughout the code‑base is:
 *   /some/root/agents/<agent‑id>/...
 * If the path does not contain a segment that looks like an ID we fall
 * back to an empty string – callers treat that as “no id found”.
 */
export function getAgentIdFromPath(p: string): string {
  const parts = p.split(path.sep);
  // Find the segment that matches the typical UUID/number pattern.
  // We keep the check deliberately permissive – any non‑empty segment
  // after a folder named “agents” (or “agent”) is considered an ID.
  const idx = parts.findIndex(
    (seg) => seg === "agents" || seg === "agent" || seg === "agents.js",
  );
  if (idx >= 0 && idx + 1 < parts.length) {
    return parts[idx + 1];
  }
  // As a fallback, try the last path component (useful for bundled
  // snapshots where the ID is the filename without extension).
  const base = path.basename(p, path.extname(p));
  return base;
}

/**
 * Read the `_meta.json` file located in an agent directory.
 *
 * The function returns a fully typed `AgentMeta` object.  If the file
 * cannot be read or parsed, an empty object is returned – the caller
 * can decide whether that means “disabled” or “invalid”.
 */
export async function readAgentMeta(dir: string): Promise<AgentMeta> {
  const metaPath = path.join(dir, "_meta.json");
  try {
    const raw = await fs.readFile(metaPath, "utf8");
    const parsed = JSON.parse(raw);
    // Ensure the required `id` field exists; otherwise treat as empty.
    if (typeof parsed.id !== "string" || parsed.id.length === 0) {
      return {} as AgentMeta;
    }
    return parsed as AgentMeta;
  } catch {
    // Missing file, permission error, malformed JSON – return a blank meta.
    return {} as AgentMeta;
  }
}

/**
 * Determines whether an agent should be considered enabled.
 *
 * The rule is simple: if the `enabled` flag is explicitly `false` the
 * agent is disabled; otherwise it is enabled (including when the flag
 * is omitted).
 */
export function isAgentEnabled(meta: AgentMeta): boolean {
  return meta.enabled !== false;
}

/**
 * Convenience wrapper used by many callers – given a directory path
 * return a tuple `[id, meta]` if the agent can be loaded, otherwise
 * `null`.
 */
export async function loadAgentInfo(
  dir: string,
): Promise<[string, AgentMeta] | null> {
  const id = getAgentIdFromPath(dir);
  if (!id) return null;

  const meta = await readAgentMeta(dir);
  if (!isAgentEnabled(meta)) return null;

  return [id, meta];
}

/* ------------------------------------------ *
 *  Unit‑tests for the new utilities (run with `npm test` or `yarn test`)
 * ------------------------------------------ */
if (import.meta?.env?.NODE_ENV === "test") {
  (async () => {
    const assert = (cond: unknown, msg: string) => {
      if (!cond) throw new Error(`Assertion failed: ${msg}`);
    };

    // getAgentIdFromPath
    assert(
      getAgentIdFromPath("/tmp/agents/12345/config.json") === "12345",
      "extracts id from path",
    );
    assert(
      getAgentIdFromPath("C:\\workspace\\agents\\my-agent\\_meta.json") ===
        "my-agent",
      "works on Windows paths",
    );

    // isAgentEnabled
    assert(isAgentEnabled({ id: "x", name: "x" }) === true, "default enabled");
    assert(
      isAgentEnabled({ id: "x", name: "x", enabled: false }) === false,
      "explicitly disabled",
    );
  })();
}
