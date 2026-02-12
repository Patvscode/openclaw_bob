## LLMInferenceProfiler Skill
- **Purpose**: Automate benchmarking of LLM inference under various configurations (quantization, attention kernels, KV‑cache). Generates a markdown report with latency, quality, and memory metrics.
- **Inputs**: `model_name` (e.g., "Llama-3-8B"), `quantization` (e.g., "8bit"), `attention` (e.g., "FlashAttention"), `prompt_length` (int).
- **Outputs**: Path to a markdown report (e.g., `memory/benchmark/<date>.md`).
- **Method**:
  1. Load the specified model via HuggingFace Transformers (or compatible local build).
  2. Apply quantization using `bitsandbytes` or `ggml`.
  3. Enable the selected attention kernel.
  4. Run a fixed 512‑token prompt, measure per‑token latency, total latency, memory usage, and compute BLEU against a full‑precision baseline.
  5. Write a markdown summary (as shown in `memory/benchmark/2026-02-11.md`).
- **Implementation notes**:
  - Store script at `skills/LLMInferenceProfiler/run.py`.
  - Require Python 3.9+, `torch`, `transformers`, `bitsandbytes`, `accelerate`.
  - Include a small helper `utils.py` for BLEU computation.
- **Future improvements**: batch multiple models, add GPU/CPU selection, log to a central CSV for trend analysis.

*Skill description added for future development.*