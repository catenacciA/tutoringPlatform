# test_models.py

from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from core.models import Subject, Profile, Tutor, TutorAvailability, Lesson, Review

User = get_user_model()


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='password123',
            first_name='Test',
            last_name='User'
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'testuser@example.com')
        self.assertEqual(self.user.first_name, 'Test')
        self.assertEqual(self.user.last_name, 'User')


class SubjectModelTest(TestCase):
    def setUp(self):
        self.subject = Subject.objects.create(name='Mathematics')

    def test_subject_creation(self):
        self.assertEqual(self.subject.name, 'Mathematics')


class ProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testprofileuser',
            email='testprofileuser@example.com',
            password='password123',
            first_name='Profile',
            last_name='User'
        )
        self.profile = Profile.objects.create(user=self.user, gender=Profile.Gender.MALE)

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, 'testprofileuser')
        self.assertEqual(self.profile.gender, Profile.Gender.MALE)


class TutorModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tutoruser',
            email='tutoruser@example.com',
            password='password123',
            first_name='Tutor',
            last_name='User'
        )
        self.subject = Subject.objects.create(name='Science')
        self.tutor = Tutor.objects.create(
            user=self.user,
            hourly_rate=50.00,
            qualifications='PhD in Science',
            experience=10
        )
        self.tutor.subjects.add(self.subject)

    def test_tutor_creation(self):
        self.assertEqual(self.tutor.user.username, 'tutoruser')
        self.assertEqual(self.tutor.hourly_rate, 50.00)
        self.assertEqual(self.tutor.qualifications, 'PhD in Science')
        self.assertEqual(self.tutor.experience, 10)
        self.assertIn(self.subject, self.tutor.subjects.all())


class TutorAvailabilityModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='tutoravailuser',
            email='tutoravailuser@example.com',
            password='password123',
            first_name='TutorAvail',
            last_name='User'
        )
        self.tutor = Tutor.objects.create(
            user=self.user,
            hourly_rate=50.00,
            qualifications='PhD in Science',
            experience=10
        )
        self.availability = TutorAvailability.objects.create(
            tutor=self.tutor,
            day_of_week='Monday',
            start_time='09:00:00',
            end_time='17:00:00'
        )

    def test_availability_creation(self):
        self.assertEqual(self.availability.day_of_week, 'Monday')
        self.assertEqual(self.availability.start_time, '09:00:00')
        self.assertEqual(self.availability.end_time, '17:00:00')

    def test_availability_clean(self):
        with self.assertRaises(ValidationError):
            invalid_availability = TutorAvailability(
                tutor=self.tutor,
                day_of_week='Monday',
                start_time='17:00:00',
                end_time='09:00:00'
            )
            invalid_availability.clean()


class LessonModelTest(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='studentuser',
            email='studentuser@example.com',
            password='password123',
            first_name='Student',
            last_name='User'
        )
        self.tutor_user = User.objects.create_user(
            username='tutorlessonuser',
            email='tutorlessonuser@example.com',
            password='password123',
            first_name='TutorLesson',
            last_name='User'
        )
        self.subject = Subject.objects.create(name='History')
        self.student = Profile.objects.create(user=self.student_user)
        self.tutor = Tutor.objects.create(
            user=self.tutor_user,
            hourly_rate=40.00,
            qualifications='MA in History',
            experience=5
        )
        self.lesson = Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            subject=self.subject,
            booking_date='2024-01-01',
            start_time='10:00:00',
            end_time='11:00:00',
            status=Lesson.Status.BOOKED
        )

    def test_lesson_creation(self):
        self.assertEqual(self.lesson.subject.name, 'History')
        self.assertEqual(self.lesson.booking_date, '2024-01-01')
        self.assertEqual(self.lesson.start_time, '10:00:00')
        self.assertEqual(self.lesson.end_time, '11:00:00')
        self.assertEqual(self.lesson.status, Lesson.Status.BOOKED)


class ReviewModelTest(TestCase):
    def setUp(self):
        self.student_user = User.objects.create_user(
            username='studentreviewuser',
            email='studentreviewuser@example.com',
            password='password123',
            first_name='StudentReview',
            last_name='User'
        )
        self.tutor_user = User.objects.create_user(
            username='tutorreviewuser',
            email='tutorreviewuser@example.com',
            password='password123',
            first_name='TutorReview',
            last_name='User'
        )
        self.student = Profile.objects.create(user=self.student_user)
        self.tutor = Tutor.objects.create(
            user=self.tutor_user,
            hourly_rate=45.00,
            qualifications='PhD in Literature',
            experience=8
        )
        self.lesson = Lesson.objects.create(
            student=self.student,
            tutor=self.tutor,
            subject=Subject.objects.create(name='Literature'),
            booking_date='2024-01-01',
            start_time='14:00:00',
            end_time='15:00:00',
            status=Lesson.Status.BOOKED
        )
        self.review = Review.objects.create(
            student=self.student,
            tutor=self.tutor,
            lesson=self.lesson,
            rating=5,
            comment='Excellent lesson!'
        )

    def test_review_creation(self):
        self.assertEqual(self.review.rating, 5)
        self.assertEqual(self.review.comment, 'Excellent lesson!')
        self.assertEqual(self.review.tutor.average_rating, 5.0)
        self.assertEqual(self.review.tutor.review_count, 1)
