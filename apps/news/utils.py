import logging
import requests
from bs4 import BeautifulSoup
import argostranslate.package
import argostranslate.translate
from deep_translator import GoogleTranslator
from .models import TranslationSetting

logger = logging.getLogger(__name__)

def detect_rss_feed(url):
    """
    Tries to detect if a given URL is an RSS feed or has a discoverable RSS feed.
    Returns the feed URL if found, else None.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content_type = response.headers.get('Content-Type', '')

        # Check if URL itself is an RSS/XML feed
        if 'xml' in content_type or 'rss' in content_type:
            return url

        # Parse HTML to find feed link
        soup = BeautifulSoup(response.content, 'html.parser')

        # Look for <link rel="alternate" type="application/rss+xml" ...>
        feed_links = soup.find_all('link', rel='alternate', type=['application/rss+xml', 'application/atom+xml'])
        if feed_links:
            href = feed_links[0].get('href')
            if href.startswith('/'):
                from urllib.parse import urljoin
                href = urljoin(url, href)
            return href

        # Try common paths as fallback
        common_paths = ['/feed/', '/rss/', '/feed.xml', '/rss.xml']
        for path in common_paths:
            test_url = f"{url.rstrip('/')}{path}"
            try:
                r = requests.head(test_url, timeout=5)
                if r.status_code == 200 and ('xml' in r.headers.get('Content-Type', '') or 'rss' in r.headers.get('Content-Type', '')):
                    return test_url
            except Exception:
                pass

    except Exception as e:
        logger.error(f"Error detecting RSS for {url}: {e}")

    return None

def setup_argos_translation(from_code, to_code):
    """
    Downloads and installs Argos translation model if not present locally.
    """
    installed_packages = argostranslate.package.get_installed_packages()
    if any(p.from_code == from_code and p.to_code == to_code for p in installed_packages):
        return

    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    package_to_install = next(
        filter(
            lambda x: x.from_code == from_code and x.to_code == to_code, available_packages
        ), None
    )

    if package_to_install:
        argostranslate.package.install_from_path(package_to_install.download())

def translate_text(text, source_lang, target_lang='en'):
    if not text or not source_lang:
        return text

    try:
        setting = TranslationSetting.objects.filter(is_active=True).first()
        engine = setting.engine if setting else 'argos'

        if engine == 'argos':
            # Install package if needed
            setup_argos_translation(source_lang, target_lang)
            return argostranslate.translate.translate(text, source_lang, target_lang)

        elif engine == 'deep':
            translator = GoogleTranslator(source=source_lang, target=target_lang)
            return translator.translate(text)

    except Exception as e:
        logger.error(f"Translation error: {e}")
        return text

    return text
