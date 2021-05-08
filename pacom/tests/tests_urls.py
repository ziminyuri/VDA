from django.test import SimpleTestCase
from django.urls import resolve, reverse
from pacom.views import ParkDetailView, ParkSearchView, SettingsPACOMCreateView


class TestUrls(SimpleTestCase):
    def test_pacom_search_urls_is_resolved(self):
        url = reverse('park_search', args=[1])
        self.assertEqual(resolve(url).func.view_class, ParkSearchView)

    def test_pacom_detail_urls_is_resolved(self):
        url = reverse('park_result', args=[1])
        self.assertEqual(resolve(url).func.view_class, ParkDetailView)

    def test_settings_pacom_urls_is_resolved(self):
        url = reverse('pacom_settings_create', args=[1])
        self.assertEqual(resolve(url).func.view_class, SettingsPACOMCreateView)