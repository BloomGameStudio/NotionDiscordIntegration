import asyncio
import os
from datetime import datetime, timezone

import azure.functions as func

from src.infrastructure.config.settings import load_environment
from src.main import run_scheduled_sync
from src.utils.logging import logger


SYNC_CRON = os.getenv("SYNC_CRON", "0 0 */4 * * *")

app = func.FunctionApp()


@app.timer_trigger(arg_name="timer", schedule=SYNC_CRON, run_on_startup=False, use_monitor=True)
def notion_discord_sync(timer: func.TimerRequest) -> None:
    """Timer-triggered Azure Function for Notion -> Discord sync."""
    if timer.past_due:
        logger.warning("Timer trigger is running later than scheduled")

    logger.info(
        "Running scheduled sync at %s",
        datetime.now(timezone.utc).isoformat(),
    )

    try:
        settings = load_environment()
        asyncio.run(run_scheduled_sync(settings))
    except Exception as exc:
        logger.error("Scheduled sync failed: %s", exc, exc_info=True)
        raise
