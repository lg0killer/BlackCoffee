from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from unittest.mock import patch

class AdminForceSyncTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_superuser('admin', 'admin@example.com', 'password')
        self.client.login(username='admin', password='password')

    def test_force_sync_button_exists_on_admin_index(self):
        # Check if button appears on admin index
        response = self.client.get(reverse('admin:index'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Force Sync All', response.content)

    @patch('apps.news.tasks.catchup_scrapers.delay')
    def test_force_sync_triggers_task_and_redirects(self, mock_delay):
        # Trigger force sync
        response = self.client.get(reverse('force_sync_all'))
        self.assertRedirects(response, reverse('admin:index'))
        mock_delay.assert_called_once()
