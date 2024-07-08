import random
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Profile, Subject, Tutor, TutorAvailability, Lesson, Review

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate the database with sample data'

    def handle(self, *args, **kwargs):
        self.create_users()
        self.create_subjects()
        self.create_profiles()
        self.create_tutors()
        self.create_availabilities()
        self.create_lessons()
        self.create_reviews()
        self.stdout.write(self.style.SUCCESS('Successfully populated the database'))

    def create_users(self):
        self.users = []
        for i in range(1, 15):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                first_name=f'FirstName{i}',
                last_name=f'LastName{i}',
                password='password123'
            )
            self.users.append(user)
        self.tutor_users = self.users[:6]
        self.student_users = self.users[6:]

    def create_subjects(self):
        self.math = Subject.objects.create(name='Math', description='Mathematics subject')
        self.physics = Subject.objects.create(name='Physics', description='Physics subject')
        self.chemistry = Subject.objects.create(name='Chemistry', description='Chemistry subject')

    def create_profiles(self):
        self.profiles = []
        for user in self.users:
            profile = Profile.objects.create(
                user=user,
                birth_date='1990-01-01',
                gender=random.choice(['M', 'F', 'O']),
                location='Location',
                is_tutor=user in self.tutor_users,
                address='Address',
                phone='555-1234'
            )
            self.profiles.append(profile)

    def create_tutors(self):
        self.tutors = []
        for user in self.tutor_users:
            tutor = Tutor.objects.create(
                user=user,
                hourly_rate=random.uniform(20, 100),
                bio=f'Experienced {random.choice(["Math", "Physics", "Chemistry"])} tutor',
                qualifications='B.Sc. in Subject',
                experience=random.randint(1, 10),
                average_rating=0.0,
                review_count=0
            )
            tutor.subjects.add(self.math, self.physics, self.chemistry)
            self.tutors.append(tutor)

    def create_availabilities(self):
        days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
        for tutor in self.tutors:
            for day in days_of_week:
                TutorAvailability.objects.create(
                    tutor=tutor,
                    day_of_week=day,
                    start_time=time(random.randint(8, 12), 0),
                    end_time=time(random.randint(13, 17), 0)
                )

    def create_lessons(self):
        self.lessons = []
        for student_profile in self.profiles[6:]:
            for _ in range(random.randint(1, 3)):
                lesson = Lesson.objects.create(
                    student=student_profile,
                    tutor=random.choice(self.tutors),
                    subject=random.choice([self.math, self.physics, self.chemistry]),
                    booking_date=timezone.now().date(),
                    start_time=time(random.randint(8, 15), 0),
                    end_time=time(random.randint(16, 19), 0)
                )
                self.lessons.append(lesson)

    def create_reviews(self):
        for lesson in self.lessons:
            Review.objects.create(
                student=lesson.student,
                tutor=lesson.tutor,
                lesson=lesson,
                rating=random.randint(1, 5),
                comment='Great lesson!',
                created_at=timezone.now()
            )
