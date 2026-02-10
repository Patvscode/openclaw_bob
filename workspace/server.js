const express = require('express');
const http = require('http');
const path = require('path');
const fs = require('fs');
const socketIo = require('socket.io');

const app = express();
const server = http.createServer(app);
const io = socketIo(server);

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Helper to read/write JSON meta files
function readMeta(file) {
  try { return JSON.parse(fs.readFileSync(file, 'utf8')); } catch (e) { return []; }
}
function writeMeta(file, data) {
  fs.writeFileSync(file, JSON.stringify(data, null, 2), 'utf8');
}

// ---------- Library API ----------
// ------------------------------------------------------------
// Library API
// ------------------------------------------------------------
// Get list of library items (metadata only)
app.get('/api/library', (req, res) => {
  try {
    const meta = readMeta(path.join(__dirname, 'library', 'meta.json'));
    res.json(meta);
  } catch (err) {
    console.error('Error fetching library list:', err);
    res.status(500).json({ error: 'Failed to read library metadata' });
  }
});

// Create a new library item. Expects JSON body with `name`, `type`, and optional `code`.
app.post('/api/library', (req, res) => {
  try {
    const { name, type, code } = req.body;
    if (!name || !type) return res.status(400).json({ error: 'name and type required' });
    const libDir = path.join(__dirname, 'library');
    if (!fs.existsSync(libDir)) fs.mkdirSync(libDir);
    const metaPath = path.join(libDir, 'meta.json');
    const meta = readMeta(metaPath);
    const id = Date.now().toString();
    const item = { id, name, type, locked: false };
    meta.push(item);
    writeMeta(metaPath, meta);
    if (code) {
      const filePath = path.join(libDir, `${id}.js`);
      fs.writeFileSync(filePath, code, 'utf8');
    }
    res.json(item);
  } catch (err) {
    console.error('Error creating library item:', err);
    res.status(500).json({ error: 'Failed to create library item' });
  }
});

// Retrieve the source code for a specific library item by its ID.
app.get('/api/library/:id', (req, res) => {
  try {
    const { id } = req.params;
    const filePath = path.join(__dirname, 'library', `${id}.js`);
    if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'not found' });
    const code = fs.readFileSync(filePath, 'utf8');
    res.json({ code });
  } catch (err) {
    console.error('Error reading library item:', err);
    res.status(500).json({ error: 'Failed to read library item' });
  }
});

// Delete a library item. Prevent deletion if the item is locked.
app.delete('/api/library/:id', (req, res) => {
  try {
    const { id } = req.params;
    const libDir = path.join(__dirname, 'library');
    const metaPath = path.join(libDir, 'meta.json');
    const meta = readMeta(metaPath);
    const index = meta.findIndex(i => i.id === id);
    if (index === -1) return res.status(404).json({ error: 'not found' });
    if (meta[index].locked) return res.status(403).json({ error: 'locked' });
    meta.splice(index, 1);
    writeMeta(metaPath, meta);
    const filePath = path.join(libDir, `${id}.js`);
    if (fs.existsSync(filePath)) fs.unlinkSync(filePath);
    res.json({ deleted: true });
  } catch (err) {
    console.error('Error deleting library item:', err);
    res.status(500).json({ error: 'Failed to delete library item' });
  }
});

// Execute the `run` export of a library module.
app.post('/api/library/:id/run', async (req, res) => {
  try {
    const { id } = req.params;
    const filePath = path.join(__dirname, 'library', `${id}.js`);
    if (!fs.existsSync(filePath)) return res.status(404).json({ error: 'code not found' });
    delete require.cache[require.resolve(filePath)];
    const mod = require(filePath);
    if (typeof mod.run !== 'function') return res.status(400).json({ error: 'module must export run' });
    const result = await mod.run();
    res.json({ result });
  } catch (e) {
    console.error('Error running library code:', e);
    res.status(500).json({ error: e.message, stack: e.stack });
  }
});

// ---------- Skills API ----------
// ------------------------------------------------
// Skills API
// ------------------------------------------------
// List all available skills (metadata only).
app.get('/api/skills', (req, res) => {
  try {
    const meta = readMeta(path.join(__dirname, 'skills', 'meta.json'));
    res.json(meta);
  } catch (err) {
    console.error('Error fetching skills list:', err);
    res.status(500).json({ error: 'Failed to read skills metadata' });
  }
});

// Create a new skill. Requires `name` and `type`. Optional `code` can be provided.
app.post('/api/skills', (req, res) => {
  try {
    const { name, type, code } = req.body;
    if (!name || !type) return res.status(400).json({ error: 'name and type required' });
    const skillsDir = path.join(__dirname, 'skills');
    if (!fs.existsSync(skillsDir)) fs.mkdirSync(skillsDir);
    const metaPath = path.join(skillsDir, 'meta.json');
    const meta = readMeta(metaPath);
    const id = Date.now().toString();
    const item = { id, name, type, locked: false };
    meta.push(item);
    writeMeta(metaPath, meta);
    if (code) {
      const filePath = path.join(skillsDir, `${id}.js`);
      fs.writeFileSync(filePath, code, 'utf8');
    }
    res.json(item);
  } catch (err) {
    console.error('Error creating skill:', err);
    res.status(500).json({ error: 'Failed to create skill' });
  }
});

app.post('/api/skills/:name/run', (req, res) => {
  const {name} = req.params;
  const {message} = req.body;
  const skillFile = path.join(__dirname, 'skills', `${name}.js`);
  if (!fs.existsSync(skillFile)) return res.status(404).json({error: 'skill not found'});
  const skill = require(skillFile);
  if (typeof skill.run !== 'function') return res.status(400).json({error: 'invalid skill'});
  // Emit result via socket when ready
  skill.run(message).then(out => {
    io.emit('skill result', out);
    res.json({output: out});
  }).catch(err => {
    res.status(500).json({error: err.message});
  });
});

// ---------- Settings API ----------
app.get('/api/settings', (req, res) => {
  const settingsPath = path.join(__dirname, 'settings.json');
  if (!fs.existsSync(settingsPath)) return res.json({});
  const data = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
  res.json(data);
});
app.post('/api/settings', (req, res) => {
  const settingsPath = path.join(__dirname, 'settings.json');
  writeMeta(settingsPath, req.body);
  res.json({saved: true});
});

// ---------- Snapshot API ----------
app.post('/api/snapshot', (req, res) => {
  const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
  const snapshotName = `snapshot-${timestamp}`;
  const src = __dirname;
  const dest = path.join(__dirname, '..', 'snapshots', snapshotName);
  // simple copy of workspace folder
  const copy = (srcDir, destDir) => {
    if (!fs.existsSync(destDir)) fs.mkdirSync(destDir, {recursive:true});
    fs.readdirSync(srcDir).forEach(item => {
      const srcPath = path.join(srcDir, item);
      const destPath = path.join(destDir, item);
      const stat = fs.statSync(srcPath);
      if (stat.isDirectory()) copy(srcPath, destPath);
      else fs.copyFileSync(srcPath, destPath);
    });
  };
  copy(src, dest);
  res.json({snapshot: snapshotName});
});

app.get('/api/snapshots', (req, res) => {
  const snapsDir = path.join(__dirname, '..', 'snapshots');
  if (!fs.existsSync(snapsDir)) return res.json([]);
  const list = fs.readdirSync(snapsDir).filter(f => fs.statSync(path.join(snapsDir, f)).isDirectory());
  res.json(list);
});

app.post('/api/rollback', (req, res) => {
  const {snapshot} = req.body;
  if (!snapshot) return res.status(400).json({error: 'snapshot required'});
  const snapsDir = path.join(__dirname, '..', 'snapshots', snapshot);
  if (!fs.existsSync(snapsDir)) return res.status(404).json({error: 'snapshot not found'});
  // replace current workspace with snapshot contents
  const copy = (srcDir, destDir) => {
    // clear dest
    if (fs.existsSync(destDir)) {
      fs.rmdirSync(destDir, {recursive:true});
    }
    fs.mkdirSync(destDir, {recursive:true});
    fs.readdirSync(srcDir).forEach(item => {
      const srcPath = path.join(srcDir, item);
      const destPath = path.join(destDir, item);
      const stat = fs.statSync(srcPath);
      if (stat.isDirectory()) copy(srcPath, destPath);
      else fs.copyFileSync(srcPath, destPath);
    });
  };
  copy(snapsDir, __dirname);
  res.json({rolledBack: snapshot});
});

// ---------- Settings endpoint (fallback) ----------
app.get('/api/settings', (req, res) => {
  const settingsPath = path.join(__dirname, 'settings.json');
  if (!fs.existsSync(settingsPath)) return res.json({});
  const data = JSON.parse(fs.readFileSync(settingsPath, 'utf8'));
  res.json(data);
});

// ---------- Root ----------
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'workspace.html'));
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => {
  console.log(`Workspace server listening on http://localhost:${PORT}`);
});
