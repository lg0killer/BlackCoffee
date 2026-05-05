from celery import shared_task
from .models import Source, Category, Article, ScrapeState
from .utils import detect_rss_feed, translate_text
import feedparser
from playwright.sync_api import sync_playwright
import datetime
from django.utils import timezone

@shared_task
def test_scrape_task(source_id):
    """
    Background task to test/detect scrape type for a newly added source.
    """
    try:
        source = Source.objects.get(id=source_id)
        if source.scrape_type == 'auto':
            feed_url = detect_rss_feed(source.url)
            if feed_url:
                source.scrape_type = 'rss'
                # Optionally save the actual feed url if we want, but for now we keep the base
                # and logic handles it. Let's update URL if it's vastly different or we can assume it.
                source.url = feed_url
                source.save()
            else:
                source.scrape_type = 'web'
                source.save()
    except Exception as e:
        print(f"Error in test_scrape_task: {e}")

@shared_task
def run_rss_scraper(source_id):
    source = Source.objects.get(id=source_id)
    feed = feedparser.parse(source.url)

    state, created = ScrapeState.objects.get_or_create(source=source)
    state.last_run = timezone.now()

    try:
        articles_created = 0
        for entry in feed.entries:
            link = entry.link
            if Article.objects.filter(link=link).exists():
                continue

            headline = entry.get('title', 'No Title')
            summary = entry.get('summary', '')

            # Apply Translation if needed
            if source.should_translate and source.source_language:
                headline = translate_text(headline, source.source_language, source.target_language)
                summary = translate_text(summary, source.source_language, source.target_language)

            # Publish date parsing
            pub_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                pub_date = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)

            Article.objects.create(
                source=source,
                headline=headline,
                summary=summary,
                link=link,
                publish_date=pub_date
            )
            articles_created += 1

        state.last_status = f"Success. Added {articles_created} articles."
        state.last_error = ""
    except Exception as e:
        state.last_status = "Error"
        state.last_error = str(e)

    state.save()

@shared_task
def run_web_scraper(source_id):
    source = Source.objects.get(id=source_id)
    state, created = ScrapeState.objects.get_or_create(source=source)
    state.last_run = timezone.now()

    try:
        articles_created = 0
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            # Simple heuristic Web Scrape
            page.goto(source.url, timeout=60000)

            if source.requires_login and source.username and source.password:
                # Naive login attempt (fill first username/password fields)
                page.fill('input[type="text"], input[name="username"], input[name="email"]', source.username)
                page.fill('input[type="password"]', source.password)
                page.click('button[type="submit"], input[type="submit"]')
                page.wait_for_timeout(3000) # Wait for navigation

            # Attempt to discover and save Category links
            nav_links = page.locator('nav a, header a').all()
            for nav in nav_links[:10]: # Look at first 10 nav links for categories
                nav_text = nav.inner_text().strip()
                try:
                    nav_href = nav.get_attribute('href')
                    if nav_text and len(nav_text) < 20 and nav_href:
                        Category.objects.get_or_create(name=nav_text)
                except:
                    pass

            # Extract links and headings roughly
            items = page.locator('article, .article, .post, h2, h3').all()
            for item in items[:20]: # Limit to 20 for generic scrape
                text = item.inner_text().strip()
                if not text:
                    continue

                # Try to find a link nearby
                link_loc = item.locator('a').first
                link = source.url
                try:
                    if link_loc.count() > 0:
                        href = link_loc.get_attribute('href')
                        if href:
                            if href.startswith('/'):
                                from urllib.parse import urljoin
                                link = urljoin(source.url, href)
                            else:
                                link = href
                except:
                    pass

                # Check exists
                if Article.objects.filter(headline=text).exists() or Article.objects.filter(link=link).exists():
                    continue

                headline = text
                summary = "Automatically scraped from web source."

                # Translate
                if source.should_translate and source.source_language:
                    headline = translate_text(headline, source.source_language, source.target_language)
                    summary = translate_text(summary, source.source_language, source.target_language)

                Article.objects.create(
                    source=source,
                    headline=headline,
                    summary=summary,
                    link=link,
                    publish_date=timezone.now()
                )
                articles_created += 1

            browser.close()

        state.last_status = f"Success. Added {articles_created} articles."
        state.last_error = ""
    except Exception as e:
        state.last_status = "Error"
        state.last_error = str(e)

    state.save()

@shared_task
def run_all_scrapers():
    """
    Main entrypoint for daily scheduled scrapers.
    """
    for source in Source.objects.all():
        if source.scrape_type == 'rss':
            run_rss_scraper.delay(source.id)
        elif source.scrape_type == 'web':
            run_web_scraper.delay(source.id)
        elif source.scrape_type == 'auto':
            # Run detect first, then it will set it to RSS or Web.
            test_scrape_task.delay(source.id)

@shared_task
def catchup_scrapers():
    """
    Runs frequently (e.g., every 15 mins). Checks if the main daily run
    should have happened but the laptop was off/sleeping.

    Logic: We want to run scrapers at 03:00 and 05:00 UTC.
    If the current time is past those times, but the last run was before those times today,
    we trigger a catchup run.
    """
    now = timezone.now()
    today = now.date()

    target_times = [
        datetime.time(3, 0),
        datetime.time(5, 0)
    ]

    # Check the latest scrape state generally. If no state exists, run it.
    latest_state = ScrapeState.objects.order_by('-last_run').first()
    last_run_time = latest_state.last_run if latest_state and latest_state.last_run else None

    should_run = False

    if not last_run_time:
        should_run = True
    else:
        for t in target_times:
            target_dt = timezone.make_aware(datetime.datetime.combine(today, t))
            # If we are currently PAST the target time, BUT the last run was BEFORE the target time.
            if now >= target_dt and last_run_time < target_dt:
                should_run = True
                break

    if should_run:
        print(f"Catch-up logic triggered at {now}")
        run_all_scrapers.delay()
