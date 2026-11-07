"""Plain-Python implementations of the work previously run by Celery tasks.

The external pinger calls the endpoints in ``cron_tasks.views``; those views
hand these functions to ``cron_tasks.runner``, which executes them outside the
HTTP request/response cycle.
"""

from __future__ import annotations

import io
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import timedelta
from typing import Any

from django.conf import settings
from django.core.management import call_command
from django.db import close_old_connections
from django.utils import timezone

from newsfeeds.models import NewsArticle
from newsfeeds.news_commands import NEWS_COMMANDS

logger = logging.getLogger(__name__)

MAX_OUTPUT_CHARS = 20_000


def _truncate(value: str, limit: int = MAX_OUTPUT_CHARS) -> str:
    if len(value) <= limit:
        return value
    return f"{value[:limit]}\n... [truncated {len(value) - limit} chars]"


def _run_management_command(command_name: str) -> dict[str, Any]:
    """Run one Django management command and capture its console output."""
    close_old_connections()
    output = io.StringIO()
    try:
        call_command(command_name, stdout=output, stderr=output)
    except Exception as exc:  # noqa: BLE001 - one bad source must not stop the rest
        logger.exception("Cron management command failed: %s", command_name)
        return {
            "command": command_name,
            "status": "failed",
            "error": f"{type(exc).__name__}: {exc}",
            "output": _truncate(output.getvalue()),
        }
    finally:
        close_old_connections()

    return {
        "command": command_name,
        "status": "success",
        "output": _truncate(output.getvalue()),
    }


def fetch_source(command_name: str) -> dict[str, Any]:
    """Fetch one registered news source."""
    if command_name not in NEWS_COMMANDS:
        raise ValueError(f"Unknown fetch command: {command_name}")
    return _run_management_command(command_name)


def fetch_all_sources() -> dict[str, Any]:
    """Fetch every source registered in ``NEWS_COMMANDS``.

    A small bounded pool is used because the old Celery deployment ran these
    commands concurrently. Keep the concurrency low enough for the database
    and news sites.
    """
    commands = list(NEWS_COMMANDS)
    try:
        concurrency = max(1, int(getattr(settings, "CRON_FETCH_CONCURRENCY", 4)))
    except (TypeError, ValueError):
        concurrency = 4

    results: list[dict[str, Any]] = []
    if concurrency == 1:
        for command_name in commands:
            results.append(_run_management_command(command_name))
    else:
        with ThreadPoolExecutor(
            max_workers=concurrency,
            thread_name_prefix="cron-fetch",
        ) as pool:
            futures = {
                pool.submit(_run_management_command, command_name): command_name
                for command_name in commands
            }
            for future in as_completed(futures):
                results.append(future.result())

    results.sort(key=lambda item: item["command"])
    failed = [item for item in results if item["status"] == "failed"]
    return {
        "total": len(results),
        "succeeded": len(results) - len(failed),
        "failed": len(failed),
        "results": results,
    }


def cleanup_old_news(days: int = 31) -> dict[str, Any]:
    """Delete articles older than ``days`` (the old daily Celery task)."""
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = NewsArticle.objects.filter(published__lt=cutoff).delete()
    return {
        "deleted": deleted,
        "cutoff": cutoff.isoformat(),
        "days": days,
    }


def populate_countries() -> dict[str, Any]:
    """Ensure every country in ``SOURCE_COUNTRY_MAP`` exists in the DB."""
    return _run_management_command("populate_countries")
