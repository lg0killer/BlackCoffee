from django.contrib import admin
from django.urls import path
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib import messages
from .models import Source, Category, Article, ScrapeState, TranslationSetting

@admin.register(TranslationSetting)
class TranslationSettingAdmin(admin.ModelAdmin):
    list_display = ('engine', 'is_active')

    def has_add_permission(self, request):
        if self.model.objects.count() >= 1:
            return False
        return super().has_add_permission(request)

@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'scrape_type', 'requires_login', 'should_translate')
    list_filter = ('scrape_type', 'requires_login', 'should_translate')
    search_fields = ('name', 'url')

    change_form_template = "admin/news/source/change_form.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:source_id>/test_scrape/', self.admin_site.admin_view(self.test_scrape), name='news_source_test_scrape'),
        ]
        return custom_urls + urls

    def test_scrape(self, request, source_id):
        source = self.get_object(request, source_id)

        if request.method == 'POST' and 'confirm' in request.POST:
            confirmed_type = request.POST.get('confirmed_scrape_type')
            source.scrape_type = confirmed_type
            source.save()
            messages.success(request, f"Scrape type for {source.name} confirmed as {confirmed_type}.")
            return HttpResponseRedirect(f"../../{source.pk}/change/")

        # Perform synchronous test scrape for preview
        from .utils import detect_rss_feed
        import feedparser
        from playwright.sync_api import sync_playwright

        scrape_type = source.scrape_type
        if scrape_type == 'auto':
            feed_url = detect_rss_feed(source.url)
            if feed_url:
                scrape_type = 'rss'
                source.url = feed_url # Temporarily update for test
            else:
                scrape_type = 'web'

        preview_articles = []
        try:
            if scrape_type == 'rss':
                feed = feedparser.parse(source.url)
                for entry in feed.entries[:5]: # preview up to 5
                    preview_articles.append({
                        'headline': entry.get('title', 'No Title'),
                        'summary': entry.get('summary', ''),
                        'link': entry.link
                    })
            elif scrape_type == 'web':
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    page = browser.new_page()
                    page.goto(source.url, timeout=30000)
                    items = page.locator('article, .article, .post, h2, h3').all()
                    for item in items[:5]:
                        text = item.inner_text().strip()
                        if text:
                            preview_articles.append({
                                'headline': text,
                                'summary': "Web Scrape Preview",
                                'link': source.url
                            })
                    browser.close()
        except Exception as e:
            messages.error(request, f"Error during test scrape: {e}")

        return render(request, 'admin/news/source/preview.html', {
            'source': source,
            'scrape_type': scrape_type,
            'articles': preview_articles
        })

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('headline', 'source', 'category', 'publish_date')
    list_filter = ('source', 'category', 'publish_date')
    search_fields = ('headline', 'summary')

@admin.register(ScrapeState)
class ScrapeStateAdmin(admin.ModelAdmin):
    list_display = ('source', 'last_run', 'last_status')
