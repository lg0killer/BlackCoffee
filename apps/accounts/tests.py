from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import UserProfile

class ProfileViewTest(TestCase):
    def setUp(self):
        self.username = 'testuser'
        self.password = 'password123'
        self.user = User.objects.create_user(username=self.username, password=self.password)
        # UserProfile is created automatically via signal

    def test_profile_view_get_authenticated(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)

    def test_profile_view_get_anonymous(self):
        response = self.client.get(reverse('profile'))
        login_url = reverse('login')
        expected_url = f"{login_url}?next={reverse('profile')}"
        self.assertRedirects(response, expected_url)

    def test_profile_view_post_valid(self):
        self.client.login(username=self.username, password=self.password)
        data = {
            'first_name': 'New',
            'last_name': 'Name',
            'email': 'new@example.com',
            'timezone': 'Europe/Stockholm'
        }
        response = self.client.post(reverse('profile'), data)
        self.assertRedirects(response, reverse('profile'))

        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'New')
        self.assertEqual(self.user.last_name, 'Name')
        self.assertEqual(self.user.email, 'new@example.com')
        self.assertEqual(self.user.userprofile.timezone, 'Europe/Stockholm')

    def test_profile_view_post_invalid(self):
        self.client.login(username=self.username, password=self.password)
        data = {
            'first_name': 'New',
            'last_name': 'Name',
            'email': 'not-an-email',
            'timezone': 'Invalid/Timezone'
        }
        response = self.client.post(reverse('profile'), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('user_form', response.context)
        self.assertIn('profile_form', response.context)
        self.assertTrue(response.context['user_form'].errors or response.context['profile_form'].errors)
