import os
import sys
import time
import json
import hashlib

def file_hash(path):
    try:
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return None

def load_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def top_keys(data):
    if isinstance(data, dict):
        return set(data.keys())
    return set()

def compare_json(old, new):
    old_keys = top_keys(old)
    new_keys = top_keys(new)
    added = list(new_keys - old_keys)
    removed = list(old_keys - new_keys)
    changed = []
    for k in old_keys & new_keys:
        if old[k] != new[k]:
            changed.append(k)
    return added, removed, changed

root = sys.argv[1] if len(sys.argv) > 1 else '.'
prev_state = {}
prev_json = {}
start = time.time()
while True:
    # check elapsed time (24h)
    if time.time() - start > 86400:
        break
    current_state = {}
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                mtime = os.path.getmtime(path)
                size = os.path.getsize(path)
                current_state[path] = (mtime, size)
            except Exception:
                continue
    # detect created and modified
    for path, meta in current_state.items():
        if path not in prev_state:
            change_type = 'created'
        else:
            if meta != prev_state[path]:
                change_type = 'modified'
            else:
                continue  # unchanged
        info = {'path': path, 'type': change_type}
        if path.lower().endswith('.json'):
            new_json = load_json(path)
            old_json = prev_json.get(path)
            if new_json is not None:
                added, removed, changed = compare_json(old_json or {}, new_json)
                info['json_diff'] = {'added': added, 'removed': removed, 'changed': changed}
                prev_json[path] = new_json
        print(json.dumps(info, ensure_ascii=False))
        sys.stdout.flush()
    # detect deletions
    for path in set(prev_state) - set(current_state):
        info = {'path': path, 'type': 'deleted'}
        if path in prev_json:
            # remove stored json snapshot
            del prev_json[path]
        print(json.dumps(info, ensure_ascii=False))
        sys.stdout.flush()
    prev_state = current_state
    time.sleep(2)
