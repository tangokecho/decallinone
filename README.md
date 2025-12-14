# Actionuity Scheduler

A standalone Python scheduler that runs Actionuity sprint prompts on a daily, weekly, and monthly cadence using the OpenAI Responses API. Outputs are saved to timestamped markdown files in `logs/` for easy ingestion elsewhere (e.g., Notion).

## Setup

1. (Optional) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install openai apscheduler python-dotenv
   ```
3. Create a `.env` file alongside the script:
   ```env
   OPENAI_API_KEY=sk-...
   TIMEZONE=America/New_York
   ```

## Usage

1. Adjust the prompt text in `PROMPTS` inside `actionuity_scheduler.py` if you want to tune tone or structure.
2. (Optional) In `main()`, uncomment `run_day_one_bootstrap()` for the first run to trigger the initial set of tasks immediately.
3. Start the scheduler:
   ```bash
   python actionuity_scheduler.py
   ```

The scheduler will start running the daily sprint tasks plus weekly and monthly checks at the configured times, writing outputs into `logs/YYYY-MM-DD__<task>.md`.
