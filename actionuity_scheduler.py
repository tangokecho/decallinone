import os
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv
from openai import OpenAI

BASE_DIR = Path(__file__).parent
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TIMEZONE = os.getenv("TIMEZONE", "America/New_York")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set in environment or .env file")

client = OpenAI(api_key=OPENAI_API_KEY)


def run_openai_task(task_name: str, prompt: str) -> str:
    """Run a scheduled OpenAI Responses call and persist the output."""
    print(f"[{datetime.now().isoformat()}] Running task: {task_name}")

    response = client.responses.create(
        model="gpt-4o",
        instructions=(
            "You are TyTll, the Actionuity AI Action Officer. "
            "You think clearly, execute sharply, and output concise, actionable results. "
            "Avoid fluff, focus on what Rex can actually do next."
        ),
        input=prompt,
    )

    try:
        output_text = response.output_text
    except AttributeError:
        output_text = str(response)

    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}__{task_name}.md"
    with log_file.open("a", encoding="utf-8") as file:
        file.write(f"\n\n# {datetime.now().isoformat()} — {task_name}\n\n")
        file.write(output_text)
        file.write("\n")

    print(f"[{datetime.now().isoformat()}] Completed task: {task_name}")
    print(f"  -> Logged to {log_file}")
    return output_text


PROMPTS = {
    "daily_revenue_scan": (
        "Run the Daily Revenue Conditions Scan. "
        "Identify today’s fastest paths to revenue based on Actionuity’s current offers, "
        "the December Entrepreneurial Month campaign, and the 39-Day Cashflow Sprint. "
        "Return a prioritized 'Today’s Money List' with 3–7 actions, labeled with: "
        "1) impact (high/med/low), 2) effort (high/med/low), 3) timebox estimate."
    ),
    "daily_content_engine": (
        "Generate today’s Content Engine Pack for Dealflow December and the 39-Day Sprint. "
        "Output 3–5 short-form content ideas (TikTok/Reels/Shorts), each with: "
        "hook, 3–6 sentence body, CTA, and recommended platform."
    ),
    "daily_notion_sync": (
        "You are a data formatter. Summarize today’s key outputs for ingestion into Notion. "
        "Return 3 sections: Tasks, Assets, Insights. Each section is a bullet list with "
        "short, import-friendly items."
    ),
    "tri_core_pulse": (
        "Run the Tri-Core Pulse Check:\n"
        "1) Strategy: what should be prioritized today and why?\n"
        "2) Codex: list 3–5 concrete build tasks (scripts, templates, automations).\n"
        "3) Agent: list 3–5 follow-up actions to close loops or gather feedback.\n"
        "Keep it tight and execution-focused."
    ),
    "sprint_profit_tracker": (
        "Update the 39-Day Sprint Financial Tracker. "
        "Assume you are summarizing today’s numbers and trend for Rex. "
        "Ask for any missing inputs explicitly (e.g., 'enter today’s revenue'). "
        "Return: Today, Cumulative, Gap-to-goal, and 1–3 adjustments."
    ),
    "sprint_opportunity_miner": (
        "Act as an opportunity miner for fast cash wins. "
        "List 5 concrete money-making plays Rex can run in the next 24 hours, "
        "using Actionuity’s existing skills, IP, and partially-built offers. "
        "For each: name, description, expected ticket, and channel."
    ),
    "sprint_hype_engine": (
        "Create one high-energy promo script to push today’s key sprint offer. "
        "Provide:\n- 1 TikTok script\n- 1 Reels caption\n- 1 short DM script\n"
        "Make them emotionally real, not corny."
    ),
    "sprint_eod_report": (
        "Generate a Sprint End-of-Day Report template for Rex to fill in. "
        "Sections: Wins, Losses, Revenue, Lessons, Tomorrow’s Top 3. "
        "Leave space/placeholders for numbers."
    ),
    "weekly_offer_optimization": (
        "Audit current offers (micro, mid, premium) for clarity, pricing, and positioning. "
        "Return a table-like markdown with columns: Offer, Problem, Promise, Price, "
        "Main Fix."
    ),
    "weekly_cashflow_forecast": (
        "Create a one-week cashflow forecast skeleton Rex can fill in. "
        "Include incoming, outgoing, risk notes, and must-pay items."
    ),
    "monthly_reset": (
        "Run a Monthly Strategic Reset for Actionuity. "
        "Return sections: What Worked, What Failed, Non-Negotiables for Next Month, "
        "Top 3 Money Levers, and OS Changes to implement."
    ),
}


def task_daily_revenue_scan():
    return run_openai_task("daily_revenue_scan", PROMPTS["daily_revenue_scan"])


def task_daily_content_engine():
    return run_openai_task("daily_content_engine", PROMPTS["daily_content_engine"])


def task_daily_notion_sync():
    return run_openai_task("daily_notion_sync", PROMPTS["daily_notion_sync"])


def task_tri_core_pulse():
    return run_openai_task("tri_core_pulse", PROMPTS["tri_core_pulse"])


def task_sprint_profit_tracker():
    return run_openai_task("sprint_profit_tracker", PROMPTS["sprint_profit_tracker"])


def task_sprint_opportunity_miner():
    return run_openai_task("sprint_opportunity_miner", PROMPTS["sprint_opportunity_miner"])


def task_sprint_hype_engine():
    return run_openai_task("sprint_hype_engine", PROMPTS["sprint_hype_engine"])


def task_sprint_eod_report():
    return run_openai_task("sprint_eod_report", PROMPTS["sprint_eod_report"])


def task_weekly_offer_optimization():
    return run_openai_task("weekly_offer_optimization", PROMPTS["weekly_offer_optimization"])


def task_weekly_cashflow_forecast():
    return run_openai_task("weekly_cashflow_forecast", PROMPTS["weekly_cashflow_forecast"])


def task_monthly_reset():
    return run_openai_task("monthly_reset", PROMPTS["monthly_reset"])


def run_day_one_bootstrap():
    """Run the one-shot Day 1 sequence before enabling the scheduler."""
    print("=== Running Day 1 Bootstrap ===")
    task_daily_revenue_scan()
    task_daily_content_engine()
    task_tri_core_pulse()
    task_sprint_opportunity_miner()
    task_sprint_profit_tracker()
    print("=== Day 1 Bootstrap complete ===")


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(timezone=TIMEZONE)

    scheduler.add_job(task_sprint_opportunity_miner, CronTrigger(hour=6, minute=0))
    scheduler.add_job(task_daily_revenue_scan, CronTrigger(hour=7, minute=30))
    scheduler.add_job(task_daily_content_engine, CronTrigger(hour=8, minute=0))
    scheduler.add_job(task_daily_notion_sync, CronTrigger(hour=8, minute=15))
    scheduler.add_job(task_tri_core_pulse, CronTrigger(hour=8, minute=30))
    scheduler.add_job(task_sprint_profit_tracker, CronTrigger(hour=9, minute=0))
    scheduler.add_job(task_sprint_hype_engine, CronTrigger(hour=10, minute=30))
    scheduler.add_job(task_sprint_eod_report, CronTrigger(hour=21, minute=0))

    scheduler.add_job(
        task_weekly_offer_optimization,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
    )
    scheduler.add_job(
        task_weekly_cashflow_forecast,
        CronTrigger(day_of_week="fri", hour=9, minute=0),
    )

    scheduler.add_job(
        task_monthly_reset,
        CronTrigger(day=1, hour=10, minute=0),
    )

    return scheduler


def main():
    # Uncomment the next line the very first time you kick off the sprint:
    # run_day_one_bootstrap()

    scheduler = build_scheduler()
    print(f"Actionuity Scheduler running with timezone {TIMEZONE}")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler stopped.")


if __name__ == "__main__":
    main()
