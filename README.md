# BlackCoffee
A self-hosted news aggregator that scrapes, translates, and displays articles from multiple sources on a single newspaper-style frontpage — your morning briefing, your way.

## What it does

BlackCoffee collects articles from news sources you configure and presents them on a clean frontpage grouped by source. It supports:

- **RSS feeds** — auto-detected or manually specified
- **Web scraping** — using Playwright for sites without feeds, with optional login support
- **Auto-detection** — point it at a site URL and it figures out whether to use RSS or scrape
- **Translation** — per-source translation using either local offline [Argos Translate](https://github.com/argosopentech/argos-translate) or [Deep Translator](https://github.com/nidhaloff/deep-translator) (Google) as a backup
- **Background scheduling** — Celery workers run scrapers on a 15-minute interval via Celery Beat

Sources and scrape behaviour are managed through the Django admin interface.

## Getting started

### With Docker (recommended)

```bash
docker compose up --build
```

This starts four services:
| Service | Role |
|---------|------|
| `web` | Django app on port 8000 |
| `worker` | Celery worker that runs scrape tasks |
| `beat` | Celery Beat scheduler (runs scrapers every 15 min) |
| `valkey` | Redis-compatible broker (Valkey 7.2) |

On first start, `entrypoint.sh` runs migrations and registers the periodic scrape schedule automatically.

Open [http://localhost:8000](http://localhost:8000) for the frontpage and [http://localhost:8000/admin](http://localhost:8000/admin) to manage sources.

### Without Docker

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Apply migrations and start the dev server:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

3. In separate terminals, start the Celery worker and scheduler:
   ```bash
   celery -A blackcoffee worker -l info
   celery -A blackcoffee beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
   ```

### Creating an admin user

To access the Django admin at [http://localhost:8000/admin](http://localhost:8000/admin), create a superuser first:

```bash
# Without Docker
python manage.py createsuperuser

# With Docker
docker compose exec web python manage.py createsuperuser
```

You will be prompted to set a username, email, and password.

### Seed test data

To populate the database with articles from BleepingComputer right away:

```bash
python seed_test_data.py
```

## Testing

Run the test suite with:

```bash
python manage.py test
```

Tests cover model creation and validation for `Source`, `Article`, `Category`, and `TranslationSetting`.
## Security Notice: deep-translator
The `deep-translator` dependency is locked to a version strictly less than `1.11.0` (e.g., `deep-translator<1.11.0`) due to a malicious takeover in version `1.11.4` (PYSEC-2022-252) that runs malware during installation. DO NOT upgrade to or past `1.11.4`.
