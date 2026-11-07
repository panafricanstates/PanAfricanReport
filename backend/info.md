FOR AUTOMATIC FETCHING

Celery/Redis are no longer used. An external cron/ping service should call:

    GET https://your-api.example.com/api/cron/fetch/
    GET https://your-api.example.com/api/cron/cleanup/

If CRON_SECRET is set, add the secret as a header or query parameter:

    curl -H "X-Cron-Secret: $CRON_SECRET" https://your-api.example.com/api/cron/fetch/
    curl "https://your-api.example.com/api/cron/fetch/?token=$CRON_SECRET"

The endpoints return 202 immediately and continue working in the background.
Check progress with:

    GET /api/cron/runs/
    GET /api/cron/runs/<run_id>/

Trigger a fetch manually (synchronous, may take a while):

    python manage.py get_all_news
    # or
    python manual_tasks.py
