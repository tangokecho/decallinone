# Workhorse Automation Builder – Specification

## Objective
Create a local, Python-based automation suite that generates business plan asset packs using a local LLM. The system must work end-to-end for a small batch of business ideas (IDs 1–10) and be trivially scalable to the full catalogue (268+ ideas) and additional artifact types.

## Environment Assumptions
- OS: Ubuntu 22.04 LTS (Linux-compatible).
- Python: 3.10+ with `venv` support.
- GPU: NVIDIA RTX 4070 with CUDA available for the local LLM.
- Local LLM: exposed via Ollama HTTP API (`http://localhost:11434/api/generate`) or equivalent local endpoint.
- Dependencies: stdlib-only; no external Python packages required.
- Network: not required beyond localhost access to the LLM.

## Input & Configuration
- Primary input: `input/ideas.json` containing objects with `id`, `title`, and `source`.
- Configuration: `config/config.yaml` defines
  - `input_file`: path to ideas file.
  - `output_base_dir`: base directory for generated artifacts.
  - `logs_dir`: directory for run logs.
  - `model`: LLM model name for Ollama.
  - `start_id` / `end_id`: inclusive ID bounds (default 1–10).
  - `timeout_seconds`: request timeout per LLM call.
  - `max_retries`: retry attempts for LLM calls.
- CLI flags:
  - `--config`: override config path.
  - `--all`: ignore bounds and process all ideas in the file.
  - `--dry-run`: validate inputs and list target ideas without calling the LLM or writing outputs.

## Output Structure
Outputs live under `output_base_dir` with deterministic folders:
```
<output_base_dir>/
  idea_XXX/
    plan.md
    summary.txt
    tiktok_script.txt
    offer_ladder.md
    funnel_copy.md
    meta.json
```
Logs are written to `<logs_dir>/run_YYYYMMDD_HHMM.log`.

## Pipeline Flow
1. Load configuration and structured ideas file.
2. Derive target idea set via `start_id`/`end_id` or `--all`.
3. For each idea:
   - Create `idea_XXX` directory.
   - Invoke LLM with templated prompts for each artifact using a steps registry.
   - Write outputs; validate non-empty content before marking success.
   - Write `meta.json` capturing status, timestamps, files, and errors.
4. Continue on per-idea failures; aggregate summary to stdout and logs.
5. In `--dry-run`, print planned idea IDs and exit.

## LLM Integration
- Wrapper `generate_with_llm(prompt, model, cfg)` uses Ollama HTTP API.
- Implements retry with exponential backoff and request timeout.
- Captures and logs failures without stopping the batch.
- Prompts are modular templates stored in `prompts.py` for easy editing.

## Extensibility
- Steps registry pattern enables adding artifacts by defining a new generator function and appending to `STEPS`.
- Scaling from 10 to 268 ideas requires only updating `start_id`/`end_id` or passing `--all`.
- Additional pipelines (e.g., Notion CSV, HTML landing pages) can reuse config/LLM utilities and register new steps.

## Quality & Safety
- Logging configured for console + file output; directories auto-created.
- Sanity checks ensure written files are non-empty before success.
- Failures recorded in `meta.json` and run log; processing continues.
- Dry-run mode validates inputs without side effects.

## Known Risks & Mitigations
- **Malformed JSON**: guarded by load error handling with clear messages.
- **Missing directories**: creation is automatic before use.
- **LLM errors/timeouts**: handled via retries and per-idea failure logging.
- **Empty responses**: outputs validated; empty content triggers failure status.

## Future Enhancements
- Parallel per-idea processing to improve throughput.
- Rich monitoring dashboard or web UI for run status.
- Pluggable model adapters for non-Ollama local backends.
- Template versioning for different asset packs.
