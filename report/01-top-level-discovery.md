# Step 1 — Top-Level Discovery

## Repository Structure

```
PanAfricanReport2026/
├── backend/          # Django REST API
├── frontend/         # Next.js web app
└── report/           # Reports directory
```

---

## Project 1: `backend/` — PanAfricanReport API

| Attribute | Detail |
|---|---|
| **Language/Framework** | Python 3.x, Django 5.2, Django REST Framework 3.16 |
| **Project name** | `panafricanreport` |
| **Package manager** | `pip` (`requirements.txt` — 43 deps) |
| **Key dependencies** | `Django==5.2`, `djangorestframework==3.16`, `celery==5.5` (Redis broker), `django-cors-headers`, `django-filter`, `drf-yasg` (Swagger), `feedparser`, `gunicorn`, `psycopg2-binary`, `redis`, `beautifulsoup4` |
| **App(s)** | `newsfeeds` (main app with models, serializers, views, tasks) |
| **Entry point** | `manage.py` → `panafricanreport.settings`, served via `gunicorn` on port 9000 |
| **Infrastructure** | Docker Compose with 4 services: `redis`, `django`, `celery_worker`, `celery_beat` |
| **What it does** | Aggregates news articles from RSS feeds (BBC, CNN, Al Jazeera, The Guardian, Channels TV, Premium Times, Vanguard, AllAfrica, ModernGhana, etc.), stores them in a DB, and exposes searchable/filterable REST API endpoints. Uses Celery for hourly background fetching. |

**Detected models:** `NewsArticle` (id, category, title, link, published, summary, source)

**Detected endpoints:** `GET /api/news/`, `GET /api/news/{id}/`, `GET /api/categories/`

---

## Project 2: `frontend/` — Global Emergency News UI

| Attribute | Detail |
|---|---|
| **Language/Framework** | TypeScript, Next.js 15 (App Router), React 19, Tailwind CSS 4 |
| **Package manager** | `npm` (`package.json`) |
| **Key dependencies** | `next@15.4`, `react@19`, `axios`, `zustand` (state), `lucide-react` (icons), `@radix-ui/*` (headless UI), `class-variance-authority` + `tailwind-merge` (styling utils), `@gnews-io/gnews-io-js` (GNEWS API client), `world-countries` |
| **Entry point** | `src/app/page.tsx` (home page), `src/app/layout.tsx` (root layout) |
| **Dev tools** | TypeScript 5, ESLint 9, Tailwind CSS 4 |
| **What it does** | Frontend UI for browsing global emergency news. Uses the backend API (and/or GNEWS) to display categorized news articles with search/filter capabilities. |

**Detected source structure:** `src/app/` (pages + API routes), `src/components/`, `src/lib/`, `src/service/`, `src/store/`, `src/utils/`

---

## Key observations

- Both projects are part of the same monorepo: backend serves data, frontend consumes it.
- The backend has a heavy focus on African news sources (Nigeria, Ghana, plus global outlets).
- Celery + Redis handle scheduled RSS fetching (hourly).
- Frontend uses Zustand for client-side state management and Axios for HTTP.
- The backend's `newsfeeds` app is where all business logic lives (models, serializers, views, tasks, management commands).
- No tests seem to be present yet (empty `tests.py` likely).
- The frontend includes an `api/` directory under `src/app/`, suggesting it may also have API routes (Next.js API routes or server actions).

## Suggested next steps (for you to choose)

1. Study the `backend/newsfeeds/` app in detail (models, views, serializers, tasks, URLs).
2. Study the `frontend/src/` directory structure and key pages/components.
3. Explore the database schema and migration files.
4. Look at the deployment config (Docker, possibly Render).
