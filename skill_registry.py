import pathlib, subprocess, shlex, json, os

SKILL_DIR = pathlib.Path("skills")

def list_skills() -> list:
    return [p.stem for p in SKILL_DIR.iterdir() if p.is_file() and os.access(p, os.X_OK)]

def run_skill(name: str, args: str):
    script_path = SKILL_DIR / f"{name}.py"
    if not script_path.exists():
        return {"error": f"Skill '{name}' not found"}
    # Execute the script with the provided arguments
    cmd = [sys.executable, str(script_path)] + shlex.split(args)
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return {"stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode}

if __name__ == "__main__":
    import sys, json
    if len(sys.argv) < 3:
        print(json.dumps({"error": "Usage: skill_registry.py <skill_name> <args>"}))
        sys.exit(1)
    skill_name = sys.argv[1]
    skill_args = " ".join(sys.argv[2:])
    out = run_skill(skill_name, skill_args)
    print(json.dumps(out, ensure_ascii=False, indent=2))
