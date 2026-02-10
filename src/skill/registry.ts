// src/skill/registry.ts
/**
 * Simple in‑memory registry for discovered skills.
 *
 * It loads the skill list once (typically at gateway start‑up) and provides
 * read‑only access for the rest of the system. No persistence is added at this
 * stage – the list is rebuilt on every process start.
 */
import { getSkills } from "./utils";

let cachedSkills: string[] | null = null;

/** Load and cache the discovered skills. */
export async function initSkillRegistry(): Promise<string[]> {
  if (!cachedSkills) {
    cachedSkills = await getSkills();
    console.log(`[skillRegistry] Loaded ${cachedSkills.length} skill(s).`);
  }
  return cachedSkills;
}

/** Return the current in‑memory list (empty array if not initialised). */
export function getRegisteredSkills(): string[] {
  return cachedSkills ?? [];
}

/** Force a refresh – useful for development when new skills are added. */
export async function refreshSkills(): Promise<string[]> {
  cachedSkills = await getSkills();
  console.log(`[skillRegistry] Refreshed – ${cachedSkills.length} skill(s).`);
  return cachedSkills;
}
