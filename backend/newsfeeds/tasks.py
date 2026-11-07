"""Legacy task wrappers.

Celery is no longer used. These functions call management commands directly so
old imports keep working. New code should use ``cron_tasks.jobs`` instead.
"""

from datetime import timedelta

from django.core.management import call_command
from django.utils import timezone

from .models import NewsArticle
from .news_commands import NEWS_COMMANDS


def make_task(cmd_name):
    def task():
        return call_command(cmd_name)

    task.__name__ = cmd_name
    return task


for cmd in NEWS_COMMANDS:
    globals()[cmd] = make_task(cmd)


def cleanup_old_news():
    cutoff_date = timezone.now() - timedelta(days=31)
    NewsArticle.objects.filter(published__lt=cutoff_date).delete()
