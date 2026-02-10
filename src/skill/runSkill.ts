// src/skill/runSkill.ts
/**
 * Minimal execution shim for a discovered skill.
 *
 * A "skill" is any entry returned by `getSkills()` – either a script file
 * (`.py`, `.js`, etc.) or a folder that may contain an executable script.
 *
 * This shim does **not** provide sandboxing or security checks – it simply
 * spawns a child process using the appropriate interpreter based on the file
 * extension. It is intended as the first step toward a usable system.
 */
import { spawn } from "node:child_process";
import * as path from "node:path";
import * as fs from "node:fs";

/**
 * Resolve the actual executable file for a skill entry.
 *   - If the entry is a file, use it directly.
 *   - If the entry is a directory, look for a conventional entry point:
 *       index.js, main.js, index.py, main.py
 *   - If none found, return null.
 */
function resolveExecutable(entryPath: string): string | null {
  const stat = fs.statSync(entryPath, { throwIfNoEntry: false });
  if (!stat) return null;
  if (stat.isFile()) return entryPath;
  if (stat.isDirectory()) {
    const candidates = ["index.js", "main.js", "index.py", "main.py"];
    for (const c of candidates) {
      const candidatePath = path.join(entryPath, c);
      if (fs.existsSync(candidatePath) && fs.statSync(candidatePath).isFile()) {
        return candidatePath;
      }
    }
  }
  return null;
}

/**
 * Execute a skill.
 * @param entry Relative path to the skill (as returned by getSkills()).
 * @param args Optional array of string arguments passed to the script.
 * @returns An object containing exit code, stdout and stderr.
 */
export async function runSkill(entry: string, args: string[] = []): Promise<{
  code: number | null;
  stdout: string;
  stderr: string;
}> {
  const cwd = process.cwd();
  const absoluteEntry = path.resolve(cwd, entry);
  const execFile = resolveExecutable(absoluteEntry);
  if (!execFile) {
    console.error(`[runSkill] Unable to resolve executable for skill: ${entry}`);
    return { code: -1, stdout: "", stderr: `No executable found for ${entry}` };
  }

  const ext = path.extname(execFile).toLowerCase();
  let command: string;
  let commandArgs: string[] = [];
  switch (ext) {
    case ".py":
      command = "python3"; // assumes python3 is in PATH
      commandArgs = [execFile, ...args];
      break;
    case ".js":
      command = "node";
      commandArgs = [execFile, ...args];
      break;
    default:
      console.error(`[runSkill] Unsupported file type: ${execFile}`);
      return { code: -1, stdout: "", stderr: `Unsupported skill type ${execFile}` };
  }

  return new Promise((resolve) => {
    const child = spawn(command, commandArgs, { cwd: process.cwd(), shell: false });
    let stdout = "";
    let stderr = "";
    child.stdout.setEncoding("utf8");
    child.stderr.setEncoding("utf8");
    child.stdout.on("data", (data) => (stdout += data));
    child.stderr.on("data", (data) => (stderr += data));
    child.on("close", (code) => {
      console.log(`[runSkill] Executed ${entry} -> exit ${code}`);
      if (stdout) console.log(`[runSkill][stdout]\n${stdout}`);
      if (stderr) console.error(`[runSkill][stderr]\n${stderr}`);
      resolve({ code, stdout, stderr });
    });
    child.on("error", (err) => {
      console.error(`[runSkill] Failed to start ${entry}:`, err);
      resolve({ code: -1, stdout: "", stderr: String(err) });
    });
  });
}

// Export a tiny self‑test when executed directly via `node -r ts-node/register src/skill/runSkill.ts`
if (import.meta?.url?.endsWith("runSkill.ts")) {
  (async () => {
    // Example: run the first discovered skill (if any)
    const { getSkills } = await import("./utils");
    const skills = await getSkills();
    if (skills.length) {
      console.log("Running skill", skills[0]);
      const result = await runSkill(skills[0]);
      console.log("Result:", result);
    } else {
      console.log("No skills discovered – nothing to run.");
    }
  })();
}
