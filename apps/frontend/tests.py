from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import datetime

from apps.dadjokes.models import Joke

class PreviousJokesViewTests(TestCase):
    def setUp(self):
        # Create multiple users as requested
        self.mike = User.objects.create_user(username='Mike', password='password123')
        self.tom = User.objects.create_user(username='Tom', password='password123')
        self.ben = User.objects.create_user(username='Ben', password='password123')

        self.url = reverse('previous_jokes')

    def test_previous_jokes_login_required(self):
        """Unauthenticated users should be redirected to the login page."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_previous_jokes_list_content(self):
        """Verify that today's joke is excluded and jokes are ordered correctly."""
        self.client.login(username='Mike', password='password123')

        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        two_days_ago = today - datetime.timedelta(days=2)

        # Today's joke (should be excluded)
        Joke.objects.create(api_id='today', content='Today joke', date_used=today)

        # Past jokes
        joke1 = Joke.objects.create(api_id='joke1', content='Joke 1', date_used=yesterday)
        joke2 = Joke.objects.create(api_id='joke2', content='Joke 2', date_used=two_days_ago)

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        jokes_in_context = response.context['page_obj'].object_list
        self.assertEqual(len(jokes_in_context), 2)
        self.assertEqual(jokes_in_context[0], joke1)
        self.assertEqual(jokes_in_context[1], joke2)
        self.assertNotIn('Today joke', response.content.decode())

    def test_previous_jokes_pagination(self):
        """Verify that per_page and page parameters work as expected."""
        self.client.login(username='Tom', password='password123')

        today = timezone.now().date()
        # Create 25 past jokes
        for i in range(25):
            Joke.objects.create(
                api_id=f'joke_{i}',
                content=f'Joke content {i}',
                date_used=today - datetime.timedelta(days=i+1)
            )

        # Default per_page=10
        response = self.client.get(self.url)
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['per_page'], 10)

        # per_page=20
        response = self.client.get(self.url, {'per_page': 20})
        self.assertEqual(len(response.context['page_obj']), 20)
        self.assertEqual(response.context['per_page'], 20)

        # per_page=50
        response = self.client.get(self.url, {'per_page': 50})
        self.assertEqual(len(response.context['page_obj']), 25)
        self.assertEqual(response.context['per_page'], 50)

        # Invalid per_page defaults to 10
        response = self.client.get(self.url, {'per_page': 30})
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['per_page'], 10)

        # Page 2
        response = self.client.get(self.url, {'page': 2, 'per_page': 10})
        self.assertEqual(len(response.context['page_obj']), 10)
        self.assertEqual(response.context['page_obj'].number, 2)

    def test_previous_jokes_multiple_users(self):
        """All users should be able to access the view."""
        for user in [self.mike, self.tom, self.ben]:
            self.client.login(username=user.username, password='password123')
            response = self.client.get(self.url)
            self.assertEqual(response.status_code, 200)
            self.client.logout()
