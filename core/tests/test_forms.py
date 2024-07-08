# test_forms.py

from django.test import TestCase
from django.contrib.auth import get_user_model
from ..forms.registration import UserRegistrationForm

User = get_user_model()


class UserRegistrationFormTests(TestCase):

    def test_valid_form(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',  # Ensure password meets complexity requirements
            'password2': 'ComplexPassword!123',
            'is_tutor': False
        }
        form = UserRegistrationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_form_username_exists(self):
        User.objects.create_user(username='testuser', email='existinguser@example.com', password='ComplexPassword!123')
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',
            'password2': 'ComplexPassword!123'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)

    def test_invalid_form_password_mismatch(self):
        form_data = {
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'testuser@example.com',
            'password1': 'ComplexPassword!123',
            'password2': 'ComplexPassword!456'
        }
        form = UserRegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
