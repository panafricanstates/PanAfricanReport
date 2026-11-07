# Step 3 — New Platform Integration Report

## Overview

Added 15 new news platforms to PanAfricanReport, categorized into **World** (international news) and **Sport** (sports news) countries.

---

## Changes Made

### 1. Updated `source_country_map.py`

Added sources to the country mapping:

| Country | Sources Added |
|---|---|
| **World** | DW, France 24, Sky News, NPR World News, The New York Times, Le Monde International, The Hindu, The Japan Times |
| **Sport** | DW Sport, France 24 Sport, BBC Sport, Yahoo Sports, CBS Sports, Sporting News, World Soccer Talk |

### 2. Created 15 Management Commands

All commands follow the existing pattern: parse RSS feed → deduplicate via `link` → fetch OG image for new articles.

| Command File | Source | RSS URL | Category |
|---|---|---|---|
| `fetch_dw_news.py` | DW | `https://rss.dw.com/rdf/rss-en-all` | top_stories |
| `fetch_dw_sport_news.py` | DW Sport | `https://rss.dw.com/rdf/rss-en-sports` | latest |
| `fetch_france24_news.py` | France 24 | `https://www.france24.com/en/rss` | news |
| `fetch_france24_sport_news.py` | France 24 Sport | `https://www.france24.com/en/sport/rss` | latest_news |
| `fetch_skynews_news.py` | Sky News | `https://feeds.skynews.com/feeds/rss/world.xml` | general |
| `fetch_nprworld_news.py` | NPR World News | `https://feeds.npr.org/1004/rss.xml` | top_news |
| `fetch_nytimes_news.py` | The New York Times | `https://rss.nytimes.com/services/xml/rss/nyt/World.xml` | general |
| `fetch_lemonde_news.py` | Le Monde International | `https://www.lemonde.fr/en/international/rss_full.xml` | world_news |
| `fetch_thehindu_news.py` | The Hindu | `https://www.thehindu.com/news/international/feeder/default.rss` | latest_news |
| `fetch_japantimes_news.py` | The Japan Times | `https://www.japantimes.co.jp/feed/` | news |
| `fetch_bbc_sport_news.py` | BBC Sport | `https://feeds.bbci.co.uk/sport/rss.xml` | latest |
| `fetch_yahoosports_news.py` | Yahoo Sports | `https://sports.yahoo.com/rss/` | top_stories |
| `fetch_cbssports_news.py` | CBS Sports | `https://www.cbssports.com/rss/headlines/` | entertainment |
| `fetch_sportingnews_news.py` | Sporting News | `https://www.sportingnews.com/us/rss` | latest_news |
| `fetch_worldsoccertalk_news.py` | World Soccer Talk | `https://worldsoccertalk.com/feed/` | soccer |

### 3. Updated `news_commands.py`

Registered all 15 new commands in the `NEWS_COMMANDS` list for Celery task generation.

### 4. Database Update

Ran `populate_countries` to ensure "Sport" country exists in the database.

---

## Source Count Summary

| Category | Before | After | Added |
|---|---|---|---|
| World | 3 (BBC, CNN, Al Jazeera) | 11 | +8 |
| Sport | 0 | 7 | +7 |
| **Total Sources** | **31** | **46** | **+15** |

---

## File Locations

```
backend/
  newsfeeds/
    source_country_map.py          # Updated with new source mappings
    news_commands.py               # Updated with new command names
    management/commands/
      fetch_dw_news.py             # New
      fetch_dw_sport_news.py       # New
      fetch_france24_news.py       # New
      fetch_france24_sport_news.py # New
      fetch_skynews_news.py        # New
      fetch_nprworld_news.py       # New
      fetch_nytimes_news.py        # New
      fetch_lemonde_news.py        # New
      fetch_thehindu_news.py       # New
      fetch_japantimes_news.py     # New
      fetch_bbc_sport_news.py      # New
      fetch_yahoosports_news.py    # New
      fetch_cbssports_news.py      # New
      fetch_sportingnews_news.py   # New
      fetch_worldsoccertalk_news.py # New
```

---

## Next Steps

- Run a test fetch for one new command to verify RSS feeds work:
  ```bash
  python manage.py fetch_dw_news
  ```
- Restart Celery worker to pick up new tasks:
  ```bash
  docker compose restart celery_worker celery_beat
  ```
