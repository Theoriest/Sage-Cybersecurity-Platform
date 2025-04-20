from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import SOCUser, NonSOCUser

User = get_user_model()

class UserTests(TestCase):
    def setUp(self):
        # Create an admin user
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            password='adminpassword',
            user_type='soc',
            is_admin=True
        )
        # Create a Non-SOC user
        self.non_soc_user = User.objects.create_user(
            username='non_soc_user',
            email='non_soc@example.com',
            first_name='Non',
            last_name='SOC',
            password='non_soc_password',
            user_type='non_soc'
        )
        NonSOCUser.objects.create(user=self.non_soc_user, department='IT')

        # Create a SOC user
        self.soc_user = User.objects.create_user(
            username='soc_user',
            email='soc@example.com',
            first_name='SOC',
            last_name='User',
            password='soc_password',
            user_type='soc'
        )
        SOCUser.objects.create(user=self.soc_user, unique_identifier='SOC123', role='analyst')

    # Test Non-SOC user signup
    def test_non_soc_user_signup(self):
        response = self.client.post(reverse('non_soc_user_signup'), {
            'username': 'new_non_soc_user',
            'email': 'new_non_soc@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'newpassword123',
            'department': 'HR',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertTrue(User.objects.filter(username='new_non_soc_user').exists())

    # Test Non-SOC user login
    def test_non_soc_user_login(self):
        response = self.client.post(reverse('non_soc_user_login'), {
            'username_or_email': 'non_soc_user',
            'password': 'non_soc_password',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, reverse('non_soc_dashboard'))

    # Test SOC user login
    def test_soc_user_login(self):
        response = self.client.post(reverse('soc_user_login'), {
            'username_or_email': 'soc_user',
            'password': 'soc_password',
            'unique_identifier': 'SOC123',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        self.assertRedirects(response, reverse('soc_dashboard'))

    # Test invalid SOC user login
    def test_invalid_soc_user_login(self):
        response = self.client.post(reverse('soc_user_login'), {
            'username_or_email': 'soc_user',
            'password': 'wrong_password',
            'unique_identifier': 'SOC123',
        })
        self.assertEqual(response.status_code, 401)  # Unauthorized

    # Test SOC user creation by admin
    def test_soc_user_creation_by_admin(self):
        self.client.login(username='admin', password='adminpassword')
        response = self.client.post(reverse('soc_user_signup'), {
            'username': 'new_soc_user',
            'email': 'new_soc@example.com',
            'first_name': 'New',
            'last_name': 'SOC',
            'password': 'newpassword123',
            'unique_identifier': 'SOC456',
            'role': 'engineer',
        })
        self.assertEqual(response.status_code, 302)  # Redirect after creation
        self.assertTrue(User.objects.filter(username='new_soc_user').exists())
        self.assertTrue(SOCUser.objects.filter(unique_identifier='SOC456').exists())

    # Test Non-SOC user signup form validation
    def test_non_soc_user_signup_form_invalid(self):
        response = self.client.post(reverse('non_soc_user_signup'), {
            'username': '',  # Missing username
            'email': 'invalid_email',
            'first_name': 'New',
            'last_name': 'User',
            'password': 'short',
            'department': 'HR',
        })
        self.assertEqual(response.status_code, 200)  # Form re-rendered with errors
        self.assertContains(response, 'This field is required.')  # Example error message

    # Test SOC user signup restricted to admin
    def test_soc_user_signup_restricted(self):
        self.client.login(username='non_soc_user', password='non_soc_password')
        response = self.client.get(reverse('soc_user_signup'))
        self.assertEqual(response.status_code, 403)  # Forbidden for non-admin users