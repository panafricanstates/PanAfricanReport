import time
import uuid
from unittest.mock import patch

from django.conf import settings
from django.test import SimpleTestCase, override_settings
from django.urls import reverse

from . import runner


def _wait_for(run_id, timeout=2.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        run = runner.get_run(run_id)
        if run is not None and run.status in {"success", "failed"}:
            return run
        time.sleep(0.01)
    return runner.get_run(run_id)


class RunnerTests(SimpleTestCase):
    def test_job_runs_to_completion(self):
        run, started = runner.submit_job(
            f"test-{uuid.uuid4()}",
            lambda: {"ok": True},
        )

        self.assertTrue(started)
        finished = _wait_for(run.run_id)
        self.assertEqual(finished.status, "success")
        self.assertEqual(finished.result, {"ok": True})

    def test_duplicate_job_is_not_stacked(self):
        job_name = f"test-{uuid.uuid4()}"

        def slow_job():
            time.sleep(0.2)
            return {"ok": True}

        first, first_started = runner.submit_job(job_name, slow_job)
        second, second_started = runner.submit_job(job_name, slow_job)

        self.assertTrue(first_started)
        self.assertFalse(second_started)
        self.assertEqual(first.run_id, second.run_id)
        _wait_for(first.run_id)


class CronViewTests(SimpleTestCase):
    def test_root_lists_jobs(self):
        response = self.client.get(reverse("cron_tasks:root"), {"token": settings.CRON_SECRET})

        self.assertEqual(response.status_code, 200)
        self.assertIn("fetch_all", response.json()["jobs"])

    @patch("cron_tasks.views.jobs.fetch_all_sources", return_value={"total": 0})
    def test_fetch_all_returns_202(self, _fetch_all):
        response = self.client.get(reverse("cron_tasks:fetch-all"), {"token": settings.CRON_SECRET})

        self.assertEqual(response.status_code, 202)
        self.assertIn("run_id", response.json())

    def test_unknown_fetch_command_returns_404(self):
        response = self.client.get(
            reverse("cron_tasks:fetch-one", args=["not_a_command"]),
            {"token": settings.CRON_SECRET},
        )

        self.assertEqual(response.status_code, 404)

    @override_settings(CRON_SECRET="secret")
    def test_secret_is_required_when_configured(self):
        self.assertEqual(
            self.client.get(reverse("cron_tasks:fetch-all")).status_code,
            403,
        )

        with patch("cron_tasks.views.jobs.fetch_all_sources", return_value={"total": 0}):
            response = self.client.get(
                reverse("cron_tasks:fetch-all"),
                {"token": "secret"},
            )
        self.assertEqual(response.status_code, 202)
