"""Business Plan Pack Generator pipeline entrypoint."""
import argparse
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

import requests
import yaml

import prompt_templates as prompts


@dataclass
class PipelineConfig:
    input_file: Path
    output_dir: Path
    logs_dir: Path
    model: str
    start_id: int
    end_id: int
    timeout_seconds: int = 120
    max_retries: int = 3
    retry_backoff: float = 2.0
    all_ideas: bool = False


@dataclass
class IdeaResult:
    idea_id: int
    title: str
    status: str
    errors: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class GenerationStep:
    name: str
    filename: str
    prompt_builder: Callable[[str], str]


API_ENDPOINT = "http://localhost:11434/api/generate"


def load_config(config_path: Path) -> PipelineConfig:
    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    return PipelineConfig(
        input_file=Path(raw["paths"]["input_file"]),
        output_dir=Path(raw["paths"]["output_dir"]),
        logs_dir=Path(raw["paths"]["logs_dir"]),
        model=raw["model"],
        start_id=raw["processing"].get("start_id", 1),
        end_id=raw["processing"].get("end_id", 10),
        timeout_seconds=raw.get("timeout_seconds", 120),
        max_retries=raw.get("max_retries", 3),
        retry_backoff=raw.get("retry_backoff", 2.0),
        all_ideas=raw["processing"].get("all", False),
    )


class LLMClient:
    def __init__(self, model: str, timeout_seconds: int, max_retries: int, retry_backoff: float):
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff

    def generate(self, prompt: str) -> str:
        last_error: Optional[str] = None
        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(
                    API_ENDPOINT,
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=self.timeout_seconds,
                )
                response.raise_for_status()
                data = response.json()
                content = data.get("response", "").strip()
                if not content:
                    last_error = "Empty response from LLM"
                    raise ValueError(last_error)
                return content
            except Exception as exc:  # noqa: BLE001 broad for resilience
                last_error = str(exc)
                logging.warning("Attempt %s failed: %s", attempt, last_error)
                if attempt < self.max_retries:
                    sleep_time = self.retry_backoff * attempt
                    time.sleep(sleep_time)
                else:
                    break
        raise RuntimeError(f"LLM generation failed after {self.max_retries} attempts: {last_error}")


def ensure_directories(config: PipelineConfig) -> None:
    for path in {config.output_dir, config.logs_dir, config.input_file.parent}:
        path.mkdir(parents=True, exist_ok=True)


def load_ideas(ideas_file: Path) -> List[Dict]:
    with ideas_file.open("r", encoding="utf-8") as f:
        ideas = json.load(f)
    if not isinstance(ideas, list):
        raise ValueError("ideas.json must contain a list of ideas")
    return ideas


def filter_ideas(ideas: List[Dict], config: PipelineConfig) -> List[Dict]:
    if config.all_ideas:
        return ideas
    return [idea for idea in ideas if config.start_id <= idea.get("id", -1) <= config.end_id]


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def write_meta(path: Path, result: IdeaResult) -> None:
    payload = {
        "idea_id": result.idea_id,
        "title": result.title,
        "status": result.status,
        "errors": result.errors,
        "started_at": result.started_at,
        "completed_at": result.completed_at,
    }
    write_file(path, json.dumps(payload, indent=2))


def process_idea(
    idea: Dict,
    steps: List[GenerationStep],
    llm_client: LLMClient,
    config: PipelineConfig,
    dry_run: bool,
) -> IdeaResult:
    idea_id = idea.get("id")
    title = idea.get("title", "Untitled Idea")
    result = IdeaResult(
        idea_id=idea_id,
        title=title,
        status="pending",
        started_at=datetime.utcnow().isoformat(),
    )

    idea_dir = config.output_dir / f"idea_{idea_id:03d}"
    meta_path = idea_dir / "meta.json"

    if dry_run:
        logging.info("[DRY RUN] Would process idea %s: %s", idea_id, title)
        result.status = "dry_run"
        result.completed_at = datetime.utcnow().isoformat()
        return result

    for step in steps:
        try:
            prompt = step.prompt_builder(title)
            content = llm_client.generate(prompt)
            if not content.strip():
                raise ValueError(f"{step.name} returned empty content")
            write_file(idea_dir / step.filename, content)
            logging.info("Generated %s for idea %s", step.name, idea_id)
        except Exception as exc:  # noqa: BLE001 broad for resilience
            error_msg = f"{step.name} failed: {exc}"
            logging.error(error_msg)
            result.errors.append(error_msg)

    result.status = "success" if not result.errors else "partial_failure"
    result.completed_at = datetime.utcnow().isoformat()
    write_meta(meta_path, result)
    return result


def summarize_results(results: List[IdeaResult]) -> str:
    successes = [r for r in results if r.status == "success"]
    failures = [r for r in results if r.status != "success"]
    summary = (
        f"Processed {len(results)} ideas | successes: {len(successes)} | "
        f"failures: {len(failures)}"
    )
    if failures:
        failure_ids = ", ".join(str(r.idea_id) for r in failures)
        summary += f" | failed IDs: {failure_ids}"
    return summary


def configure_logging(logs_dir: Path) -> None:
    logs_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    log_file = logs_dir / f"run_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Business Plan Pack Generator")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.yaml"),
        help="Path to YAML configuration file",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all ideas in the input file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate inputs without calling the LLM or writing outputs",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if args.all:
        config.all_ideas = True

    ensure_directories(config)
    configure_logging(config.logs_dir)

    logging.info("Loading ideas from %s", config.input_file)
    ideas = load_ideas(config.input_file)
    selected_ideas = filter_ideas(ideas, config)

    if not selected_ideas:
        logging.warning("No ideas selected for processing. Check the ID range or input file.")
        return

    steps = [
        GenerationStep("plan_md", "plan.md", prompts.business_plan_prompt),
        GenerationStep("summary", "summary.txt", prompts.summary_prompt),
        GenerationStep("tiktok_script", "tiktok_script.txt", prompts.tiktok_prompt),
        GenerationStep("offer_ladder", "offer_ladder.md", prompts.offer_ladder_prompt),
        GenerationStep("funnel_copy", "funnel_copy.md", prompts.funnel_copy_prompt),
    ]

    llm_client = LLMClient(
        model=config.model,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
        retry_backoff=config.retry_backoff,
    )

    results: List[IdeaResult] = []
    for idea in selected_ideas:
        results.append(process_idea(idea, steps, llm_client, config, args.dry_run))

    summary = summarize_results(results)
    logging.info(summary)
    print(summary)


if __name__ == "__main__":
    main()
