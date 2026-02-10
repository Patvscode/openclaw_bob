// src/skill/utils.ts
/**
 * Utility helpers for discovering skill files within the workspace.
 *
 * A "skill" is any file or directory directly under the top‑level `skills`
 * folder.  For now we treat both scripts (e.g., .py, .js) and sub‑folders
 * (which may contain additional resources) as discoverable skill entries.
 *
 * The function returns a simple array of relative paths (from the workspace
 * root) so callers can later decide how to load/execute them.
 */
import { promises as fs } from "node:fs";
import * as path from "node:path";

/**
 * List skill entries.
 * @param workspaceRoot Absolute path to the workspace root. Defaults to the
 *   current working directory (process.cwd()).
 * @returns Array of skill entry paths relative to the workspace root.
 */
export async function getSkills(workspaceRoot: string = process.cwd()): Promise<string[]> {
  const skillsDir = path.join(workspaceRoot, "skills");
  try {
    const entries = await fs.readdir(skillsDir);
    // Filter out hidden files (starting with .) – they are not intended as skills.
    return entries.filter((e) => !e.startsWith(".")).map((e) => path.join("skills", e));
  } catch (err) {
    // If the directory does not exist we return an empty list; callers can
    // treat this as “no skills discovered”.
    return [];
  }
}

// Simple self‑test when run directly via `node -r esm src/skill/utils.ts`.
export function getSkillNameFromPath(filePath: string): string {
  // Normalize the path to resolve any relative components (., ..) and ensure
  // consistent separators across platforms.
  const normalized = path.normalize(filePath);
  const parts = normalized.split(path.sep);
  const idx = parts.indexOf('skills');
  if (idx >= 0 && parts.length > idx + 1) {
    const candidate = parts[idx + 1];
    // If the candidate is a file (has an extension), return the name without
    // the extension; otherwise return the directory name as‑is.
    const parsed = path.parse(candidate);
    return parsed.name; // works for both files and directories
  }
  return '';
}

if (import.meta?.url?.endsWith("utils.ts")) {
  (async () => {
    const list = await getSkills();
    console.log("Discovered skills:", list);
  })();
}
