# Collab Runtime

A minimal **live‑coding collaborative runtime** built with React, Vite, and a lightweight Node.js backend.

## Features
- Dynamic UI panels (grid layout) that can be added/removed via a WebSocket API.
- Secure sandbox placeholder for executing user code (Python example).
- Persistent key‑value store (SQLite) and a simple file‑system API for a per‑session workspace.
- Extensible component system – currently ships with Monaco editor, iframe, and console log components.
- All assets served from a single `dist` folder; the backend also proxies Vite dev server during development.

## Getting Started
```bash
cd collab-runtime
npm install
npm run dev   # starts Vite dev server (http://localhost:3001)
# In another terminal:
node server.js # starts the backend WebSocket on port 3000
```
The frontend will connect to `ws://localhost:3000/ws` and listen for UI commands.

## API Overview
### UI Management (`/api/ui/*`)
- **POST** `/api/ui/addPanel` – payload `{id, x, y, w, h, title, componentSpec}`
- **POST** `/api/ui/removePanel` – payload `{id}`
- **POST** `/api/ui/updatePanel` – payload with any panel fields to update.

### File System (`/api/fs/*`)
- **GET** `/api/fs/list?path=.` – list directory entries.
- **GET** `/api/fs/read?path=relative/file.txt` – read file contents.
- **POST** `/api/fs/write` – `{path: 'relative/file.txt', content: '...'}`

### Key‑Value Store (`/api/kv/*`)
- **POST** `/api/kv/set` – `{key, value}`
- **GET** `/api/kv/get?key=yourKey`

### Code Execution (placeholder)
- **POST** `/api/run/python` – `{script, panelId}` creates a console panel showing the script.

## Extending Components
Add a new component to `src/DynamicHost.jsx` inside `componentWhitelist` and reference it from the back‑end UI commands.

---
*This repository is a starting point; the sandbox runner should be replaced with a proper Docker‑based isolated environment for production use.*
