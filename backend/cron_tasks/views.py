"""HTTP endpoints used by the external cron/ping service."""

from __future__ import annotations

from django.conf import settings
from django.utils.crypto import constant_time_compare
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from newsfeeds.news_commands import NEWS_COMMANDS

from . import jobs, runner


def _secret_ok(request) -> bool:
    expected = getattr(settings, "CRON_SECRET", "")
    if not expected:
        return True
    provided = request.headers.get("X-Cron-Secret") or request.query_params.get("token")
    return bool(provided) and constant_time_compare(provided, expected)


def _forbidden() -> Response:
    return Response(
        {"detail": "Invalid or missing cron secret."},
        status=status.HTTP_403_FORBIDDEN,
    )


def _queue(job_name: str, func) -> Response:
    run, started = runner.submit_job(job_name, func)
    return Response(
        {
            "job": job_name,
            "run_id": run.run_id,
            "status": run.status,
            "started": started,
            "message": "Job started." if started else "Job is already running.",
            "status_url": f"/api/cron/runs/{run.run_id}/",
        },
        status=status.HTTP_202_ACCEPTED,
    )


@api_view(["GET", "POST"])
def cron_root(request):
    """Small discovery/health response for the pinger."""
    if not _secret_ok(request):
        return _forbidden()
    return Response(
        {
            "status": "ok",
            "auth_required": bool(getattr(settings, "CRON_SECRET", "")),
            "jobs": {
                "fetch_all": "/api/cron/fetch/",
                "fetch_one": "/api/cron/fetch/<command_name>/",
                "cleanup": "/api/cron/cleanup/",
                "populate_countries": "/api/cron/populate-countries/",
                "runs": "/api/cron/runs/",
            },
            "fetch_commands": NEWS_COMMANDS,
        }
    )


@api_view(["GET", "POST"])
def fetch_all(request):
    """Queue every registered news fetch command."""
    if not _secret_ok(request):
        return _forbidden()
    return _queue("fetch_all", jobs.fetch_all_sources)


@api_view(["GET", "POST"])
def fetch_one(request, command_name: str):
    """Queue a single fetch command, e.g. ``/api/cron/fetch/fetch_bbc_news/``."""
    if not _secret_ok(request):
        return _forbidden()
    if command_name not in NEWS_COMMANDS:
        return Response(
            {
                "detail": f"Unknown fetch command: {command_name}",
                "fetch_commands": NEWS_COMMANDS,
            },
            status=status.HTTP_404_NOT_FOUND,
        )
    return _queue(f"fetch:{command_name}", lambda: jobs.fetch_source(command_name))


@api_view(["GET", "POST"])
def cleanup(request):
    """Queue the old-article cleanup that used to run daily via Celery Beat."""
    if not _secret_ok(request):
        return _forbidden()
    return _queue("cleanup_old_news", jobs.cleanup_old_news)


@api_view(["GET", "POST"])
def populate_countries(request):
    """Queue ``populate_countries`` (needed after a fresh deployment)."""
    if not _secret_ok(request):
        return _forbidden()
    return _queue("populate_countries", jobs.populate_countries)


@api_view(["GET"])
def run_list(request):
    """List recent in-process runs."""
    if not _secret_ok(request):
        return _forbidden()
    return Response(
        {
            "runs": [
                run.as_dict(include_result=False) for run in runner.list_runs()
            ]
        }
    )


@api_view(["GET"])
def run_detail(request, run_id):
    """Return the status/result of one run."""
    if not _secret_ok(request):
        return _forbidden()
    run = runner.get_run(str(run_id))
    if run is None:
        return Response(
            {"detail": "Run not found."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(run.as_dict())
