"""AI Daily Brief — entrypoint.

Usage:
    python main.py              Run once now and send the email.
    python main.py --dry-run    Run the pipeline, write preview.html, send nothing.
    python main.py --schedule   Stay running and fire every day at 09:00 local time.
"""

import argparse
import logging
import sys
import time
from datetime import datetime

try:
    from src import config, emailer, fetcher, summarizer
except ImportError:  # pragma: no cover - supports the flat-file layout used here.
    import config
    import emailer
    import fetcher
    import summarizer

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ai-brief")

MAX_ATTEMPTS = 3


def run_once(dry_run: bool = False) -> int:
    now = datetime.now(config.TIMEZONE)
    log.info("Starting digest run for %s", now.strftime("%Y-%m-%d %H:%M %Z"))

    stories = fetcher.fetch_news()
    if not stories:
        log.warning("No stories returned by Tavily. Nothing to send today.")
        return 1

    digest = summarizer.summarize(stories)
    if not digest["stories"]:
        log.warning("Summarizer produced no usable stories.")
        return 1

    if dry_run:
        with open("preview.html", "w", encoding="utf-8") as handle:
            handle.write(emailer.build_html(digest, now))
        log.info("Dry run complete. Open preview.html to review the email.")
        print("\n" + emailer.build_plaintext(digest, now))
        return 0

    emailer.send_digest(digest, now)
    return 0


def run_with_retries(dry_run: bool = False) -> int:
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return run_once(dry_run=dry_run)
        except Exception:
            log.exception("Attempt %d/%d failed", attempt, MAX_ATTEMPTS)
            if attempt == MAX_ATTEMPTS:
                return 1
            backoff = 30 * attempt
            log.info("Retrying in %ds", backoff)
            time.sleep(backoff)
    return 1


def run_scheduler() -> None:
    from apscheduler.schedulers.blocking import BlockingScheduler

    scheduler = BlockingScheduler(timezone=config.TIMEZONE)
    scheduler.add_job(
        run_with_retries,
        trigger="cron",
        hour=9,
        minute=0,
        id="daily_ai_brief",
        misfire_grace_time=3600,
    )
    log.info("Scheduler armed. Digest will be sent daily at 09:00 %s.", config.TIMEZONE)
    log.info("Keep this process running. Ctrl+C to stop.")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        log.info("Scheduler stopped.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily AI news digest.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the digest and write preview.html without sending email.",
    )
    parser.add_argument(
        "--schedule",
        action="store_true",
        help="Run continuously and send every day at 09:00 local time.",
    )
    args = parser.parse_args()

    if args.schedule:
        run_scheduler()
    else:
        sys.exit(run_with_retries(dry_run=args.dry_run))


if __name__ == "__main__":
    main()
