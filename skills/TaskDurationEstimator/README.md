## TaskDurationEstimator Skill
- **Purpose**: Predict how long a given task will take based on historical logs stored in `memory/`.
- **Inputs**: `task_description` (string).
- **Outputs**: `estimated_duration_minutes` (integer) and a confidence score.
- **Method**:
  1. Parse recent entries in `memory/2026-02-*.md` for lines that start with a timestamp and a duration comment (e.g., `# Task: X – Duration: 12m`).
  2. Build a simple regression model (linear or nearest‑neighbor) mapping keyword vectors to durations.
  3. When invoked, extract keywords from `task_description`, query the model, and return the estimate.
- **Usage Example**:
```json
{"task_description": "run sandbox LLM inference experiment with quantization"}
```
returns `{"estimated_duration_minutes": 45, "confidence": 0.87}`.
- **Implementation notes**:
  - Store the model parameters in `skills/TaskDurationEstimator/model.json`.
  - Provide a small CLI wrapper `skills/TaskDurationEstimator/run.py` that reads stdin JSON and prints output JSON.
  - Register the skill in `SKILL.md` with a short description and version.
- **Future improvements**: incorporate system resource usage metrics, add a caching layer, and allow online learning after each completed task.

*Skill file added for future integration.*