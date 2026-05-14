
class MockEntry:
    def __init__(self, link, title, summary, published_parsed=None):
        self.link = link
        self.title = title
        self.summary = summary
        self.published_parsed = published_parsed
    def get(self, key, default=None):
        return getattr(self, key, default)

from django.test import TestCase, Client
from apps.news.models import Source, Category, Article, TranslationSetting
from django.utils import timezone
from unittest.mock import patch, MagicMock
from apps.news.tasks import run_rss_scraper
from django.contrib.auth.models import User
from django.urls import reverse

class NewsModelsTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Tech")
        self.source = Source.objects.create(
            name="Test Source",
            url="http://example.com/rss",
            scrape_type="rss",
            should_translate=True,
            source_language="sv",
            target_language="en"
        )
        self.article = Article.objects.create(
            source=self.source,
            category=self.category,
            headline="Test Headline",
            summary="Test Summary",
            link="http://example.com/article1",
            publish_date=timezone.now()
        )
        self.setting = TranslationSetting.objects.get_or_create(engine="argos", is_active=True)[0]

    def test_source_creation(self):
        self.assertEqual(self.source.name, "Test Source")
        self.assertEqual(self.source.scrape_type, "rss")

    def test_article_creation(self):
        self.assertEqual(self.article.headline, "Test Headline")
        self.assertEqual(self.article.source, self.source)

    def test_translation_setting(self):
        self.assertEqual(self.setting.engine, "argos")

class NewsTasksTest(TestCase):
    def setUp(self):
        self.source = Source.objects.create(
            name="RSS Source",
            url="http://example.com/rss",
            scrape_type="rss"
        )

    @patch('apps.news.tasks.feedparser.parse')
    def test_run_rss_scraper_optimization(self, mock_parse):
        # Create an existing article
        Article.objects.create(
            source=self.source,
            headline="Existing Article",
            link="http://example.com/existing"
        )

        # Mock feed entries: one existing, one new
        mock_feed = MagicMock()
        mock_feed.entries = [
            MockEntry(link="http://example.com/existing", title="Existing Article", summary="", published_parsed=None),
            MockEntry(link="http://example.com/new", title="New Article", summary="", published_parsed=None)
        ]
        mock_feed.get.return_value = False
        mock_parse.return_value = mock_feed

        # Run the scraper
        with self.assertNumQueries(8):
             # (Note: actual count might vary based on DB/ScrapeState logic,
             # but the key is that Article check is now 1 query for all links)
            run_rss_scraper(self.source.id)

        # Verify results
        self.assertEqual(Article.objects.count(), 2)
        self.assertTrue(Article.objects.filter(link="http://example.com/new").exists())
class NewsViewsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', password='password123')

        self.source = Source.objects.create(
            user=self.user,
            name="My Source",
            url="http://mysource.com/rss",
            scrape_type="rss"
        )
        self.other_source = Source.objects.create(
            user=self.other_user,
            name="Other Source",
            url="http://othersource.com/rss",
            scrape_type="rss"
        )
        self.client = Client()

    def test_manage_sources_get_authenticated(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('manage_sources'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'news/manage_sources.html')
        self.assertIn(self.source, response.context['sources'])
        self.assertNotIn(self.other_source, response.context['sources'])

    def test_manage_sources_get_anonymous(self):
        response = self.client.get(reverse('manage_sources'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_manage_sources_post_valid(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'name': 'New Source',
            'url': 'http://newsource.com/rss',
            'scrape_type': 'rss'
        }
        response = self.client.post(reverse('manage_sources'), data)
        self.assertRedirects(response, reverse('manage_sources'))
        self.assertTrue(Source.objects.filter(name='New Source', user=self.user).exists())

    def test_manage_sources_post_invalid(self):
        self.client.login(username='testuser', password='password123')
        data = {
            'name': '',  # Invalid: name is required
            'url': 'not-a-url', # Invalid: url format
            'scrape_type': 'invalid' # Invalid choice
        }
        response = self.client.post(reverse('manage_sources'), data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Source.objects.filter(name='', user=self.user).exists())
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_delete_source_post_owner(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('delete_source', args=[self.source.pk]))
        self.assertRedirects(response, reverse('manage_sources'))
        self.assertFalse(Source.objects.filter(pk=self.source.pk).exists())

    def test_delete_source_post_non_owner(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.post(reverse('delete_source', args=[self.other_source.pk]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Source.objects.filter(pk=self.other_source.pk).exists())

    def test_delete_source_get_redirect(self):
        self.client.login(username='testuser', password='password123')
        response = self.client.get(reverse('delete_source', args=[self.source.pk]))
        self.assertRedirects(response, reverse('manage_sources'))
        self.assertTrue(Source.objects.filter(pk=self.source.pk).exists())
