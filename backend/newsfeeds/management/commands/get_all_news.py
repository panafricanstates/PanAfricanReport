from django.core.management.base import BaseCommand

from cron_tasks.jobs import fetch_all_sources


class Command(BaseCommand):
    help = (
        "Fetch all registered news sources synchronously. "
        "Scheduled runs should use GET /api/cron/fetch/ instead."
    )

    def handle(self, *args, **kwargs):
        result = fetch_all_sources()
        self.stdout.write(
            self.style.SUCCESS(
                f"Fetched {result['total']} sources: "
                f"{result['succeeded']} succeeded, {result['failed']} failed."
            )
        )
        for item in result["results"]:
            if item["status"] == "failed":
                self.stdout.write(
                    self.style.ERROR(f"{item['command']}: {item.get('error')}")
                )
