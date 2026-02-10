# ──────────────────────────────────────────────────────────────────────
# app.py  –  Co‑Bench: a fully‑integrated Streamlit UI for OpenClause
# ──────────────────────────────────────────────────────────────────────
import os
import subprocess
import time
import json
from pathlib import Path

import pandas as pd
import streamlit as st

# --------------------------------------------------------------
# Helper: run a shell command (sandboxed, short timeout)
# --------------------------------------------------------------
def run_cmd(command: str) -> str:
    """Execute a command inside the workspace and return stdout (or error)."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=os.getcwd(),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=10,
            check=False,
            text=True,
        )
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return "⏱️ Command timed out."
    except Exception as e:
        return f"❗️ {e}"

# --------------------------------------------------------------
# Page configuration (named Co‑Bench)
# --------------------------------------------------------------
st.set_page_config(
    page_title="Co‑Bench",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🧑‍🤝‍🧑 **Co‑Bench** – OpenClause Integrated Dashboard")
st.caption(
    "All‑in‑one UI for browsing files, watching background jobs, "
    "sending prompts to the OpenClause agent, and running quick shell commands."
)

# --------------------------------------------------------------
# Sidebar – global controls
# --------------------------------------------------------------
with st.sidebar:
    st.header("🔧 Global Controls")

    # CSV loader
    csv_path = st.text_input(
        "Path to CSV (relative to workspace)",
        value="sample.csv",
        help="Leave empty to just browse files.",
    )

    # Age filter (only shown if CSV has an `age` column)
    age_filter = st.slider(
        "Maximum age",
        min_value=0,
        max_value=120,
        value=120,
        help="Filter rows where `age` ≤ selected value (if `age` exists).",
    )

    # Message box – send to OpenClause agent
    user_msg = st.text_input(
        "💬 Prompt for OpenClause:",
        placeholder="Ask something …",
        key="prompt_box",
    )
    send_btn = st.button("Send ▶️")

    # Quick shell command
    quick_cmd = st.text_input(
        "⚡️ Quick shell command:",
        placeholder="e.g. `ls -l`",
        key="quick_cmd",
    )
    run_cmd_btn = st.button("Run command")

# --------------------------------------------------------------
# MAIN PANEL – File browser & CSV preview
# --------------------------------------------------------------
def list_workspace_files() -> pd.DataFrame:
    """Return a DataFrame with all files/folders under the workspace."""
    rows = []
    for root, dirs, files in os.walk('.'):
        for name in dirs + files:
            full_path = os.path.join(root, name)
            size = os.path.getsize(full_path) if os.path.isfile(full_path) else ""
            rows.append({
                "Path": full_path,
                "Type": "Folder" if os.path.isdir(full_path) else "File",
                "Size (bytes)": size,
            })
    return pd.DataFrame(rows)

st.subheader("📁 Workspace file browser")
file_df = list_workspace_files()
st.dataframe(file_df, use_container_width=True)

# --------------------------------------------------------------
# CSV loader (if a path was provided)
# --------------------------------------------------------------
if csv_path:
    @st.cache_data
    def load_csv(path: str) -> pd.DataFrame:
        try:
            return pd.read_csv(path)
        except Exception as e:
            st.error(f"❗️ Could not read **{path}** – {e}")
            return pd.DataFrame()

    df = load_csv(csv_path)

    if not df.empty:
        if "age" in df.columns:
            df["age"] = pd.to_numeric(df["age"], errors="coerce")
            df = df[df["age"] <= age_filter]
        st.subheader("📊 CSV preview (filtered)")
        st.dataframe(df, use_container_width=True)
    else:
        st.info("🗂️ No CSV data to display – check the path above.")

# --------------------------------------------------------------
# Echo the user message locally (just for sanity)
# --------------------------------------------------------------
if user_msg:
    st.markdown("**You typed:**")
    st.success(user_msg)

# --------------------------------------------------------------
# QUICK SHELL COMMAND RESULT
# --------------------------------------------------------------
if run_cmd_btn and quick_cmd:
    with st.spinner(f"Running `{quick_cmd}` …"):
        output = run_cmd(quick_cmd)
    st.subheader(f"🖥️ Output of `{quick_cmd}`")
    st.code(output, language="text")

# --------------------------------------------------------------
# INTEGRATION WITH OPENCLAUSE – SEND PROMPT & SHOW RESPONSE
# --------------------------------------------------------------
BRIDGE_FILE = Path("co_bench_bridge.json")

def write_prompt(prompt: str):
    payload = {"prompt": prompt, "timestamp": time.time()}
    BRIDGE_FILE.write_text(json.dumps(payload))

def read_reply(timeout: int = 10) -> str:
    start = time.time()
    while time.time() - start < timeout:
        if BRIDGE_FILE.exists():
            try:
                data = json.loads(BRIDGE_FILE.read_text())
                if "reply" in data:
                    BRIDGE_FILE.unlink(missing_ok=True)
                    return data["reply"]
            except Exception:
                pass
        time.sleep(0.5)
    return "⏳ No reply received (backend may be idle)."

if send_btn and user_msg:
    with st.spinner("Sending prompt to OpenClause…"):
        write_prompt(user_msg)
        reply = read_reply()
    st.subheader("🤖 OpenClause reply")
    st.success(reply)

# --------------------------------------------------------------
# BACKGROUND PROCESS LIST (full integration)
# --------------------------------------------------------------
st.subheader("⚙️ Running background jobs")
process_output = run_cmd("ps -eo pid,etime,cmd | grep streamlit | grep -v grep")
if process_output:
    rows = []
    for line in process_output.splitlines():
        parts = line.split(maxsplit=2)
        if len(parts) == 3:
            pid, etime, cmd = parts
            rows.append({"PID": pid, "Uptime": etime, "Command": cmd})
    proc_df = pd.DataFrame(rows)
    st.dataframe(proc_df, use_container_width=True)
else:
    st.info("No Streamlit background jobs found.")

st.caption(
    "Co‑Bench – your collaborative benchmarking & control panel for OpenClause. "
    "Run `./openclause_venv/bin/streamlit run app.py` to launch."
)
