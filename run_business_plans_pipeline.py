"""Business Plan Pack Generator pipeline.

This script processes business ideas from a structured JSON file and generates
multiple artifacts per idea using a local LLM (e.g., via Ollama HTTP API).
It supports dry-run mode, configurable ID ranges, and resilient logging.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import csv
import logging
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import prompts


@dataclass
class Step:
    """Represents a generation step for a single output artifact."""

    name: str
    filename: str
    template: str
    description: str


def load_config(path: Path) -> Dict[str, Any]:
    """Load a minimal YAML-like configuration from disk using stdlib only."""

    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")

    config: Dict[str, Any] = {}
    with path.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'\"")

            if value.lower() in {"true", "false"}:
                parsed_value: Any = value.lower() == "true"
            else:
                try:
                    parsed_value = int(value)
                except ValueError:
                    parsed_value = value
            config[key] = parsed_value
    return config


def validate_config(cfg: Dict[str, Any]) -> None:
    """Ensure required configuration values exist."""

    required_keys = ["input_file", "output_base_dir", "model"]
    missing = [key for key in required_keys if key not in cfg]
    if missing:
        raise ValueError(f"Missing required config keys: {', '.join(missing)}")


def setup_logging(logs_dir: Path) -> Path:
    """Configure logging to file and stdout."""

    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = dt.datetime.now().strftime("%Y%m%d_%H%M")
    log_path = logs_dir / f"run_{timestamp}.log"

    log_format = "%(asctime)s | %(levelname)s | %(message)s"
    handlers = [
        logging.FileHandler(log_path, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
    logging.basicConfig(level=logging.INFO, format=log_format, handlers=handlers)
    return log_path


def load_ideas(path: Path) -> List[Dict[str, Any]]:
    """Load the ideas JSON file into memory."""
    if not path.exists():
        raise FileNotFoundError(f"Ideas file not found at {path}")

    # Support either JSON or CSV input files. CSV must contain rows of `id,title`.
    if path.suffix.lower() == ".csv":
        ideas: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            for row in reader:
                if not row:
                    continue
                # Skip header or malformed rows
                first = row[0].strip().lower()
                if first == "id" or first == "":
                    continue
                try:
                    idea_id = int(row[0].strip())
                except Exception:
                    # skip malformed id rows
                    continue
                title = row[1].strip() if len(row) > 1 else ""
                ideas.append({"id": idea_id, "title": title})
        if not isinstance(ideas, list):
            raise ValueError("CSV ideas file must produce a list of idea objects")
        return ideas

    # Default: assume JSON
    with path.open("r", encoding="utf-8") as handle:
        try:
            ideas = json.load(handle)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Ideas file is not valid JSON: {exc}") from exc
    if not isinstance(ideas, list):
        raise ValueError("Ideas file must contain a list of idea objects")
    return ideas


def filter_ideas(
    ideas: List[Dict[str, Any]], start_id: Optional[int], end_id: Optional[int], process_all: bool
) -> List[Dict[str, Any]]:
    """Filter ideas based on ID range unless processing all."""

    if process_all or start_id is None or end_id is None:
        return ideas
    return [idea for idea in ideas if start_id <= idea.get("id", -1) <= end_id]


def generate_with_llm(prompt: str, model: str, timeout_seconds: int, max_retries: int, logger: logging.Logger) -> Optional[str]:
    """Call the local LLM via Ollama HTTP API with retries using stdlib HTTP."""

    url = "http://localhost:11434/api/generate"
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")
    headers = {"Content-Type": "application/json"}

    for attempt in range(1, max_retries + 1):
        try:
            request = urllib.request.Request(url, data=payload, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                raw_body = response.read().decode("utf-8")
            data = json.loads(raw_body)
            text = data.get("response") if isinstance(data, dict) else None
            if text:
                return text.strip()
            logger.warning("Empty response received on attempt %s", attempt)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.warning("LLM request failed on attempt %s: %s", attempt, exc)
        sleep_seconds = min(2 ** attempt, 10)
        time.sleep(sleep_seconds)
    return None


def write_output_file(path: Path, content: str) -> bool:
    """Write content to disk and return True if non-empty."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)
    return bool(content.strip())


def build_steps() -> List[Step]:
    """Declare the generation steps for an idea."""

    return [
        Step(
            name="plan",
            filename="plan.md",
            template=prompts.PLAN_TEMPLATE,
            description="Full 2026 business plan",
        ),
        Step(
            name="summary",
            filename="summary.txt",
            template=prompts.SUMMARY_TEMPLATE,
            description="One-page summary",
        ),
        Step(
            name="tiktok_script",
            filename="tiktok_script.txt",
            template=prompts.TIKTOK_TEMPLATE,
            description="Short-form video script",
        ),
        Step(
            name="offer_ladder",
            filename="offer_ladder.md",
            template=prompts.OFFER_LADDER_TEMPLATE,
            description="Offer ladder",
        ),
        Step(
            name="funnel_copy",
            filename="funnel_copy.md",
            template=prompts.FUNNEL_COPY_TEMPLATE,
            description="Landing page copy",
        ),
    ]


def generate_artifacts_for_idea(
    idea: Dict[str, Any],
    steps: List[Step],
    output_dir: Path,
    cfg: Dict[str, Any],
    logger: logging.Logger,
    dry_run: bool,
) -> Dict[str, Any]:
    """Generate all configured artifacts for a single idea."""

    idea_dir = output_dir / f"idea_{idea['id']:03d}"
    meta = {
        "idea_id": idea.get("id"),
        "title": idea.get("title"),
        "source": idea.get("source"),
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "status": "pending",
        "errors": [],
        "generated_files": [],
    }

    if dry_run:
        logger.info("[DRY RUN] Would process idea %s (%s)", idea.get("id"), idea.get("title"))
        meta["status"] = "dry_run"
        return meta

    idea_dir.mkdir(parents=True, exist_ok=True)

    for step in steps:
        prompt_text = step.template.format(**idea)
        logger.info("Generating %s for idea %s", step.name, idea.get("id"))
        content = generate_with_llm(
            prompt_text,
            model=cfg["model"],
            timeout_seconds=cfg.get("timeout_seconds", 120),
            max_retries=cfg.get("max_retries", 3),
            logger=logger,
        )
        if not content:
            error_msg = f"No content returned for {step.name}"
            logger.error(error_msg)
            meta["errors"].append(error_msg)
            continue
        target_path = idea_dir / step.filename
        is_non_empty = write_output_file(target_path, content)
        if is_non_empty:
            meta["generated_files"].append(step.filename)
        else:
            error_msg = f"Generated empty content for {step.name}"
            logger.error(error_msg)
            meta["errors"].append(error_msg)

    meta["status"] = "success" if not meta["errors"] else "failed"
    meta["completed_at"] = dt.datetime.utcnow().isoformat() + "Z"

    meta_path = idea_dir / "meta.json"
    write_output_file(meta_path, json.dumps(meta, indent=2))
    return meta


def summarize_results(results: List[Dict[str, Any]], logger: logging.Logger) -> None:
    """Log and print a summary of pipeline execution."""

    total = len(results)
    successes = sum(1 for r in results if r.get("status") == "success")
    failures = [r for r in results if r.get("status") == "failed"]

    logger.info("Pipeline complete: %s processed, %s successes, %s failures", total, successes, len(failures))
    if failures:
        failure_ids = [str(r.get("idea_id")) for r in failures]
        logger.info("Failed idea IDs: %s", ", ".join(failure_ids))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(description="Run the Business Plan Pack Generator")
    parser.add_argument("--config", default="config/config.yaml", help="Path to config file")
    parser.add_argument("--all", action="store_true", dest="process_all", help="Process all ideas in the file")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Validate inputs without LLM calls")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg_path = Path(args.config)
    cfg = load_config(cfg_path)
    validate_config(cfg)

    logs_dir = Path(cfg.get("logs_dir", "logs"))
    log_path = setup_logging(logs_dir)
    logger = logging.getLogger("business_plans_pipeline")
    logger.info("Logging to %s", log_path)

    ideas_path = Path(cfg["input_file"])
    ideas = load_ideas(ideas_path)

    ideas_to_process = filter_ideas(
        ideas,
        start_id=cfg.get("start_id"),
        end_id=cfg.get("end_id"),
        process_all=args.process_all,
    )

    if not ideas_to_process:
        logger.warning("No ideas match the provided filters. Nothing to do.")
        return

    output_dir = Path(cfg["output_base_dir"])
    steps = build_steps()

    logger.info(
        "Beginning processing for %s ideas (dry_run=%s, process_all=%s)",
        len(ideas_to_process),
        args.dry_run,
        args.process_all,
    )

    results = []
    for idea in ideas_to_process:
        if "id" not in idea or "title" not in idea:
            logger.error("Idea missing required fields: %s", idea)
            continue
        result = generate_artifacts_for_idea(idea, steps, output_dir, cfg, logger, args.dry_run)
        results.append(result)

    summarize_results(results, logger)


if __name__ == "__main__":
    main()
