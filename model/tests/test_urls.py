from django.test import SimpleTestCase
from django.urls import resolve, reverse
from model.views import IndexView, LoginView, RegistrationView, LogoutView, UploadView, DownloadCSVView,\
    ModelListCreateView, ModelView, ModelCreateView, DemoModelCreateView, StatisticsView


class TestUrls(SimpleTestCase):
    def test_index_urls_is_resolved(self):
        url = reverse('index')
        self.assertEqual(resolve(url).func.view_class, IndexView)

    def test_login_urls_is_resolved(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, LoginView)

    def test_registration_urls_is_resolved(self):
        url = reverse('registration')
        self.assertEqual(resolve(url).func.view_class, RegistrationView)

    def test_logout_urls_is_resolved(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class, LogoutView)

    def test_upload_urls_is_resolved(self):
        url = reverse('upload')
        self.assertEqual(resolve(url).func.view_class, UploadView)

    def test_download_urls_is_resolved(self):
        url = reverse('download')
        self.assertEqual(resolve(url).func.view_class, DownloadCSVView)

    def test_models_list_urls_is_resolved(self):
        url = reverse('models')
        self.assertEqual(resolve(url).func.view_class, ModelListCreateView)

    def test_model_detail_urls_is_resolved(self):
        url = reverse('models_id', args=[3])
        self.assertEqual(resolve(url).func.view_class, ModelView)

    def test_model_create_urls_is_resolved(self):
        url = reverse('create_model')
        self.assertEqual(resolve(url).func.view_class, ModelCreateView)

    def test_demo_create_urls_is_resolved(self):
        url = reverse('demo_create')
        self.assertEqual(resolve(url).func.view_class, DemoModelCreateView)

    def test_statistics_urls_is_resolved(self):
        url = reverse('statistics')
        self.assertEqual(resolve(url).func.view_class, StatisticsView)