"""Run all news fetches synchronously from the command line.

This is the non-Celery replacement for the old manual_tasks.py script. For
scheduled runs, use the ``/api/cron/fetch/`` endpoint instead.
"""

import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "emergency_news.settings")
django.setup()

from cron_tasks.jobs import fetch_all_sources


def run_all_fetch_tasks():
    result = fetch_all_sources()
    print(
        f"Fetched {result['total']} sources: "
        f"{result['succeeded']} succeeded, {result['failed']} failed."
    )
    for item in result["results"]:
        if item["status"] == "failed":
            print(f"FAILED {item['command']}: {item.get('error')}")
    return result


if __name__ == "__main__":
    run_all_fetch_tasks()
