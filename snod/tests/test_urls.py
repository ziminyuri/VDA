from django.test import SimpleTestCase
from django.urls import resolve, reverse

from snod.views import (OriginalSnodDetailView, OriginalSnodSearchView,
                        SettingsOriginalSnodCreateView, SnodDetailView,
                        SnodSearchView)


class TestUrls(SimpleTestCase):
    def test_snod_search_urls_is_resolved(self):
        url = reverse('snod_search', args=[1])
        self.assertEqual(resolve(url).func.view_class, SnodSearchView)

    def test_snod_detail_urls_is_resolved(self):
        url = reverse('snod_result', args=[1])
        self.assertEqual(resolve(url).func.view_class, SnodDetailView)

    def test_original_snod_search_urls_is_resolved(self):
        url = reverse('snod_original_search', args=[1])
        self.assertEqual(resolve(url).func.view_class, OriginalSnodSearchView)

    def test_original_snod_detail_urls_is_resolved(self):
        url = reverse('snod_original_result', args=[1])
        self.assertEqual(resolve(url).func.view_class, OriginalSnodDetailView)

    def test_snod_original_settings_create_urls_is_resolved(self):
        url = reverse('snod_original_settings_create', args=[1])
        self.assertEqual(resolve(url).func.view_class, SettingsOriginalSnodCreateView)