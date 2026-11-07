# backend/cron_tasks/urls.py
#
# Cron Tasks endpoints — triggered by an external ping/cron service.
# All endpoints support optional secret authentication via ``?token=report123``
# or ``X-Cron-Secret`` header. When ``CRON_SECRET`` is unset in settings the
# endpoints are open.
#
# Test example (replace ``$CRON_SECRET`` with your actual secret):
#   curl "https://your-api.example.com/api/cron/fetch/?token=$CRON_SECRET"
#
from django.urls import path

from . import views

app_name = "cron_tasks"

urlpatterns = [
    # Root discovery — lists available jobs and fetch commands.
    # GET /api/cron/
    path("", views.cron_root, name="root"),

    # Fetch every registered news source (47 commands from NEWS_COMMANDS).
    # Returns 202 immediately; work runs in a background thread pool.
    # GET /api/cron/fetch/?token=report123
    path("fetch/", views.fetch_all, name="fetch-all"),

    # Fetch a single source by its command name (e.g. ``fetch_bbc_news``).
    # Unknown names return 404.
    # GET /api/cron/fetch/fetch_bbc_news/?token=report123
    path("fetch/<str:command_name>/", views.fetch_one, name="fetch-one"),

    # Delete articles older than 31 days (the former daily Celery Beat task).
    # GET /api/cron/cleanup/?token=report123
    path("cleanup/", views.cleanup, name="cleanup"),

    # Seed the Country table from SOURCE_COUNTRY_MAP (run once after deployment).
    # GET /api/cron/populate-countries/?token=report123
    path("populate-countries/", views.populate_countries, name="populate-countries"),

    # List recent in-process job runs.
    # GET /api/cron/runs/?token=report123
    path("runs/", views.run_list, name="run-list"),

    # Return the status/result of one run by its ``run_id``.
    # GET /api/cron/runs/<run_id>/?token=report123
    path("runs/<uuid:run_id>/", views.run_detail, name="run-detail"),
]
