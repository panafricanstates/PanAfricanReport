# PanAfricanReport Backend Architecture Study

## 1. Project Overview

PanAfricanReport is a Django REST Framework-based news aggregation API that collects news articles from 31 RSS feed sources across Africa and international media, stores them in PostgreSQL, and serves them via a filterable/paginated REST API. The backend runs inside Docker with Celery for background task scheduling.

**Tech Stack:** Django 5.2, DRF, Celery + Redis, PostgreSQL (Supabase), Docker, feedparser, BeautifulSoup4.

---

## 2. Directory Structure

```
backend/
  panafricanreport/          # Django project package
    settings.py            # Django + DRF + Celery config
    urls.py                # Root URL routing + Swagger
    celery.py              # Celery app + beat schedule
    wsgi.py / asgi.py      # WSGI/ASGI entry points
  newsfeeds/               # Core Django app
    models.py              # Country, NewsArticle models
    views.py               # DRF ViewSets + custom API views
    serializers.py         # DRF serializers
    urls.py                # API URL routing
    admin.py               # Empty (not registered)
    pagination.py          # Custom HTTPS pagination
    utils.py               # OG image scraper (fetch_og_image)
    source_country_map.py  # Source-to-country mapping dict
    news_commands.py       # List of all 31 fetch command names
    tasks.py               # Dynamic Celery task generation
    tasks_cleanup.py       # Cleanup task (31-day TTL)
    management/commands/   # 31 fetch commands + 2 utility commands
  manual_tasks.py          # Standalone script to trigger all tasks
  run_fetch_tasks.sh       # Shell wrapper for Docker execution
  docker-compose.yml       # 4 services: redis, django, celery_worker, celery_beat
  Dockerfile               # Python 3.12-slim image
  requirements.txt         # 43 pinned dependencies
```

---

## 3. Data Models

### `Country` (`newsfeeds/models.py:4`)
| Field | Type | Notes |
|-------|------|-------|
| `name` | CharField(100) | unique |

Populated via `populate_countries` management command from `SOURCE_COUNTRY_MAP` keys.

### `NewsArticle` (`newsfeeds/models.py:10`)
| Field | Type | Notes |
|-------|------|-------|
| `title` | CharField(500) | |
| `link` | URLField | **unique** - used for deduplication |
| `published` | DateTimeField | |
| `summary` | TextField | HTML content, stripped at serialization |
| `source` | CharField(100) | e.g. "BBC", "Vanguard", "CNN" |
| `image` | CharField(1000) | OG image URL, nullable |
| `category` | CharField(100) | RSS feed category key, nullable |
| `country` | ForeignKey(Country) | auto-assigned on save via `source_country_map` |

**Auto-assignment logic** (`models.py:25-34`): On `save()`, if `country` is not set, `get_country_by_source()` looks up the source name in `SOURCE_COUNTRY_MAP` to find which country list it belongs to, then queries the `Country` table for a case-insensitive match.

---

## 4. How RSS Feeds Are Extracted

### 4.1 Per-Source Management Commands

Each news source has its own Django management command under `newsfeeds/management/commands/fetch_<source>_news.py`. There are **31 fetch commands** registered in `newsfeeds/news_commands.py`.

**All 31 commands follow an identical pattern:**

1. **Define RSS feed URLs** as a Python dict mapping category keys to URLs:
   ```python
   BBC_FEEDS = {
       "top_stories": "https://feeds.bbci.co.uk/news/rss.xml",
       "world": "https://feeds.bbci.co.uk/news/world/rss.xml",
       ...
   }
   ```
   Some sources with a single feed use a plain URL string instead of a dict.

2. **Parse the RSS feed** using `feedparser.parse(url)`.

3. **Iterate entries** and extract:
   - `title` from `entry.get("title")`
   - `link` from `entry.get("link")` (skip if missing - this is the dedup key)
   - `summary` from `entry.get("summary")`, falling back to `entry.content[0].value`
   - `published` from `entry.get("published_parsed")` or `entry.get("updated_parsed")`, converted via `datetime(*published_parsed[:6])`, defaulting to `datetime.now()`

4. **Deduplication** via `NewsArticle.objects.get_or_create(link=link, ...)` - the unique `link` field prevents duplicate articles.

5. **OG Image extraction** (only for newly created articles): `fetch_og_image(link)` from `newsfeeds/utils.py` scrapes the article's HTML for:
   - Open Graph `<meta property="og:image">`
   - Twitter Card `<meta name="twitter:image">`
   - First `<img>` tag in body (fallback)
   - Falls back to a Cloudinary-hosted placeholder image

6. **Source field** is hardcoded per command (e.g., `"BBC"`, `"Vanguard"`, `"CNN"`).

### 4.2 Category Classification

Categories come directly from the **RSS feed URL structure**, not from any content analysis:

- **Multi-category sources** (BBC, CNN, Vanguard, Channels TV, Premium Times, Al Jazeera, The Guardian, MaliWeb, Modern Ghana, GH Headlines): The category is the Python dict key mapping to that feed URL. Examples: `"top_stories"`, `"world"`, `"africa"`, `"business"`, `"technology"`, `"politics"`, `"sports"`, `"entertainment"`, `"latest"`, `"latest_posts"`, `"politique"`, etc.

- **Single-feed sources** (AllAfrica, MyJoyOnline, The Point, FatuNetwork, Dakaractu, Kassataya, Cocorioko, etc.): Category is hardcoded as either `"africa"` (AllAfrica) or `"general"` (all others).

**Summary:** There is **no AI/ML classification**. Categories are structural labels derived from which RSS feed URL was used, or hardcoded defaults for single-feed sources.

### 4.3 Country Assignment

Country is **not** derived from article content. It is assigned at the model level:

1. `source_country_map.py` maintains `SOURCE_COUNTRY_MAP` - a dict mapping 48 African country names to lists of source name strings.
2. When `NewsArticle.save()` runs and `country` is `None`, it calls `get_country_by_source(self.source)` which iterates the map to find which country list contains the source name.
3. If found, it queries `Country.objects.filter(name__iexact=country_name).first()`.

**Example mappings:**
- `"Vanguard"` -> `"Nigeria"`
- `"Modern Ghana"` -> `"Ghana"`
- `"Dakaractu"` -> `"Senegal"`
- `"Kassataya"` -> `"Mauritania"`
- International sources (BBC, CNN, Al Jazeera, The Guardian, AllAfrica) have **no country mapping** (they map to empty lists or are not listed).

---

## 5. Task Scheduling (Celery)

### 5.1 Dynamic Task Generation (`newsfeeds/tasks.py`)

Instead of writing 31 separate Celery tasks, the system dynamically creates them:

```python
def make_task(cmd_name):
    @shared_task(name=cmd_name)
    def task():
        call_command(cmd_name)
    return task

for cmd in NEWS_COMMANDS:
    globals()[cmd] = make_task(cmd)
```

Each task simply calls the corresponding Django management command via `call_command()`.

### 5.2 Beat Schedule (`panafricanreport/celery.py`)

All 31 fetch tasks run **every hour** on the hour (`crontab(minute=0, hour='*')`). A cleanup task runs daily at 00:30 to delete articles older than 31 days.

### 5.3 Docker Services (`docker-compose.yml`)

| Service | Purpose |
|---------|---------|
| `redis` | Redis 7 Alpine, broker + cache |
| `django` | Gunicorn on port 9000, runs migrations |
| `celery_worker` | `celery -A panafricanreport worker -l info` |
| `celery_beat` | `celery -A panafricanreport beat -l info` |

---

## 6. API Layer

### 6.1 URL Structure (`panafricanreport/urls.py`, `newsfeeds/urls.py`)

```
/api/news/                     -> NewsArticleViewSet (list/retrieve)
/api/news/{id}/                -> NewsArticleViewSet (retrieve)
/api/news/top-sources-recent/  -> top_sources_recent_news view
/api/categories/               -> categories_list view
/api/countries/                -> countries_list view
/admin/                        -> Django admin
/swagger/                      -> Swagger UI
/redoc/                        -> ReDoc
```

### 6.2 Filtering & Search (`newsfeeds/views.py`)

**`NewsArticleViewSet`** (read-only):
- `?search=` - full-text search across title, category, summary, source, country name
- `?category=` - filter by category (icontains)
- `?source=` - filter by source (icontains)
- `?country=` - filter by country name (iexact)
- `?sources=` - comma-separated normalized source names (e.g. `?sources=bbc,vanguard`)
- `?time_frame=` - temporal filters: `today`, `yesterday`, `last_7_days`, `last_30_days`, `this_week`, `last_week`, `this_month`, `last_month`, `this_year`, `last_year`, `YYYY-MM`, `YYYY`

**`top_sources_recent_news`**: Returns articles from priority sources (Nigeria sources + BBC/CNN) published in the last 1 hour.

### 6.3 Pagination (`newsfeeds/pagination.py`)

Custom `HttpsPagination` (extends `PageNumberPagination`, page_size=40) that forces HTTPS on next/previous links unless pointing to localhost.

### 6.4 Serialization (`newsfeeds/serializers.py`)

`NewsArticleSerializer` strips HTML tags from the `summary` field using BeautifulSoup before returning it to the client.

---

## 7. Complete Source Registry (31 Sources)

### International (no country assignment)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| BBC | `fetch_bbc_news` | 5 feeds (top_stories, world, africa, business, technology) | from feed key |
| CNN | `fetch_cnn_news` | 2 feeds (top_stories, world) | from feed key |
| Al Jazeera | `fetch_aljazeera_news` | 7 feeds (top_stories, middle_east, economy, technology, africa, asia, americas) | from feed key |
| The Guardian | `fetch_guardian_news` | 3 feeds (world, politics, business) | from feed key |
| AllAfrica | `fetch_allafrica_news` | 1 feed (Africa headlines) | "africa" |

### Nigeria (4 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| Vanguard | `fetch_vanguard_news` | 5 feeds | from feed key |
| Premium Times | `fetch_premiumtimes_news` | 5 feeds | from feed key |
| The Guardian | `fetch_guardian_news` | 3 feeds | from feed key |
| Channels TV | `fetch_channelstv_news` | 5 feeds | from feed key |

### Ghana (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| Modern Ghana | `fetch_modernghana_news` | 4 feeds | from feed key |
| MyJoyOnline | `fetch_myjoyonline_news` | 1 feed | "general" |
| GH Headlines | `fetch_ghheadlines_news` | 1 feed | from feed key |

### Gambia (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| The Standard | `fetch_standard_news` | 1 feed | "general" |
| The Point | `fetch_thepoint_news` | 1 feed | "general" |
| FatuNetwork | `fetch_fatunetwork_news` | 1 feed | "general" |

### Mali (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| MaliWeb | `fetch_maliweb_news` | 6 feeds | from feed key |
| L'Express du Mali | `fetch_lexpressdumali_news` | 1 feed | "general" |
| Bamada | `fetch_bamada_news` | 1 feed | "general" |

### Mauritania (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| Kassataya | `fetch_kassataya_news` | 1 feed | "general" |
| Le Calame | `fetch_lecalame_news` | 1 feed | "general" |
| Tawary | `fetch_tawary_news` | 1 feed | "general" |

### Niger (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| NigerExpress | `fetch_nigerexpress_news` | 1 feed | "general" |
| Le Sahel | `fetch_lesahel_news` | 1 feed | "general" |
| AirInfoAgadez | `fetch_airinfoagadez_news` | 1 feed | "general" |

### Senegal (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| Dakaractu | `fetch_dakaractu_news` | 1 feed | "general" |
| Thiesinfo | `fetch_thiesinfo_news` | 1 feed | "general" |
| TerangaTimesN | `fetch_terangatimesn_news` | 1 feed | "general" |

### Sierra Leone (3 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| Cocorioko | `fetch_cocorioko_news` | 1 feed | "general" |
| The Calabash Newspaper | `fetch_calabash_news` | 1 feed | "general" |
| CritiqueEcho | `fetch_critiqueecho_news` | 1 feed | "general" |

### Togo (2 sources)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| iciLome | `fetch_icilome_news` | 1 feed | "general" |
| LomeInfos | `fetch_lomeInfos_news` | 1 feed | "general" |

### Liberia (1 source via AllAfrica)
| Source | Command | RSS Feed(s) | Category |
|--------|---------|-------------|----------|
| AllAfrica Liberia | `fetch_allafrica_liberia_news` | 1 RDF feed | "general" |

---

## 8. Key Architectural Observations

1. **No content-based classification**: Categories are entirely derived from which RSS feed URL an article came from, or hardcoded to "general"/"africa". There is no NLP, keyword analysis, or AI classification.

2. **No content-based country detection**: Country assignment is source-level, not article-level. An article from BBC about Nigeria still has `country=None` because BBC is not in any country's source list.

3. **Deduplication via URL**: The unique `link` field on `NewsArticle` is the sole deduplication mechanism. `get_or_create(link=link)` prevents storing the same article twice.

4. **Image fetching is post-hoc**: After an article is created, `fetch_og_image()` makes a separate HTTP request to the article's URL to scrape its Open Graph image. This adds latency and a network call per new article.

5. **Massive code duplication**: All 31 management commands are near-identical copies with only the source name, feed URLs, and category labels changed. This could be refactored into a single parameterized command.

6. **No admin registration**: `admin.py` is empty, so articles are not manageable via Django admin.

7. **31-day TTL**: Articles older than 31 days are deleted daily at 00:30 via the cleanup task.

8. **All tasks run hourly simultaneously**: All 31 fetch tasks are scheduled at the same crontab time (`minute=0, hour='*'`), meaning they all fire at once every hour, which could cause burst load.
