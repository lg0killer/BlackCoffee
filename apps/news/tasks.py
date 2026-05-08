import logging
import traceback
from celery import shared_task
from .models import Source, Category, Article, ScrapeState
from .utils import detect_rss_feed, translate_text
import feedparser
from playwright.sync_api import sync_playwright
import datetime
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def test_scrape_task(source_id):
    """
    Background task to detect scrape type for a source and then run the appropriate scraper.
    """
    try:
        source = Source.objects.get(id=source_id)
        logger.info("[test_scrape] Starting for source '%s' (id=%s, current type=%s)", source.name, source_id, source.scrape_type)
        if source.scrape_type == 'auto':
            feed_url = detect_rss_feed(source.url)
            if feed_url:
                source.scrape_type = 'rss'
                source.url = feed_url
                source.save()
                logger.info("[test_scrape] Detected RSS feed for '%s': %s", source.name, feed_url)
            else:
                source.scrape_type = 'web'
                source.save()
                logger.info("[test_scrape] No RSS feed found for '%s', using web scraper", source.name)
        # Now run the appropriate scraper
        if source.scrape_type == 'rss':
            logger.info("[test_scrape] Dispatching run_rss_scraper for '%s'", source.name)
            run_rss_scraper.delay(source_id)
        elif source.scrape_type == 'web':
            logger.info("[test_scrape] Dispatching run_web_scraper for '%s'", source.name)
            run_web_scraper.delay(source_id)
    except Exception as e:
        logger.error("[test_scrape] Error for source_id=%s: %s\n%s", source_id, e, traceback.format_exc())


@shared_task
def run_rss_scraper(source_id):
    source = Source.objects.get(id=source_id)
    logger.info("[rss] Starting scrape for '%s' (%s)", source.name, source.url)

    feed = feedparser.parse(source.url)
    logger.info("[rss] Feed fetched for '%s': %d entries, bozo=%s", source.name, len(feed.entries), feed.get('bozo'))
    if feed.get('bozo'):
        logger.warning("[rss] Feed parse warning for '%s': %s", source.name, feed.get('bozo_exception'))

    state, created = ScrapeState.objects.get_or_create(source=source)
    state.last_run = timezone.now()

    try:
        articles_created = 0
        skipped = 0
        for entry in feed.entries:
            link = entry.link
            if Article.objects.filter(link=link).exists():
                skipped += 1
                continue

            headline = entry.get('title', 'No Title')
            summary = entry.get('summary', '')

            # Apply Translation if needed
            if source.should_translate and source.source_language:
                logger.debug("[rss] Translating article '%s'", headline[:60])
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
            logger.debug("[rss] Created article: %s", headline[:80])

        logger.info("[rss] Done for '%s': %d created, %d skipped (already exist)", source.name, articles_created, skipped)
        state.last_status = f"Success. Added {articles_created} articles."
        state.last_error = ""
    except Exception as e:
        logger.error("[rss] Error scraping '%s': %s\n%s", source.name, e, traceback.format_exc())
        state.last_status = "Error"
        state.last_error = str(e)

    state.save()
    return state.last_status


@shared_task
def run_web_scraper(source_id):
    source = Source.objects.get(id=source_id)
    logger.info("[web] Starting scrape for '%s' (%s)", source.name, source.url)

    state, created = ScrapeState.objects.get_or_create(source=source)
    state.last_run = timezone.now()

    try:
        articles_created = 0
        scraped_items = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            logger.info("[web] Navigating to %s", source.url)
            page.goto(source.url, timeout=60000)

            if source.requires_login and source.username and source.password:
                logger.info("[web] Attempting login for '%s'", source.name)
                page.fill('input[type="text"], input[name="username"], input[name="email"]', source.username)
                page.fill('input[type="password"]', source.password)
                page.click('button[type="submit"], input[type="submit"]')
                page.wait_for_timeout(3000)
                logger.info("[web] Login submitted for '%s'", source.name)

            # Collect category nav links
            nav_links = page.locator('nav a, header a').all()
            logger.debug("[web] Found %d nav links for '%s'", len(nav_links), source.name)
            category_names = []
            for nav in nav_links[:10]:
                nav_text = nav.inner_text().strip()
                try:
                    nav_href = nav.get_attribute('href')
                    if nav_text and len(nav_text) < 20 and nav_href:
                        category_names.append(nav_text)
                except:
                    pass

            # Collect article data without touching the DB
            items = page.locator('article, .article, .post, h2, h3').all()
            logger.info("[web] Found %d candidate items for '%s'", len(items), source.name)
            for item in items[:20]:
                text = item.inner_text().strip()
                if not text:
                    continue
                link = source.url
                try:
                    link_loc = item.locator('a').first
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
                scraped_items.append({'headline': text, 'link': link})

            browser.close()

        # All DB work happens after Playwright has fully exited
        for name in category_names:
            Category.objects.get_or_create(name=name)

        skipped = 0
        for item in scraped_items:
            text = item['headline']
            link = item['link']

            if Article.objects.filter(headline=text).exists() or Article.objects.filter(link=link).exists():
                skipped += 1
                continue

            headline = text
            summary = "Automatically scraped from web source."

            if source.should_translate and source.source_language:
                logger.debug("[web] Translating article '%s'", headline[:60])
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
            logger.debug("[web] Created article: %s", headline[:80])

        logger.info("[web] Done for '%s': %d created, %d skipped", source.name, articles_created, skipped)
        state.last_status = f"Success. Added {articles_created} articles."
        state.last_error = ""
    except Exception as e:
        logger.error("[web] Error scraping '%s': %s\n%s", source.name, e, traceback.format_exc())
        state.last_status = "Error"
        state.last_error = str(e)

    state.save()
    return state.last_status


@shared_task
def run_all_scrapers():
    """
    Main entrypoint for daily scheduled scrapers.
    """
    sources = list(Source.objects.all())
    logger.info("[run_all] Dispatching scrapers for %d sources", len(sources))
    for source in sources:
        if source.scrape_type == 'rss':
            run_rss_scraper.delay(source.id)
        elif source.scrape_type == 'web':
            run_web_scraper.delay(source.id)
        elif source.scrape_type == 'auto':
            test_scrape_task.delay(source.id)
        logger.info("[run_all] Queued scrape for '%s' (type=%s)", source.name, source.scrape_type)


@shared_task
def catchup_scrapers():
    """
    Runs every 15 minutes. Triggers scraper if no run has occurred in the last 15 minutes.
    """
    now = timezone.now()
    cutoff = now - datetime.timedelta(minutes=15)

    latest_state = ScrapeState.objects.order_by('-last_run').first()
    last_run_time = latest_state.last_run if latest_state and latest_state.last_run else None

    if not last_run_time or last_run_time < cutoff:
        logger.info("[catchup] Triggering run_all_scrapers at %s (last run: %s)", now, last_run_time)
        run_all_scrapers.delay()
    else:
        logger.debug("[catchup] Skipping — last run was %s, cutoff is %s", last_run_time, cutoff)
