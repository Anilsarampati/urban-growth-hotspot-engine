from __future__ import annotations

import argparse
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from urban_growth.ingestion import run_ingestion
from urban_growth.pipeline import run_pipeline


def run_monthly_refresh() -> None:
    print(f"[{datetime.now().isoformat()}] Starting monthly refresh job")
    run_ingestion()
    output_df = run_pipeline(tune_weights=True)
    print(f"[{datetime.now().isoformat()}] Refresh complete. Zones scored: {len(output_df)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Monthly ingestion + retraining + scoring scheduler")
    parser.add_argument(
        "--run-once",
        action="store_true",
        help="Run refresh immediately and exit",
    )
    args = parser.parse_args()

    if args.run_once:
        run_monthly_refresh()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(
        run_monthly_refresh,
        CronTrigger(day=1, hour=3, minute=0),
        id="urban_growth_monthly_refresh",
        replace_existing=True,
    )

    print("Scheduler started. Monthly refresh set for day 1 at 03:00.")
    scheduler.start()


if __name__ == "__main__":
    main()
