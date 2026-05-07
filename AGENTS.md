# AGENTS.md — BlackCoffee

Guidance for AI agents working in this repository.

---

## Project overview

BlackCoffee is a self-hosted Django 6 web application that aggregates news from configurable sources, serves a daily dad joke, sends notifications, and presents everything on a newspaper-style frontpage.

---

## Tech stack

| Layer | Technology |
|---|---|
| Web framework | Django 6 |
| Task queue | Celery 5 |
| Task broker | Valkey 7.2 (Redis-compatible) |
| Task scheduler | Celery Beat with `django_celery_beat` DB scheduler |
| Web scraping | Playwright (Chromium, headless) |
| RSS parsing | feedparser |
| Translation | Argos Translate (offline) / Deep Translator (Google, fallback) |
| Database | SQLite (file: `db.sqlite3`) |
| Container runtime | Docker Compose |

---

## Repository layout

```
blackcoffee/          Django project package (settings, urls, celery, wsgi, asgi)
apps/
  accounts/           User auth, UserProfile (timezone preference), signup/login/profile views
  dadjokes/           Daily joke fetched from icanhazdadjoke.com, rating/view tracking
  frontend/           Frontpage view — newspaper layout grouping articles by source
  news/               Core news app: Source, Article, Category, ScrapeState, TranslationSetting
  notifications/      Per-user notification preferences (email) and send log
templates/            Global templates (base layout, etc.)
entrypoint.sh         Docker entrypoint: runs migrations, registers Celery Beat periodic task
seed_test_data.py     Seeds BleepingComputer RSS articles for development
manage.py
requirements.txt
docker-compose.yml
Dockerfile            Base image: mcr.microsoft.com/playwright/python:v1.42.0-jammy
```

---

## Apps in detail

### `apps/news`
- **Models:** `Source`, `Article`, `Category`, `ScrapeState`, `TranslationSetting`
- **Tasks (`tasks.py`):**
  - `run_rss_scraper(source_id)` — parses RSS feed, creates `Article` records, translates if configured
  - `run_web_scraper(source_id)` — Playwright headless scrape, supports login
  - `test_scrape_task(source_id)` — auto-detects scrape type (RSS vs web) for a new source
  - `catchup_scrapers()` — runs all sources; scheduled every 15 minutes via Celery Beat
- **Utils (`utils.py`):** `detect_rss_feed(url)` probes a URL for an RSS/Atom feed; `translate_text(...)` dispatches to Argos or Deep Translator based on `TranslationSetting`
- **Admin:** `SourceAdmin` has a custom "Test Scrape" preview action at `/<source_id>/test_scrape/`

### `apps/accounts`
- **Models:** `UserProfile` (OneToOne with `User`, stores timezone)
- **Signals:** `post_save` on `User` — uses `get_or_create` to ensure every user always has a `UserProfile` (handles users created before the app existed, e.g. superusers)
- **Views:** `signup`, `profile` (requires login)
- **Auth views** (login/logout) use Django's built-in `LoginView`/`LogoutView`

### `apps/dadjokes`
- **Models:** `Joke`, `DadJokeSettings`, `JokeView`, `JokeRating`
- **Task:** `fetch_joke_of_the_day()` — fetches from `https://icanhazdadjoke.com/`; skips if today's joke already exists; falls back to oldest stored joke if all fetched jokes are duplicates

### `apps/notifications`
- **Models:** `NotificationPreference` (user + platform + time_of_day), `NotificationLog`
- Currently only supports email as a platform

### `apps/frontend`
- Single view (`newspaper_frontpage`) — shows articles from the last 48 hours grouped by source; falls back to the 50 most recent if none found in that window

---

## Running the project

### Docker (recommended)
```bash
docker compose up --build
```
Four services start: `web` (port 8000), `worker`, `beat`, `valkey`.

### Local
```bash
pip install -r requirements.txt
playwright install chromium
python manage.py migrate
python manage.py runserver
# separate terminals:
celery -A blackcoffee worker -l info
celery -A blackcoffee beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Create admin user
```bash
# Docker
docker compose exec web python manage.py createsuperuser
# Local
python manage.py createsuperuser
```

### Seed dev data
```bash
python seed_test_data.py
```

---

## Running tests
```bash
python manage.py test
```
Tests live in `apps/<app>/tests.py`. Each app has its own test class.

---

## Triggering tasks manually

Always use `manage.py shell` or the Celery CLI — never bare `python -c` (Django won't be configured):

```bash
# Trigger news scrape for all sources
docker compose exec worker python manage.py shell -c \
  "from apps.news.tasks import catchup_scrapers; catchup_scrapers.delay()"

# Trigger dad joke fetch
docker compose exec worker python manage.py shell -c \
  "from apps.dadjokes.tasks import fetch_joke_of_the_day; fetch_joke_of_the_day.delay()"

# Or via Celery CLI
docker compose exec worker celery -A blackcoffee call news.tasks.catchup_scrapers
docker compose exec worker celery -A blackcoffee call dadjokes.tasks.fetch_joke_of_the_day
```

Tasks can also be triggered from the Django admin under **Periodic Tasks → Run now**.

---

## Future features

Planned features are tracked in [FUTURE_FEATURES.md](FUTURE_FEATURES.md).

**When implementing a planned feature:** remove its entry from `FUTURE_FEATURES.md` as part of the same change. If you add a new planned feature during your work, add it there too.

---

## Key conventions

- All Django apps live under `apps/` and are referenced as `apps.<name>` in `INSTALLED_APPS` and task paths (e.g. `apps.news.tasks.catchup_scrapers`).
- SQLite is used in development; `db.sqlite3` is at the repo root.
- `DEFAULT_AUTO_FIELD` is not set globally — models produce `W042` warnings. This is known and non-breaking.
- `entrypoint.sh` is idempotent: it uses `get_or_create` for the Beat periodic task so re-running the container is safe.
- Migrations must be created manually with `manage.py makemigrations` after any model change — they are not auto-generated on startup.
- `SECRET_KEY` defaults to an insecure dev key; set the `SECRET_KEY` environment variable in production.
- `DEBUG = True` is hardcoded — not suitable for production as-is.
