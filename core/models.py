from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class User(AbstractUser):
    """
    Custom reviews model extending Django's AbstractUser to include first and last names.
    """
    first_name = models.CharField(max_length=30, blank=False)
    last_name = models.CharField(max_length=30, blank=False)
    groups = models.ManyToManyField(
        Group,
        related_name='core_user_set',
        blank=True,
        help_text=(
            'The groups this reviews belongs to. A reviews will get all permissions '
            'granted to each of their groups.'
        ),
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='core_user_set',
        blank=True,
        help_text='Specific permissions for this reviews.',
        verbose_name='reviews permissions',
    )
    email = models.EmailField(unique=True, blank=False)
    username = models.CharField(max_length=150, unique=True, blank=False)

    def __str__(self):
        return self.username

    def get_user_model(self):
        return self


class Subject(models.Model):
    """
    Model representing a subject for tutoring.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Profile(models.Model):
    """
    Model representing a reviews profile with additional information.
    """

    class Gender(models.TextChoices):
        MALE = 'M', 'Male'
        FEMALE = 'F', 'Female'
        OTHER = 'O', 'Other'

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', unique=True)
    propic = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    is_tutor = models.BooleanField(default=False)
    address = models.CharField(max_length=255, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f'{self.user.first_name} {self.user.last_name}'

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'


class Tutor(models.Model):
    """
    Model representing a tutor with their details.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='tutor', unique=True)
    subjects = models.ManyToManyField(Subject, related_name='tutors')
    hourly_rate = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    availability_status = models.BooleanField(default=True)
    bio = models.TextField(null=True, blank=True)
    qualifications = models.TextField()
    experience = models.IntegerField(validators=[MinValueValidator(0)], default=0)
    profile_picture = models.ImageField(upload_to='tutor_photos/', null=True, blank=True)
    average_rating = models.FloatField(default=0.0)
    review_count = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'Tutor: {self.user.first_name} {self.user.last_name}'

    class Meta:
        verbose_name = 'Tutor'
        verbose_name_plural = 'Tutors'

    def get_full_name(self):
        return f'{self.user.first_name} {self.user.last_name}'


class TutorAvailability(models.Model):
    """
    Model representing a tutor's availability.
    """
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.CharField(max_length=10)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.tutor.user.first_name} {self.tutor.user.last_name} availability on {self.day_of_week}'

    class Meta:
        unique_together = ('tutor', 'day_of_week', 'start_time', 'end_time')

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time")

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


class Lesson(models.Model):
    """
    Model representing a lesson booked between a student and a tutor.
    """

    class Status(models.TextChoices):
        BOOKED = 'booked', 'Booked'
        COMPLETED = 'completed', 'Completed'
        CANCELED = 'canceled', 'Canceled'

    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='lessons')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='lessons')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    booking_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BOOKED)

    def __str__(self):
        return (f'{self.subject.name} lesson with {self.tutor.user.first_name} {self.tutor.user.last_name} '
                f'on {self.booking_date} at {self.start_time}')

    class Meta:
        ordering = ['-booking_date', '-start_time']
        indexes = [
            models.Index(fields=['booking_date']),
            models.Index(fields=['student', 'tutor']),
        ]


class Review(models.Model):
    """
    Model representing a review given by a student to a tutor.
    """
    student = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reviews')
    tutor = models.ForeignKey(Tutor, on_delete=models.CASCADE, related_name='reviews')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        choices=[(i, str(i)) for i in range(1, 6)]
    )
    comment = models.TextField()
    response = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f'Review by {self.student.user.first_name} {self.student.user.last_name} '
                f'for {self.tutor.user.first_name} {self.tutor.user.last_name}')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['tutor', 'created_at']),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_tutor_rating()

    def update_tutor_rating(self):
        reviews = self.tutor.reviews.all()
        total_rating = sum(review.rating for review in reviews)
        review_count = reviews.count()
        self.tutor.average_rating = total_rating / review_count if review_count > 0 else 0
        self.tutor.review_count = review_count
        self.tutor.save()
