"""Legacy cleanup helper.

Use ``cron_tasks.jobs.cleanup_old_news`` for the active implementation.
"""

from datetime import timedelta

from django.utils import timezone

from .models import NewsArticle


def cleanup_old_news():
    cutoff_date = timezone.now() - timedelta(days=31)
    deleted_count, _ = NewsArticle.objects.filter(
        published__lt=cutoff_date
    ).delete()

    return f"Deleted {deleted_count} old news articles"
