import sys, pathlib

if len(sys.argv) < 2:
    print("Usage: add_task.py <task description>")
    sys.exit(1)

task = " ".join(sys.argv[1:])
mem = pathlib.Path("MEMORY.md")
with mem.open("a", encoding="utf-8") as f:
    f.write(f"\n- [ ] {task}\n")
print(f"Task added: {task}")
