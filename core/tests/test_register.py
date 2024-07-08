# test_register.py
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..forms.profile import ProfileForm
from ..forms.registration import UserRegistrationForm
from ..models import Profile, Tutor
import json

User = get_user_model()


class RegisterViewTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('core:register')

    def test_get_register_view(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/register.html')
        self.assertIsInstance(response.context['form'], UserRegistrationForm)
        self.assertIsInstance(response.context['profile_form'], ProfileForm)

    def test_post_valid_registration(self):
        # Simulate a profile picture upload
        profile_pic = ''  # Update this as per actual implementation for handling file upload simulation
        post_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',  # Ensure password meets complexity requirements
            'password2': 'ComplexPassword!123',
            'is_tutor': 'on',
            'propic': profile_pic
        }

        response = self.client.post(self.url, post_data, follow=True)
        self.assertRedirects(response, reverse('core:profile'))
        self.assertTrue(User.objects.filter(username='testuser').exists())
        user = User.objects.get(username='testuser')
        self.assertTrue(Profile.objects.filter(user=user).exists())
        self.assertTrue(Tutor.objects.filter(user=user).exists())

    def test_post_invalid_registration(self):
        post_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',
            'password2': 'ComplexPassword!456',  # Mismatched passwords
        }

        response = self.client.post(self.url, post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'The two password fields didn’t match.')
        self.assertFalse(User.objects.filter(username='testuser').exists())

    def test_ajax_post_valid_registration(self):
        profile_pic = ''  # Update this as per actual implementation for handling file upload simulation
        post_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',  # Ensure password meets complexity requirements
            'password2': 'ComplexPassword!123',
            'is_tutor': 'on',
            'propic': profile_pic
        }

        response = self.client.post(self.url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        self.assertTrue(User.objects.filter(username='testuser').exists())

    def test_ajax_post_invalid_registration(self):
        post_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',
            'password2': 'ComplexPassword!456',  # Mismatched passwords
        }

        response = self.client.post(self.url, post_data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        response_data = json.loads(response.content)
        self.assertFalse(response_data['success'])
        self.assertIn('password2', response_data['errors'])
        self.assertFalse(User.objects.filter(username='testuser').exists())
