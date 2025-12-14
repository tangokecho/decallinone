# Workhorse Automation Builder Specification

## Overview
This specification describes a Python-based, fully local automation suite for the Workhorse workstation. The suite generates content packs for business ideas by orchestrating local LLM calls, managing configuration, and producing structured artifacts. The initial pipeline focuses on generating business plan packs for a small subset of ideas (IDs 1–10) and is designed to scale to the full catalog of 268 ideas and additional artifact types.

## Environment Assumptions
- **OS:** Ubuntu 22.04 LTS (or similar Linux)
- **Python:** 3.10+
- **GPU:** NVIDIA RTX 4070 with CUDA available
- **Local LLM:** Accessible via Ollama HTTP API at `http://localhost:11434/api/generate` or compatible endpoint
- **Tools:** `venv`, `pip`, `requests`, `PyYAML`, standard library utilities. Optional: `langchain` or similar can be added later but is not required for v1.

## Folder Structure
```
/workhorse_projects/
  business_plans_pipeline/
    config/
      config.yaml
    input/
      ideas.json
    output/
      idea_001/
        plan.md
        summary.txt
        tiktok_script.txt
        offer_ladder.md
        funnel_copy.md
        meta.json
    logs/
      run_YYYYMMDD_HHMM.log
```
The script auto-creates missing directories.

## Core Pipeline: Business Plan Pack Generator v1
- **Input:** Structured JSON list of ideas with fields `id`, `title`, and optional `source`.
- **Scope:** Default processing for IDs 1–10; configurable via `start_id`/`end_id` or `--all` flag.
- **Outputs per idea:**
  - `plan.md`: 2026 business plan using template sections (Executive Summary, Market, Offer, Revenue Model, Marketing, Ops, Risk, 90-Day Roadmap).
  - `summary.txt`: One-page plain-text summary.
  - `tiktok_script.txt`: Hook/body/CTA script for TikTok/Reels.
  - `offer_ladder.md`: Free, low-ticket, mid-ticket, high-ticket offers.
  - `funnel_copy.md`: Landing page hero, bullets, CTA copy.
  - `meta.json`: Metadata with status, timestamps, and errors if any.

## LLM Integration
- LLM calls go through a utility function `generate_with_llm(prompt: str) -> str` using the configured model/endpoint.
- Includes retry logic (default 3 attempts) with incremental backoff and timeout handling.
- Prompts are template-driven per artifact and stored centrally for easy editing.

## Script Behavior & Flow
1. Load configuration from `config/config.yaml` or CLI overrides.
2. Read `input/ideas.json` and filter ideas by ID range.
3. For each idea:
   - Create `output/idea_XXX/` directory.
   - Run registered generation steps to create artifacts.
   - Validate non-empty outputs before marking success.
   - Write `meta.json` with status and any errors.
4. Log detailed progress to `logs/run_YYYYMMDD_HHMM.log` and print a final summary (# processed, successes, failures).
5. Graceful failure: individual idea errors are logged and do not stop the batch.
6. `--dry-run` mode validates inputs and prints planned work without LLM calls or file creation.

## Scalability & Extensibility
- Scaling from 10 to 268 ideas is a config change: adjust `start_id`/`end_id` or use `--all`.
- New artifact types are added via generator functions registered in a `STEPS` registry.
- Configuration is declarative; paths, model, timeouts, and idea ranges are adjustable.

## Quality & Audit
- Code is modular and commented for non-engineers.
- Basic sanity checks ensure outputs are non-empty before success.
- Logging captures malformed responses and retries.
- README includes setup, usage, and scaling instructions plus limitations/future improvements.

## Known Limitations & Future Enhancements (Initial)
- Parallel processing is not implemented; ideas run sequentially.
- No web UI/dashboard yet; relies on CLI and log files.
- Assumes Ollama endpoint availability; model management is manual.

