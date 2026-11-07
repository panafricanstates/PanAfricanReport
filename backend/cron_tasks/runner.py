"""In-process asynchronous job runner.

This replaces Celery/Redis for the cron endpoints. A request only queues work
and returns immediately; a bounded thread pool inside the web process performs
the actual fetch/cleanup work.
"""

from __future__ import annotations

import json
import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Callable

from django.conf import settings
from django.db import close_old_connections
from django.utils import timezone

logger = logging.getLogger(__name__)

MAX_RUNS = 200


def _setting_int(name: str, default: int) -> int:
    try:
        return max(1, int(getattr(settings, name, default)))
    except (TypeError, ValueError):
        return default


@dataclass
class JobRun:
    run_id: str
    job_name: str
    status: str = "queued"
    queued_at: str = field(default_factory=lambda: timezone.now().isoformat())
    started_at: str | None = None
    finished_at: str | None = None
    result: Any = None
    error: str | None = None

    def as_dict(self, include_result: bool = True) -> dict[str, Any]:
        data = {
            "run_id": self.run_id,
            "job_name": self.job_name,
            "status": self.status,
            "queued_at": self.queued_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "error": self.error,
        }
        if include_result:
            data["result"] = self.result
        return data


_runs: dict[str, JobRun] = {}
_runs_lock = threading.Lock()
_active_jobs: dict[str, str] = {}
_active_lock = threading.Lock()

_executor: ThreadPoolExecutor | None = None
_executor_lock = threading.Lock()


def _get_executor() -> ThreadPoolExecutor:
    """Create the pool lazily so pre-fork servers stay fork-safe."""
    global _executor
    if _executor is None:
        with _executor_lock:
            if _executor is None:
                _executor = ThreadPoolExecutor(
                    max_workers=_setting_int("CRON_MAX_WORKERS", 4),
                    thread_name_prefix="cron-job",
                )
    return _executor


def _json_safe(value: Any) -> Any:
    """Make job results safe for DRF's JSON renderer."""
    return json.loads(json.dumps(value, default=str))


def _prune_runs_locked() -> None:
    if len(_runs) <= MAX_RUNS:
        return
    finished = [run for run in _runs.values() if run.status in {"success", "failed"}]
    finished.sort(key=lambda run: run.queued_at)
    for run in finished[: max(0, len(_runs) - MAX_RUNS)]:
        _runs.pop(run.run_id, None)


def _update_run(run_id: str, **fields: Any) -> None:
    with _runs_lock:
        run = _runs.get(run_id)
        if run is None:
            return
        for key, value in fields.items():
            setattr(run, key, value)


def submit_job(job_name: str, func: Callable[[], Any]) -> tuple[JobRun, bool]:
    """Queue a job and return ``(run, started)``.

    If a job with the same name is already queued/running, the existing run is
    returned with ``started=False``. This prevents repeated pings from stacking
    duplicate work when a previous run is still busy.
    """
    with _active_lock:
        existing_id = _active_jobs.get(job_name)
        if existing_id:
            with _runs_lock:
                existing = _runs.get(existing_id)
            if existing is not None and existing.status in {"queued", "running"}:
                return existing, False
            _active_jobs.pop(job_name, None)

        run = JobRun(run_id=str(uuid.uuid4()), job_name=job_name)
        with _runs_lock:
            _runs[run.run_id] = run
            _prune_runs_locked()
        _active_jobs[job_name] = run.run_id

    try:
        _get_executor().submit(_execute_job, run.run_id, job_name, func)
    except Exception as exc:  # pragma: no cover - only if the pool is shut down
        logger.exception("Could not queue cron job: %s", job_name)
        _update_run(
            run.run_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            finished_at=timezone.now().isoformat(),
        )
        with _active_lock:
            if _active_jobs.get(job_name) == run.run_id:
                _active_jobs.pop(job_name, None)
        raise

    return run, True


def _execute_job(run_id: str, job_name: str, func: Callable[[], Any]) -> None:
    logger.info("Cron job started: %s (%s)", job_name, run_id)
    _update_run(run_id, status="running", started_at=timezone.now().isoformat())
    close_old_connections()
    try:
        result = _json_safe(func())
    except Exception as exc:  # noqa: BLE001 - job failures must not kill the runner
        logger.exception("Cron job failed: %s (%s)", job_name, run_id)
        _update_run(
            run_id,
            status="failed",
            error=f"{type(exc).__name__}: {exc}",
            finished_at=timezone.now().isoformat(),
        )
    else:
        _update_run(
            run_id,
            status="success",
            result=result,
            finished_at=timezone.now().isoformat(),
        )
        logger.info("Cron job finished: %s (%s)", job_name, run_id)
    finally:
        close_old_connections()
        with _active_lock:
            if _active_jobs.get(job_name) == run_id:
                _active_jobs.pop(job_name, None)


def get_run(run_id: str) -> JobRun | None:
    with _runs_lock:
        return _runs.get(run_id)


def list_runs(limit: int = 50) -> list[JobRun]:
    with _runs_lock:
        runs = sorted(_runs.values(), key=lambda run: run.queued_at, reverse=True)
    return runs[: max(1, limit)]
