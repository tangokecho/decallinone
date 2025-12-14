# Workhorse Business Plan Pack Generator

This repository provides a local-first automation pipeline that uses a local LLM (via Ollama or similar) to generate business plan packs for a list of business ideas. It starts with a small batch (ideas 1–10) and is designed to scale to the full list of 268+ ideas and additional artifact types.

## Features
- Reads ideas from a structured JSON file and filters by ID range or `--all` flag.
- Generates multiple artifacts per idea (plan, summary, TikTok script, offer ladder, funnel copy) using reusable prompt templates.
- Creates deterministic output folders, writes metadata, and logs each run.
- Includes retry-aware LLM client with timeout handling and sanity checks for empty outputs.
- Dry-run mode validates inputs and prints planned work without invoking the LLM or writing artifacts.

## Quickstart
1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run a test batch (ideas 1–3 sample)**
   ```bash
   python run_business_plans_pipeline.py --dry-run
   ```
   Remove `--dry-run` to generate real outputs once your local LLM endpoint is available.

## Configuration
Configuration lives in `config/config.yaml`:
- `paths.input_file`: JSON file containing the ideas list.
- `paths.output_dir`: Base directory for generated artifacts.
- `paths.logs_dir`: Directory for log files.
- `processing.start_id` / `processing.end_id`: Inclusive range of idea IDs to process.
- `processing.all`: Set to `true` or use `--all` flag to process every idea in the file.
- `model`, `timeout_seconds`, `max_retries`, `retry_backoff`: LLM and request tuning parameters.

## Scaling to All Ideas
- Update `processing.start_id` / `processing.end_id` in `config/config.yaml`, or run with `--all` to process the full list (e.g., all 268 ideas) without code changes.
- Add new artifact types by defining a new prompt builder in `prompt_templates.py`, creating a `GenerationStep`, and registering it in `run_business_plans_pipeline.py` within the `steps` list.

## Known Limitations & Future Improvements
- **Sequential execution:** Ideas are processed one at a time; parallelism can be added later to improve throughput.
- **LLM endpoint dependency:** Assumes a reachable local Ollama-compatible endpoint; model availability and hardware setup are manual.
- **No dashboard yet:** Monitoring is via CLI output and log files; a lightweight web UI or status dashboard would help at scale.
- **Enhanced validation:** Current checks ensure non-empty outputs; schema validation for responses could further reduce malformed files.

## Self-Audit: Potential Failure Modes
- **Malformed `ideas.json`:** Loading will fail if the file is not valid JSON or not a list; errors surface early with logs.
- **Missing directories or paths:** The pipeline auto-creates expected directories, but incorrect paths in config can still prevent file writes.
- **LLM failures/timeouts:** Retries with backoff are built-in; repeated failures record errors in `meta.json` and continue with the next idea.

## Repository Layout
- `SPEC.md`: Formal specification of the automation suite.
- `run_business_plans_pipeline.py`: Pipeline entrypoint and orchestrator.
- `prompt_templates.py`: Modular prompt builders for each artifact.
- `config/config.yaml`: Default configuration.
- `input/ideas.json`: Sample ideas for quick testing.
- `output/`: Generated artifacts will be written here.
- `logs/`: Run logs.

## Example Commands
- Validate setup without LLM calls:
  ```bash
  python run_business_plans_pipeline.py --dry-run
  ```
- Process a specific ID range (e.g., ideas 5–15):
  ```bash
  python run_business_plans_pipeline.py --config config/config.yaml
  ```
  and set `start_id: 5`, `end_id: 15` in the config.
- Process all ideas in the file:
  ```bash
  python run_business_plans_pipeline.py --all
  ```

