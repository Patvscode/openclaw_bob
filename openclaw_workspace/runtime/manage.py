#!/usr/bin/env python3
"""OpenClaw Workspace Management CLI

Usage examples:
  python manage.py skill add hello_world "print('Hello, OpenClaw!')"
  python manage.py skill run hello_world
  python manage.py snapshot create "Initial snapshot"
  python manage.py snapshot list
  python manage.py snapshot restore <snapshot-id>
  python manage.py lock set "Maintenance"   # lock the workspace
  python manage.py lock release

All commands operate on the local `openclaw_workspace` directory.
"""
import argparse, json, os, shutil, sys, datetime, uuid, importlib.util, subprocess

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WORKSPACE_DIR = os.path.join(BASE_DIR, 'openclaw_workspace')
SETTINGS_DIR = os.path.join(WORKSPACE_DIR, 'settings')
LIBRARY_DIR = os.path.join(WORKSPACE_DIR, 'library')
SKILLS_DIR = os.path.join(WORKSPACE_DIR, 'skills')
SNAPSHOTS_DIR = os.path.join(LIBRARY_DIR, 'snapshots')

def load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, 'r') as f:
        return json.load(f)

def save_json(data, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# ---------- Persistence / Locking ----------
def is_locked():
    lock = load_json(os.path.join(SETTINGS_DIR, 'lock.json'))
    return lock.get('locked', False)

def require_unlocked():
    if is_locked():
        sys.exit('Workspace is locked. Unlock before performing this operation.')

def lock_workspace(reason):
    lock = {
        "locked": True,
        "reason": reason,
        "lockedBy": os.getenv('USER') or 'unknown',
        "timestamp": datetime.datetime.utcnow().isoformat() + 'Z'
    }
    save_json(lock, os.path.join(SETTINGS_DIR, 'lock.json'))
    print('Workspace locked:', reason)

def unlock_workspace():
    lock = {
        "locked": False,
        "reason": None,
        "lockedBy": None,
        "timestamp": None
    }
    save_json(lock, os.path.join(SETTINGS_DIR, 'lock.json'))
    print('Workspace unlocked')

# ---------- Skill Management ----------
def skill_path(name):
    return os.path.join(SKILLS_DIR, f"{name}.py")

def add_skill(name, code):
    require_unlocked()
    os.makedirs(SKILLS_DIR, exist_ok=True)
    path = skill_path(name)
    if os.path.exists(path):
        sys.exit(f'Skill "{name}" already exists. Use "skill update" to modify.')
    with open(path, 'w') as f:
        f.write('# Auto‑generated skill\n')
        f.write(code)
    print(f'Skill "{name}" created at {path}')

def list_skills():
    if not os.path.isdir(SKILLS_DIR):
        print('No skills directory yet.')
        return
    files = [f[:-3] for f in os.listdir(SKILLS_DIR) if f.endswith('.py')]
    for s in sorted(files):
        print('- ', s)

def run_skill(name, args=None):
    path = skill_path(name)
    if not os.path.exists(path):
        sys.exit(f'Skill "{name}" not found.')
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:
        sys.exit(f'Error loading skill "{name}": {e}')
    # If the skill defines a main() function, call it.
    if hasattr(mod, 'main'):
        try:
            if args is None:
                mod.main()
            else:
                mod.main(*args)
        except Exception as e:
            sys.exit(f'Error executing skill "{name}": {e}')
    else:
        # Run the file as a script via subprocess for maximum compatibility.
        subprocess.run([sys.executable, path] + (args or []), check=True)

# ---------- Snapshot Management ----------
def ensure_snapshot_dir():
    os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

def create_snapshot(message):
    require_unlocked()
    ensure_snapshot_dir()
    snap_id = str(uuid.uuid4())
    timestamp = datetime.datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    snap_name = f"{timestamp}_{snap_id}"
    dest = os.path.join(SNAPSHOTS_DIR, snap_name)
    shutil.copytree(WORKSPACE_DIR, dest, dirs_exist_ok=True)
    meta = {
        "id": snap_id,
        "name": snap_name,
        "message": message,
        "created": datetime.datetime.utcnow().isoformat() + 'Z'
    }
    save_json(meta, os.path.join(dest, 'snapshot_meta.json'))
    print('Snapshot created:', snap_name)

def list_snapshots():
    ensure_snapshot_dir()
    snaps = sorted(os.listdir(SNAPSHOTS_DIR))
    if not snaps:
        print('No snapshots stored.')
        return
    for s in snaps:
        meta_path = os.path.join(SNAPSHOTS_DIR, s, 'snapshot_meta.json')
        meta = load_json(meta_path)
        print(f"* {s} – {meta.get('message','')} (created {meta.get('created')})")

def restore_snapshot(snap_name):
    require_unlocked()
    src = os.path.join(SNAPSHOTS_DIR, snap_name)
    if not os.path.isdir(src):
        sys.exit(f'Snapshot "{snap_name}" not found.')
    # Remove current workspace (except the .snapshots folder) and copy back.
    for item in os.listdir(WORKSPACE_DIR):
        if item == 'library' and os.path.isdir(os.path.join(WORKSPACE_DIR, 'library', 'snapshots')):
            continue  # keep the snapshots folder itself
        p = os.path.join(WORKSPACE_DIR, item)
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)
    shutil.copytree(src, WORKSPACE_DIR, dirs_exist_ok=True)
    print('Workspace restored to snapshot', snap_name)

# ---------- Argument Parsing ----------
def main():
    parser = argparse.ArgumentParser(prog='manage.py')
    sub = parser.add_subparsers(dest='command')

    # skill sub‑commands
    skill_parser = sub.add_parser('skill', help='Skill operations')
    skill_sub = skill_parser.add_subparsers(dest='action')
    skill_add = skill_sub.add_parser('add', help='Add a new skill')
    skill_add.add_argument('name')
    skill_add.add_argument('code', help='Python code string (no surrounding quotes needed)')
    skill_update = skill_sub.add_parser('update', help='Update an existing skill')
    skill_update.add_argument('name')
    skill_update.add_argument('code')
    skill_sub.add_parser('list', help='List all available skills')
    skill_run = skill_sub.add_parser('run', help='Run a skill')
    skill_run.add_argument('name')
    skill_run.add_argument('args', nargs='*', help='Optional arguments passed to the skill')

    # snapshot sub‑commands
    snap_parser = sub.add_parser('snapshot', help='Snapshot operations')
    snap_sub = snap_parser.add_subparsers(dest='action')
    snap_create = snap_sub.add_parser('create', help='Create a snapshot')
    snap_create.add_argument('message', nargs='?', default='')
    snap_sub.add_parser('list', help='List stored snapshots')
    snap_restore = snap_sub.add_parser('restore', help='Restore a snapshot')
    snap_restore.add_argument('name')

    # lock sub‑commands
    lock_parser = sub.add_parser('lock', help='Locking operations')
    lock_sub = lock_parser.add_subparsers(dest='action')
    lock_set = lock_sub.add_parser('set', help='Lock the workspace')
    lock_set.add_argument('reason')
    lock_sub.add_parser('release', help='Unlock the workspace')

    args = parser.parse_args()

    if args.command == 'skill':
        if args.action == 'add':
            add_skill(args.name, args.code)
        elif args.action == 'update':
            require_unlocked()
            path = skill_path(args.name)
            with open(path, 'w') as f:
                f.write('# Updated skill\n')
                f.write(args.code)
            print(f'Skill "{args.name}" updated.')
        elif args.action == 'list':
            list_skills()
        elif args.action == 'run':
            run_skill(args.name, args.args)
        else:
            parser.print_help()
    elif args.command == 'snapshot':
        if args.action == 'create':
            create_snapshot(args.message)
        elif args.action == 'list':
            list_snapshots()
        elif args.action == 'restore':
            restore_snapshot(args.name)
        else:
            parser.print_help()
    elif args.command == 'lock':
        if args.action == 'set':
            lock_workspace(args.reason)
        elif args.action == 'release':
            unlock_workspace()
        else:
            parser.print_help()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
