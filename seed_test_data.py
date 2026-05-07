import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blackcoffee.settings')
django.setup()

from apps.news.models import Source, Category
from apps.news.tasks import run_rss_scraper
from apps.news.utils import detect_rss_feed

def main():
    print("Setting up test data for BleepingComputer...")

    # Create or get category
    tech_cat, _ = Category.objects.get_or_create(name="Cybersecurity")

    url = "https://www.bleepingcomputer.com"
    feed_url = detect_rss_feed(url) or "https://www.bleepingcomputer.com/feed/"

    source, created = Source.objects.get_or_create(
        name="Bleeping Computer",
        defaults={
            'url': feed_url,
            'scrape_type': 'rss',
            'should_translate': False
        }
    )

    if not created and source.url != feed_url:
        source.url = feed_url
        source.scrape_type = 'rss'
        source.save()

    print(f"Running RSS scraper for {source.name}...")
    run_rss_scraper(source.id)

    from apps.news.models import Article
    count = Article.objects.filter(source=source).count()
    print(f"Success! Database now has {count} articles from {source.name}.")

if __name__ == '__main__':
    main()
