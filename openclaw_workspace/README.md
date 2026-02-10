# OpenClaw Local Workspace

This folder is the **shared, persistent, modular workspace** you described. It contains a minimal, extensible structure that can evolve over time while keeping all artifacts local and version‑controlled.

```
openclaw_workspace/
├─ library/      # Stored apps, tools, data, snapshots, etc.
├─ skills/       # Modular "skills" – Python modules that implement features.
├─ settings/     # Configuration, permissions, lock files.
├─ runtime/      # Runtime helpers (CLI, snapshot manager, etc.)
└─ workspace.json# Core metadata (name, version, persistence flags)
```

## Core Concepts
- **Persistence & Locking** – Controlled via `settings/persistence.json` and `settings/lock.json`.
- **Snapshots** – `runtime/snapshot.py` can capture the entire workspace into `library/snapshots/` and restore safely.
- **Skill Management** – `runtime/skill_manager.py` lets you add, list, run, and remove skills dynamically.
- **Modular Evolution** – New folders/files can be added without breaking existing tools.

All operations are performed through the **CLI** in `runtime/manage.py`.  Run `python manage.py --help` for usage.

---
*This workspace is fully local; nothing is sent outside unless you explicitly add networking code in a skill.*