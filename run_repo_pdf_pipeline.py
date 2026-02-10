# Wrapper skill for autonomous repo + PDF pipeline
import json, os, subprocess, datetime

# The OpenClaw orchestrator will inject the real tool functions at runtime.
# For readability we refer to them via a generic "tools" namespace.

def load_state():
    # Pull the most recent state line from MEMORY.md for this pipeline
    entries = tools.memory_search(query="pipeline:repo-pdf-pipeline", maxResults=1, minScore=0.1)
    if not entries:
        return {"step": 1, "status": "init"}
    # entries[0]["content"] holds the JSON string
    try:
        return json.loads(entries[0]["content"])
    except Exception:
        return {"step": 1, "status": "init"}

def save_state(state):
    # Append a tiny JSON line to MEMORY.md – the orchestrator provides memory_write
    tools.memory_write(json=state)

def step_1_collect():
    results = tools.web_search(query="autonomous long-horizon OpenClaw", count=5)
    os.makedirs("project_artifacts", exist_ok=True)
    with open("project_artifacts/step_1_results.json", "w") as f:
        json.dump(results, f, indent=2)
    save_state({"pipeline": "repo-pdf-pipeline", "step": 2, "status": "search-done", "results": results})
    tools.telegram_send(text="✅ Day 1 completed – web‑search done. Next step tomorrow.")

def step_2_summarise():
    with open("project_artifacts/step_1_results.json") as f:
        raw = json.load(f)
    prompt = "Summarise each of the following web‑search results in one short paragraph."
    summary = tools.run_llm(prompt=prompt, input=json.dumps(raw))
    md_path = "project_artifacts/step_2_summary.md"
    with open(md_path, "w") as f:
        f.write("# Daily Summary – Day 2\n\n")
        f.write(summary)
    save_state({"pipeline": "repo-pdf-pipeline", "step": 3, "status": "summary-done", "summary_path": md_path})
    tools.telegram_send(text="✅ Day 2 completed – summary generated.")

def step_3_generate_pdf():
    md_path = "project_artifacts/step_2_summary.md"
    pdf_path = "project_artifacts/step_3_report.pdf"
    subprocess.run(["pandoc", md_path, "-o", pdf_path], check=True)
    save_state({"pipeline": "repo-pdf-pipeline", "step": 4, "status": "pdf-done", "pdf_path": pdf_path})
    tools.telegram_send_file(file_path=pdf_path, caption="✅ Day 3 completed – PDF report generated.")

def step_4_cleanup_and_finish():
    zip_path = "project_artifacts_repo.zip"
    subprocess.run(["zip", "-r", zip_path, "project_artifacts"], check=True)
    tools.telegram_send_file(file_path=zip_path, caption="🗂️ All artifacts zipped – pipeline finished.")
    # Disable the cron job – JOB_ID will be injected by the orchestrator
    tools.cron_update(job_id=JOB_ID, patch=json.dumps({"enabled": false}))
    save_state({"pipeline": "repo-pdf-pipeline", "step": 5, "status": "finished"})

# Dispatcher
state = load_state()
step = state.get("step", 1)
if step == 1:
    step_1_collect()
elif step == 2:
    step_2_summarise()
elif step == 3:
    step_3_generate_pdf()
elif step == 4:
    step_4_cleanup_and_finish()
else:
    tools.telegram_send(text="🚀 Pipeline already finished.")
