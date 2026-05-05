# BlackCoffee

A daily scraper and RSS grabber to get you started in the morning. BlackCoffee aggregates news from various sources and presents them in a clean, scrollable, newspaper-like layout.

## Features
- **RSS & Web Scraping**: Automatically pull articles from RSS feeds or use Playwright to scrape traditional web pages.
- **Offline Translation**: Integrates `argostranslate` for 100% self-hosted, offline translation of foreign sources (e.g., Swedish to English).
- **Background Tasks**: Powered by Celery and Valkey to ensure schedules are met and to catch up on missed scrapes when your machine is offline.
- **Dockerized**: The entire stack (Django, Celery Worker, Celery Beat, Valkey) fits perfectly into a single `docker-compose.yml`.

## Quickstart

```bash
docker compose up --build
```
