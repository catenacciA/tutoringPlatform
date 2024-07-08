from django.test import TestCase
from django.urls import reverse
from django.test.client import Client


class RegisterTemplateTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.url = reverse('core:register')

    def test_template_content(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<h1><i class="bi bi-person-plus-fill"></i> Register</h1>')
        self.assertContains(response, 'Create a new account to access our platform.')
        self.assertContains(response, 'form id="register-form" method="post" enctype="multipart/form-data"')
        self.assertContains(response, '<button type="submit" class="btn btn-primary mt-3">Register</button>')
