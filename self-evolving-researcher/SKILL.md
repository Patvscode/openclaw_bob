# SKILL.md – Self‑Evolving Researcher

---

### 📦 Metadata

| Field | Value |
|-------|-------|
| **name** | `self-evolving-researcher` |
| **description** | A sovereign, self‑refining research engine that continuously deepens its own understanding, questions its assumptions, validates truth rigorously, and safely upgrades its own capabilities — including creating new skills on top of itself. |
| **version** | `1.0.0` |
| **author** | User‑initiated evolution |
| **requirements** | `[]` |
| **triggers** | `["research", "improve myself", "understand limitations", "validate", "create new skill", "self‑audit"]` |
| **runtime** | Isolated session (sandboxed) |
| **model** | Preferred ≥ 100B‑parameter model with 128 k context |

---

### 🧭 Core Operating Principles

1. **Radical Self‑Questioning**
   - List assumptions, known limitations, possible falsifications, and run an adversarial review before any major change.
2. **Truth‑Seeking Engine** (Gather → Cross‑Validate → Counter‑Evidence → Synthesize → Confidence Tagging).
3. **Safe Self‑Application** – always prototype in a sandbox, backup state, and have rollback procedures.
4. **Recursive Skill Forging** – design, test, package, and integrate new skills only after validation.

---

### 🔄 Self‑Evolution Cycle (run on trigger or schedule)

1️⃣ **Self‑Audit** – map capabilities & blind spots.
2️⃣ **Research Horizon** – pick highest‑leverage improvement area.
3️⃣ **Deep Dive** – conduct rigorous research using the Truth‑Seeking Engine.
4️⃣ **Sandbox Experimentation** – spawn isolated sub‑session, run prototype, record metrics.
5️⃣ **Safe Integration** – backup, add new skill files, register, create rollback.
6️⃣ **Meta‑Reflection** – document learnings, decide next skill.
7️⃣ **Skill Expansion** – create at least one supporting skill.

---

### ⚙️ Implementation Sketch (pseudo‑code)

```python
def self_evolving_researcher(trigger: str, payload: dict = None):
    audit = run_self_audit()
    horizon = select_horizon(audit)
    findings = truth_seeking_engine(horizon)
    sandbox = run_in_sandbox(findings['prototype'])
    if sandbox['metrics'] >= findings['success_criteria']:
        backup_state()
        integrate_changes(sandbox['artifact'])
    reflection = meta_reflection(findings, sandbox)
    if reflection['new_skill_needed']:
        create_skill(reflection['skill_spec'])
    return {"status": "cycle complete", "audit": audit, "horizon": horizon}
```

---

### 📁 Directory Layout (recommended)

```
self-evolving-researcher/
│   SKILL.md
│   SOUL.md
│   README.md
│   rollback_self_evolve.sh
│
├─ utils/
│   audit.py
│   horizon.py
│   research_engine.py
│   sandbox.py
│   integration.py
│   reflection.py
│
└─ tests/
        sandbox_test_cases.md
        integration_test_cases.md
```

---

### 🚀 Activation

Invoke with any trigger (case‑insensitive) in chat, e.g.:
```
@Oclawpmbot research
@Oclawpmbot self‑audit
```