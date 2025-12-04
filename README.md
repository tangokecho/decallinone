# Workhorse Business Plan Pack Generator

This repository contains a local-first automation pipeline that turns a structured list of business ideas into a complete set of assets using a local LLM (e.g., Ollama). The initial pipeline targets the Business Plan Pack for ideas 1–10 and is designed to scale to all 268 ideas with minimal changes.

## Features
- Reads structured ideas from `input/ideas.json`.
- Uses configurable ID ranges or an `--all` flag to control batch size.
- Generates multiple artifacts per idea (plan, summary, TikTok script, offer ladder, funnel copy) with modular prompt templates.
- Writes outputs to a deterministic folder structure and logs to timestamped files.
- Includes retry logic for LLM calls, sanity checks for empty outputs, and per-idea metadata tracking.
- Dry-run mode validates inputs without calling the LLM or writing outputs.

## Quickstart
1. **Set up environment** (stdlib-only dependencies)
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run a test batch (ideas 1–3 provided)**
   ```bash
   python run_business_plans_pipeline.py --config config/config.yaml --dry-run
   # remove --dry-run to generate outputs
   ```

3. **Scale to full list (up to 268 ideas)**
   - Update `start_id` and `end_id` in `config/config.yaml`, **or**
   - Run with `--all` to process every entry in `input/ideas.json`.

## Configuration
`config/config.yaml` controls runtime behavior:
- `input_file`: path to ideas JSON file.
- `output_base_dir`: base folder for generated assets.
- `logs_dir`: folder for log files.
- `model`: local LLM model name (for Ollama API).
- `start_id`, `end_id`: inclusive bounds for idea IDs.
- `timeout_seconds`: per-request timeout for the LLM.
- `max_retries`: retry attempts for failed LLM calls.

## File Structure
```
workhorse_projects/
  business_plans_pipeline/
    input/              # ideas file lives outside repo; default path is config value
    output/
      idea_001/
        plan.md
        summary.txt
        tiktok_script.txt
        offer_ladder.md
        funnel_copy.md
        meta.json
logs/                   # timestamped run logs
config/config.yaml      # example config
input/ideas.json        # sample ideas (1–3)
```

## Extending the pipeline
- Add a new artifact by creating a new prompt template in `prompts.py` and a `Step` entry in `build_steps()`.
- Create additional pipelines (e.g., Notion CSVs, HTML landing pages) by reusing the LLM helper (`generate_with_llm`) and step pattern.
- To change models or endpoints, adjust the model name in config or swap the URL inside `generate_with_llm`.

## Known Limitations & Future Improvements
- **Failure mode: malformed JSON** – guarded during load with clear errors, but the run halts for invalid input.
- **Failure mode: missing directories** – auto-created, but ensure the configured base path is writable.
- **Failure mode: LLM timeouts/empty responses** – retried with backoff; persistent issues are logged and marked as failures per idea.
- **Enhancement:** Parallelize per-idea processing for throughput.
- **Enhancement:** Add a simple dashboard or web UI to monitor run status.

## LLM Endpoint Assumption
The script targets an Ollama-compatible HTTP endpoint at `http://localhost:11434/api/generate`. Adjust the URL inside `generate_with_llm` if using a different local endpoint.
