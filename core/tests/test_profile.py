from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from ..models import Tutor, Lesson, Review, Profile, Subject, TutorAvailability

User = get_user_model()


class BaseTestCase(TestCase):
    def setUp(self):
        self.subject_math = Subject.objects.create(name='Mathematics')
        self.subject_physics = Subject.objects.create(name='Physics')

        self.student_user = self.create_user('studentuser', 'studentuser@example.com', '12345')
        self.student_profile = self.create_profile(self.student_user, '2000-01-01', 'M', 'Location1', 'Address1', '1111111111')

        self.tutor_user = self.create_user('tutoruser', 'tutoruser@example.com', '12345')
        self.tutor_profile = self.create_profile(self.tutor_user, '1980-01-01', 'F', 'Location2', 'Address2', '2222222222', is_tutor=True)
        self.tutor = self.create_tutor(self.tutor_user, 'PhD in Mathematics', 10, [self.subject_math, self.subject_physics])

        TutorAvailability.objects.create(tutor=self.tutor, day_of_week='Monday', start_time='09:00:00', end_time='17:00:00')

        self.lesson = Lesson.objects.create(
            student=self.student_profile,
            tutor=self.tutor,
            subject=self.subject_math,
            booking_date=datetime.now().date() + timedelta(days=1),
            start_time='10:00:00',
            end_time='11:00:00'
        )

        self.client = self.client_class()

    def create_user(self, username, email, password):
        return User.objects.create_user(username=username, email=email, password=password)

    def create_profile(self, user, birth_date, gender, location, address, phone, is_tutor=False):
        return Profile.objects.create(user=user, birth_date=birth_date, gender=gender, location=location, address=address, phone=phone, is_tutor=is_tutor)

    def create_tutor(self, user, qualifications, experience, subjects):
        tutor = Tutor.objects.create(user=user, qualifications=qualifications, experience=experience)
        tutor.subjects.add(*subjects)
        return tutor

    def login_user(self, username, password):
        self.client.login(username=username, password=password)


class EditProfileViewTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.login_user('tutoruser', '12345')

    def test_edit_profile_view_template(self):
        response = self.client.get(reverse('core:edit_profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/edit_profile.html')

    def test_edit_profile_view_context(self):
        response = self.client.get(reverse('core:edit_profile'))
        self.assertIn('tutor_form', response.context)
        self.assertIn('password_form', response.context)
        self.assertIn('user_form', response.context)
        self.assertIn('availabilities_formset', response.context)

    def test_handle_password_change(self):
        data = {
            'old_password': '12345',
            'new_password1': 'A_strong_password_123',
            'new_password2': 'A_strong_password_123',
            'change_password': 'true'
        }
        response = self.client.post(reverse('core:edit_profile'), data)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_data['success'])
        self.assertEqual(response_data['message'], 'Your password has been updated successfully!')

    def test_handle_profile_save_tutor(self):
        data = {
            'username': 'newtutorusername',
            'email': 'newtutoremail@example.com',
            'first_name': 'NewTutor',
            'last_name': 'Name',
            'birth_date': '1980-01-01',
            'gender': 'F',
            'location': 'New Location',
            'address': 'New Address',
            'phone': '1234567890',
            'is_tutor': 'True',
            'save_profile': 'true',
            'form-TOTAL_FORMS': '1',
            'form-INITIAL_FORMS': '0',
            'form-MIN_NUM_FORMS': '0',
            'form-MAX_NUM_FORMS': '1000',
            'form-0-day_of_week': 'Tuesday',
            'form-0-start_time': '09:00:00',
            'form-0-end_time': '17:00:00',
            'form-0-tutor': str(self.tutor.id),
            'form-0-is_available': 'on'
        }
        response = self.client.post(reverse('core:edit_profile'), data)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_data['success'])
        self.tutor_user.refresh_from_db()
        self.assertEqual(self.tutor_user.username, 'newtutorusername')
        self.assertEqual(self.tutor_user.email, 'newtutoremail@example.com')
        self.assertEqual(response_data['message'], 'Your profile has been updated.')

    def test_handle_profile_save_student(self):
        self.login_user('studentuser', '12345')
        data = {
            'username': 'newstudentusername',
            'email': 'newstudentemail@example.com',
            'first_name': 'NewStudent',
            'last_name': 'Name',
            'birth_date': '2000-01-01',
            'gender': 'M',
            'location': 'New Location',
            'address': 'New Address',
            'phone': '1234567890',
            'is_tutor': 'False',
            'save_profile': 'true',
        }
        response = self.client.post(reverse('core:edit_profile'), data)
        response_data = response.json()
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response_data['success'])
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.username, 'newstudentusername')
        self.assertEqual(self.student_user.email, 'newstudentemail@example.com')
        self.assertEqual(response_data['message'], 'Your profile has been updated.')

    def test_invalid_form_submission(self):
        data = {}  # Empty data should trigger invalid form submission
        response = self.client.post(reverse('core:edit_profile'), data, content_type='application/x-www-form-urlencoded')
        response_data = response.json()
        self.assertEqual(response.status_code, 200)  # Should be 200 because it returns a JSON response, not a 400 error
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['message'], 'Invalid form submission')


class ProfileViewTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.login_user('studentuser', '12345')

    def test_profile_view_template(self):
        response = self.client.get(reverse('core:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/profile.html')

    def test_profile_view_context(self):
        response = self.client.get(reverse('core:profile'))
        self.assertIn('tutor_form', response.context)
        self.assertIn('password_form', response.context)
        self.assertIn('lessons', response.context)
        self.assertIn('tutor_lessons', response.context)
        self.assertIn('lesson_reviews', response.context)


class PublicProfileViewTests(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.profile_user = self.create_user('profileuser', 'profileuser@example.com', '12345')
        self.profile_profile_user = self.create_profile(self.profile_user, '1980-01-01', 'F', 'Location3', 'Address3', '3333333333', is_tutor=True)
        self.tutor = self.create_tutor(self.profile_user, 'MSc in Physics', 5, [self.subject_math])
        self.review = Review.objects.create(lesson=self.lesson, rating=5, student=self.student_profile, tutor=self.tutor)

    def test_public_profile_view_template(self):
        response = self.client.get(reverse('core:public_profile', args=[self.profile_user.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'profile/public_profile.html')

    def test_public_profile_view_context(self):
        response = self.client.get(reverse('core:public_profile', args=[self.profile_user.id]))
        self.assertIn('profile_user', response.context)
        self.assertIn('tutor', response.context)
        self.assertIn('lessons', response.context)
        self.assertIn('tutor_lessons', response.context)
        self.assertIn('total_review_score', response.context)
        self.assertEqual(response.context['total_review_score'], 5.0)
