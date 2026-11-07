# UbuntuReport API

**Project Name:** UbuntuReport

**Author:** Adesina Olagunju ([daadesina1@gmail.com](mailto:daadesina1@gmail.com))

**Date:** 23 October 2025

---

## Table of Contents

- [UbuntuReport API](#ubuntureport-api)
  - [Table of Contents](#table-of-contents)
  - [Overview](#overview)
  - [Features](#features)
  - [Technologies](#technologies)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Usage](#usage)
  - [API Endpoints](#api-endpoints)
    - [News Articles](#news-articles)
    - [Categories](#categories)
  - [Cron Endpoints](#cron-endpoints)
  - [Models](#models)
    - [NewsArticle](#newsarticle)
  - [License](#license)

---

## Overview

**UbuntuReport** is a Django-based API designed to aggregate news articles from multiple international sources and provide users with fast access to news across various categories. It fetches news via RSS feeds, stores them in a database, and exposes searchable and filterable REST API endpoints.

---

## Features

* Fetch news from multiple sources:

  * BBC, CNN, Al Jazeera, The Guardian, Channels TV, Premium Times, Vanguard
* Categorized news articles
* Automatic deduplication of articles
* Searchable and filterable API endpoints
* Scheduled fetching of news triggered by an external cron/ping service
* REST API with pagination

---

## Technologies

* Python 3.x
* Django 5.2
* Django REST Framework (DRF)
* Django Filters
* PostgreSQL (Supabase in production)
* External cron/ping service for scheduled runs
* Feedparser for RSS feed parsing

---

## Installation

1. Clone the repository:

```bash
git clone <repository_url>
cd emergency_news
```

2. Create a virtual environment and activate it:

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Apply migrations:

```bash
python manage.py migrate
```

5. Create a superuser (optional, for Django admin):

```bash
python manage.py createsuperuser
```

---

## Configuration

* **Database:** Configure `DATABASE_URL` for PostgreSQL/Supabase.
* **Cron authentication:** Set `CRON_SECRET` to require `X-Cron-Secret` or `?token=...` on cron endpoints. If unset, the endpoints are open.
* **Cron concurrency:** `CRON_FETCH_CONCURRENCY` controls how many sources fetch in parallel (default 4); `CRON_MAX_WORKERS` controls the async job pool (default 4).

---

## Usage

1. Run the Django development server:

```bash
python manage.py runserver
```

2. Point your external cron/ping service at the endpoints below:

```bash
curl "https://your-api.example.com/api/cron/fetch/?token=$CRON_SECRET"
curl "https://your-api.example.com/api/cron/cleanup/?token=$CRON_SECRET"
```

3. Fetch news manually (optional):

```bash
python manage.py get_all_news
# or
python manual_tasks.py
```

---

## API Endpoints

### News Articles

| Method | Endpoint          | Description                                                    |
| ------ | ----------------- | -------------------------------------------------------------- |
| GET    | `/api/news/`      | List all news articles (paginated, searchable, and filterable) |
| GET    | `/api/news/{id}/` | Retrieve a single article by ID                                |

**Search & Filtering:**

* `search` query parameter: searches in `title`, `category`, `summary`, and `source`
* `category` query parameter: filters by category
* `source` query parameter: filters by news source

Example:

```
/api/news/?search=technology&category=world&source=BBC
```

---

### Categories

| Method | Endpoint           | Description                |
| ------ | ------------------ | -------------------------- |
| GET    | `/api/categories/` | List all unique categories |

---

## Cron Endpoints

Periodic work is triggered by an external cron/ping service. The endpoints
return `202 Accepted` immediately and run the work in a background thread pool
inside the web process.

> The old Celery/Redis/Docker files may still be present in the repository for
> reference, but the application no longer starts or requires them.

| Method | Endpoint | Description |
| ------ | -------- | ----------- |
| GET/POST | `/api/cron/fetch/` | Fetch every registered source |
| GET/POST | `/api/cron/fetch/<command_name>/` | Fetch one source, e.g. `fetch_bbc_news` |
| GET/POST | `/api/cron/cleanup/` | Delete articles older than 31 days |
| GET/POST | `/api/cron/populate-countries/` | Seed `Country` rows from `SOURCE_COUNTRY_MAP` |
| GET | `/api/cron/runs/` | List recent in-process runs |
| GET | `/api/cron/runs/<run_id>/` | Check one run's status/result |
| GET | `/api/cron/` | Discovery/health response |

If `CRON_SECRET` is set, include it as `X-Cron-Secret: <secret>` or
`?token=<secret>`. Example hourly pings:

```bash
curl -H "X-Cron-Secret: $CRON_SECRET" https://your-api.example.com/api/cron/fetch/
curl -H "X-Cron-Secret: $CRON_SECRET" https://your-api.example.com/api/cron/cleanup/
```

---

## Models

### NewsArticle

| Field       | Type      | Description                  |
| ----------- | --------- | ---------------------------- |
| `id`        | AutoField | Primary key                  |
| `category`  | CharField | News category                |
| `title`     | CharField | News title                   |
| `link`      | URLField  | Unique link to the article   |
| `published` | DateTime  | Publication datetime         |
| `summary`   | TextField | Short summary of the article |
| `source`    | CharField | News source name             |

---

## License

This project is developed by **Adesina Olagunju**. All rights reserved.
