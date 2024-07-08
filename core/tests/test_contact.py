from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from core.models import Tutor, TutorAvailability, Lesson, Profile, User, Subject
from django.core.cache import cache
from unittest.mock import patch


class BookLessonViewTests(TestCase):
    def setUp(self):
        # Set up test data
        self.subject = Subject.objects.create(name='Math')
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')
        self.profile = Profile.objects.create(user=self.user)
        self.tutor_user = User.objects.create_user(username='tutoruser', password='tutorpassword',
                                                   email='tutoruser@example.com')
        self.tutor = Tutor.objects.create(user=self.tutor_user)
        TutorAvailability.objects.create(tutor=self.tutor, day_of_week='Monday', start_time='09:00', end_time='17:00',
                                         is_available=True)
        self.client.login(username='testuser', password='testpassword')

    def tearDown(self):
        # Clean up after each test
        User.objects.all().delete()
        Tutor.objects.all().delete()
        Profile.objects.all().delete()
        TutorAvailability.objects.all().delete()
        Lesson.objects.all().delete()
        Subject.objects.all().delete()
        cache.clear()

    def get_next_monday(self):
        today = timezone.now().date()
        days_ahead = 0 - today.weekday() + 7  # 0 is Monday
        if days_ahead <= 0:
            days_ahead += 7
        return today + timezone.timedelta(days=days_ahead)

    def test_booking_in_the_past(self):
        # Test booking a lesson in the past
        response = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': '2000-01-01',
            'start_time': '10:00',
            'end_time': '11:00'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Booking date cannot be in the past.', response.json()['errors'])

    def test_booking_on_current_date(self):
        # Test booking a lesson on the current date
        today = timezone.now().date()
        response = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': today,
            'start_time': '10:00',
            'end_time': '11:00'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Booking date must be in the future.', response.json()['errors'])

    def test_booking_without_availability(self):
        # Test booking a lesson outside the tutor's available hours
        future_date = self.get_next_monday()
        response = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '18:00',
            'end_time': '19:00'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Selected time is not within the tutor's available slots.", response.json()['errors'])

    def test_booking_overlapping_with_another_lesson(self):
        # Test booking a lesson that overlaps with another existing lesson
        future_date = self.get_next_monday()
        Lesson.objects.create(tutor=self.tutor, student=self.profile, subject=self.subject, booking_date=future_date,
                              start_time='10:00', end_time='11:00')
        response = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '10:30',
            'end_time': '11:30'
        })
        print(response.json())  # Debug: Print the actual response
        self.assertEqual(response.status_code, 202)
        self.assertIn('queued', response.json())
        self.assertEqual(response.json()['position'], 1)

    def test_valid_booking(self):
        # Test booking a valid lesson
        future_date = self.get_next_monday()
        response = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '10:00',
            'end_time': '11:00'
        })
        print(response.json())  # Debug: Print the actual response
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())

    def test_queue_position(self):
        # Test queueing for overlapping bookings
        future_date = self.get_next_monday()
        Lesson.objects.create(tutor=self.tutor, student=self.profile, subject=self.subject, booking_date=future_date,
                              start_time='10:00', end_time='11:00')

        # First overlapping booking by the same user
        response1 = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '10:30',
            'end_time': '11:30'
        })
        print(response1.json())
        self.assertEqual(response1.status_code, 202)
        self.assertIn('queued', response1.json())
        self.assertEqual(response1.json()['position'], 1)

        # Create a new user for the second booking
        self.user2 = User.objects.create_user(username='testuser2', password='testpassword2',
                                              email='testuser2@example.com')
        self.profile2 = Profile.objects.create(user=self.user2)
        self.client.login(username='testuser2', password='testpassword2')

        # Second overlapping booking by a different user
        response2 = self.client.post(reverse('core:book_lesson', kwargs={'tutor_id': self.tutor.id}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '10:30',
            'end_time': '11:30'
        })
        print("RESPONSE", response2.json())  # Debug: Print the actual response
        self.assertEqual(response2.status_code, 202)
        self.assertIn('queued', response2.json())
        self.assertEqual(response2.json()['position'], 2)


class ModifyDeleteLessonViewTests(TestCase):
    def setUp(self):
        # Set up test data
        self.subject = Subject.objects.create(name='Physics')
        self.user = User.objects.create_user(username='testuser', password='testpassword', email='testuser@example.com')
        self.profile = Profile.objects.create(user=self.user)
        self.tutor_user = User.objects.create_user(username='tutoruser', password='tutorpassword',
                                                   email='tutoruser@example.com')
        self.tutor = Tutor.objects.create(user=self.tutor_user)
        TutorAvailability.objects.create(tutor=self.tutor, day_of_week='Monday', start_time='09:00', end_time='17:00',
                                         is_available=True)
        self.tutor.subjects.add(self.subject)  # Ensure the tutor can teach this subject
        self.client.login(username='testuser', password='testpassword')

    def tearDown(self):
        # Clean up after each test
        User.objects.all().delete()
        Tutor.objects.all().delete()
        Profile.objects.all().delete()
        TutorAvailability.objects.all().delete()
        Lesson.objects.all().delete()
        Subject.objects.all().delete()
        cache.clear()

    def get_next_monday(self):
        today = timezone.now().date()
        days_ahead = 0 - today.weekday() + 7  # 0 is Monday
        if days_ahead <= 0:
            days_ahead += 7
        return today + timezone.timedelta(days=days_ahead)

    def create_lesson(self):
        # Helper method to create a lesson
        return Lesson.objects.create(tutor=self.tutor, student=self.profile, subject=self.subject,
                                     booking_date=self.get_next_monday(), start_time='10:00', end_time='11:00')

    def test_modify_lesson_valid(self):
        lesson = self.create_lesson()
        # Test modifying a lesson with valid data
        future_date = self.get_next_monday()
        response = self.client.post(reverse('core:modify_lesson', kwargs={'pk': lesson.pk}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '11:00',
            'end_time': '12:00',
            'status': 'booked'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())

    def test_modify_lesson_past_date(self):
        lesson = self.create_lesson()
        # Test modifying a lesson with a past date
        response = self.client.post(reverse('core:modify_lesson', kwargs={'pk': lesson.pk}), {
            'subject': self.subject.id,
            'booking_date': '2000-01-01',
            'start_time': '10:00',
            'end_time': '11:00',
            'status': 'booked'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('Booking date cannot be in the past.', response.json()['errors'])

    def test_modify_lesson_outside_availability(self):
        lesson = self.create_lesson()
        # Test modifying a lesson outside the tutor's available hours
        future_date = self.get_next_monday()
        response = self.client.post(reverse('core:modify_lesson', kwargs={'pk': lesson.pk}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '18:00',
            'end_time': '19:00',
            'status': 'booked'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn("Selected time is not within the tutor's available slots.", response.json()['errors'])

    def test_modify_lesson_time_already_booked(self):
        lesson = self.create_lesson()
        # Test modifying a lesson to a time slot already booked
        future_date = self.get_next_monday()
        overlapping_lesson = Lesson.objects.create(tutor=self.tutor, student=self.profile, subject=self.subject,
                                                   booking_date=future_date, start_time='11:00', end_time='12:00')
        response = self.client.post(reverse('core:modify_lesson', kwargs={'pk': lesson.pk}), {
            'subject': self.subject.id,
            'booking_date': future_date,
            'start_time': '11:00',
            'end_time': '12:00',
            'status': 'booked'
        })
        self.assertEqual(response.status_code, 400)
        self.assertIn('The time slot is already booked.', response.json()['errors'])

    @patch('core.views.contact.send_email_notification')
    def test_delete_lesson(self, mock_send_email):
        lesson = self.create_lesson()
        # Test deleting a lesson
        mock_send_email.return_value = True
        response = self.client.post(reverse('core:delete_lesson', kwargs={'pk': lesson.pk}), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn('success', response.json())
        self.assertFalse(Lesson.objects.filter(pk=lesson.pk).exists())

    @patch('core.views.contact.send_email_notification')
    def test_delete_lesson_notifications(self, mock_send_email):
        lesson = self.create_lesson()
        # Test deleting a lesson and sending notifications
        mock_send_email.return_value = True
        with self.assertLogs('core.views', level='INFO') as log:
            response = self.client.post(reverse('core:delete_lesson', kwargs={'pk': lesson.pk}), {})
            self.assertEqual(response.status_code, 200)
            self.assertIn('success', response.json())
            self.assertFalse(Lesson.objects.filter(pk=lesson.pk).exists())
            self.assertTrue(any('Email sent successfully' in message for message in log.output))

    @patch('core.views.contact.send_email_notification', side_effect=Exception('SMTP error'))
    def test_delete_lesson_notification_failure(self, mock_send_email):
        lesson = self.create_lesson()
        # Test deleting a lesson when email sending fails
        with self.assertLogs('core.views', level='ERROR') as log:
            response = self.client.post(reverse('core:delete_lesson', kwargs={'pk': lesson.pk}), {})
            self.assertEqual(response.status_code, 500)
            self.assertIn('Error sending email for lesson cancellation', log.output[0])