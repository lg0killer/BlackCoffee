from django.test import TestCase
from .models import Source, Category, Article, TranslationSetting
from django.utils import timezone

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
        self.setting = TranslationSetting.objects.create(engine="argos", is_active=True)

    def test_source_creation(self):
        self.assertEqual(self.source.name, "Test Source")
        self.assertEqual(self.source.scrape_type, "rss")

    def test_article_creation(self):
        self.assertEqual(self.article.headline, "Test Headline")
        self.assertEqual(self.article.source, self.source)

    def test_translation_setting(self):
        self.assertEqual(self.setting.engine, "argos")
