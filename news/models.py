from django.db import models
from django.core.exceptions import ValidationError

class TranslationSetting(models.Model):
    TRANSLATION_ENGINES = [
        ('argos', 'Local Offline (Argos Translate)'),
        ('deep', 'External Backup (Deep Translator)'),
    ]
    engine = models.CharField(max_length=20, choices=TRANSLATION_ENGINES, default='argos')
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.pk and TranslationSetting.objects.exists():
            raise ValidationError('There can be only one TranslationSetting instance')
        return super(TranslationSetting, self).save(*args, **kwargs)

    def __str__(self):
        return f"Translation Setting ({self.get_engine_display()})"


from django.contrib.auth.models import User

class Source(models.Model):
    SCRAPE_TYPES = [
        ('auto', 'Auto-detect'),
        ('rss', 'RSS Feed'),
        ('web', 'Web Scrape (Playwright)'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_sources', null=True, blank=True, help_text="If blank, this is a global source for everyone.")
    name = models.CharField(max_length=200)
    url = models.URLField(unique=True)
    scrape_type = models.CharField(max_length=10, choices=SCRAPE_TYPES, default='auto')

    # Credentials for web scraping
    requires_login = models.BooleanField(default=False)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)

    # Translation
    should_translate = models.BooleanField(default=False)
    source_language = models.CharField(max_length=10, blank=True, null=True, help_text="e.g. 'sv' for Swedish")
    target_language = models.CharField(max_length=10, default='en', help_text="e.g. 'en' for English")

    def __str__(self):
        return self.name

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Article(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    headline = models.CharField(max_length=500)
    summary = models.TextField(blank=True, null=True)
    link = models.URLField(unique=True)
    publish_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.headline

class ScrapeState(models.Model):
    source = models.OneToOneField(Source, on_delete=models.CASCADE)
    last_run = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=50, blank=True, null=True)
    last_error = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Scrape State for {self.source.name}"
