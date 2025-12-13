<!-- GitHub Copilot instructions for coding agents -->

# Copilot Guidance — Business Plan Pack pipeline

Purpose: help an AI coding agent get productive fast. Read the three files below before changing behavior.

- Read first:
  - `run_business_plans_pipeline.py` — runner and control flow (config, input loading, LLM call, artifact loop).
  - `prompts.py` — all prompt templates; templates use `str.format(**idea)` so referenced keys must exist.
  - `config/config.yaml` — simple colon-separated config (no YAML lists/nesting). Example keys: `input_file`, `output_base_dir`, `model`, `timeout_seconds`, `max_retries`.

- Inputs & outputs:
  - Supported inputs: `input/ideas.json` (JSON list) or `input/ideas.csv` (`id,title`). `load_ideas()` auto-detects `.csv`.
  - Outputs: deterministic folders `workhorse_projects/business_plans_pipeline/output/idea_{id:03d}/` with generated files and `meta.json` per idea.

- Runtime notes & examples:
  - Dry run (no LLM): `python run_business_plans_pipeline.py --config config/config.yaml --dry-run`
  - Full run: `python run_business_plans_pipeline.py --config config/config.yaml`
  - CSV -> JSON helper: `python scripts/csv_to_json.py` (optional)

- Integration points:
  - LLM endpoint used in code: `http://localhost:11434/api/generate` (Ollama). When testing, stub or mock `generate_with_llm()`.

- Editing patterns to follow:
  - Add artifact: add a template to `prompts.py` and a `Step(name, filename, template, description)` in `build_steps()`.
  - Preserve `load_config()` semantics if changing `config/config.yaml` format.
  - Preserve `idea_{id:03d}` naming and `meta.json` structure unless updating downstream consumers.

- Testing guidance (discoverable from repo):
  - Unit tests should stub `generate_with_llm()` and assert files are written to a temp `output_base_dir`.

If you want I can: add unit tests for CSV parsing, implement a mock LLM harness, or tighten config validation. Reply with which one.
<!-- GitHub Copilot instructions for coding agents -->
# Repo-specific guidance for AI coding agents

Purpose: Give a concise, actionable orientation so an AI coding agent can be immediately productive in this repository.

- **Big picture**: This repo contains a linear, local-first pipeline that reads a list of business ideas (JSON), calls a local LLM to generate multiple artifacts per idea, and writes a deterministic set of files plus a `meta.json` per idea. The main runner is `run_business_plans_pipeline.py`.

- **Key files**:
  - `run_business_plans_pipeline.py` — primary pipeline; contains `load_config`, `load_ideas`, `generate_with_llm`, `build_steps()` and `generate_artifacts_for_idea()`.
  - `prompts.py` — prompt templates used by each `Step` (look for `PLAN_TEMPLATE`, `SUMMARY_TEMPLATE`, `TIKTOK_TEMPLATE`, `OFFER_LADDER_TEMPLATE`, `FUNNEL_COPY_TEMPLATE`).
  - `config/config.yaml` — canonical runtime config (note: parser is a tiny stdlib-only parser, not a full YAML loader).
  - `input/ideas.json` and `input/ideas.csv` — sample inputs; pipeline expects `input/ideas.json` to be a top-level JSON array of idea objects.
    - `input/ideas.json` and `input/ideas.csv` — sample inputs; the pipeline accepts either JSON (list of objects) or CSV (`id,title`) directly.
  - `workhorse_projects/business_plans_pipeline/output/` — default `output_base_dir` where the pipeline writes per-idea folders `idea_XXX/` and `meta.json` files.

- **How the pipeline works (data flow)**:
  1. Read `config/config.yaml` using a simple colon-split parser (keys/values only).
  2. Load `input_file` (must be a JSON list). Each idea is a dict; required keys are `id` and `title`.
  3. For each idea, build prompt text with `step.template.format(**idea)` using templates from `prompts.py`.
  4. Call the local LLM via `generate_with_llm()` which targets `http://localhost:11434/api/generate` (Ollama-compatible) using `urllib`.
  5. Write artifacts into `output_base_dir/idea_{id:03d}/` and record `meta.json` with status/errors.

- **Run & debug**:
  - Dry run (no LLM calls, validates inputs):
    `python run_business_plans_pipeline.py --config config/config.yaml --dry-run`
  - Full run (be careful — writes files and calls LLM):
    `python run_business_plans_pipeline.py --config config/config.yaml`
  - Per-run logs are written to the configured `logs_dir` (default `logs/`) — check the timestamped file for LLM errors and backoff retries.
  - Per-idea diagnostics are in each `idea_XXX/meta.json`.

- **Config parser specifics (important for patching or tests)**:
  - `config/config.yaml` is parsed with a minimal parser (colon-separated). Values that look like integers are converted to `int`; `true`/`false` (case-insensitive) become booleans; everything else is raw string.
  - Do not rely on YAML features (lists, nested maps). If you change config format, update `load_config()` accordingly.

- **Patterns & conventions to follow**:
  - Add new artifacts by creating a new prompt in `prompts.py` and adding a `Step(...)` entry in `build_steps()` in `run_business_plans_pipeline.py`.
  - Templates use `str.format(**idea)`; ensure `idea` keys referenced by templates exist on sample ideas.
  - The pipeline expects `ideas` to be a `list[dict]`; a non-list JSON input raises a `ValueError` in `load_ideas()`.
  - ID formatting: output folders are `idea_{id:03d}` (zero-padded to three digits).

- **Integration points & external dependencies**:
  - Local LLM: `http://localhost:11434/api/generate` (Ollama HTTP API) — tests and CI must mock or stub this endpoint if running non-dry tests.
  - `requirements.txt` may include helper packages; the runner itself is stdlib-first.

- **Quick examples to reference in edits**:
  - Required idea fields check (see `main()`): the runner skips ideas missing `id` or `title`.
  - Template usage (see `generate_artifacts_for_idea()`): `prompt_text = step.template.format(**idea)`.
  - LLM retry/backoff logic (see `generate_with_llm()`): exponential backoff with caps at 10s.

- **When editing code, pay attention to**:
  - Preserving the simple config parser semantics or updating it in one place (`load_config`).
  - Not changing output folder layout unless `config/config.yaml` is updated and tests adjusted.
  - Handling JSON errors: `load_ideas()` raises `ValueError` for invalid JSON — keep error messages clear.

If anything here is unclear or you'd like more examples (sample `prompts.py` usages, a mocked LLM test harness, or an example `ideas.json`), tell me which part to expand and I will iterate.
