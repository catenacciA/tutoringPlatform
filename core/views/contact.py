import json
import logging
from datetime import date

from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import FormView, UpdateView, DeleteView
from django.core.cache import cache

from core.models import Lesson, Tutor, TutorAvailability, Profile
from ..forms.contact import BookLessonForm, ModifyLessonForm, DeleteLessonForm

logger = logging.getLogger(__name__)

QUEUE_CACHE_PREFIX = 'lesson_queue_'


def send_email_notification(subject, message, recipient_list):
    try:
        send_mail(
            subject,
            message,
            'alessandrocatenacci2@gmail.com',
            recipient_list,
        )
        logger.info(f"Email sent successfully to {recipient_list}")
    except Exception as e:
        logger.error(f"Error sending email to {recipient_list}: {e}", exc_info=True)


def add_to_queue(tutor_id, booking_date, start_time, end_time, user_email):
    queue_key = f"{QUEUE_CACHE_PREFIX}{tutor_id}_{booking_date}_{start_time}_{end_time}"
    queue = cache.get(queue_key, [])
    if user_email not in queue:
        queue.append(user_email)
        cache.set(queue_key, queue)
    return queue


def pop_from_queue(tutor_id, booking_date, start_time, end_time):
    queue_key = f"{QUEUE_CACHE_PREFIX}{tutor_id}_{booking_date}_{start_time}_{end_time}"
    queue = cache.get(queue_key, [])
    if queue:
        next_user = queue.pop(0)
        cache.set(queue_key, queue)
        return next_user
    return None


class BookLessonView(FormView):
    template_name = 'core/book_lesson.html'
    form_class = BookLessonForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tutor_id = self.kwargs['tutor_id']
        tutor = get_object_or_404(Tutor, id=tutor_id)
        availabilities = TutorAvailability.objects.filter(tutor=tutor, is_available=True)
        subjects = tutor.subjects.all()
        availabilities_json = json.dumps(list(availabilities.values('day_of_week', 'start_time', 'end_time')),
                                         cls=DjangoJSONEncoder)
        context.update({
            'tutor': tutor,
            'availabilities': availabilities_json,
            'subjects': subjects
        })
        logger.debug(f'Availabilities JSON: {availabilities_json}')
        return context

    def form_valid(self, form):
        try:
            lesson = form.save(commit=False)
            tutor_id = self.kwargs['tutor_id']
            student_profile = get_object_or_404(Profile, user=self.request.user)
            tutor = get_object_or_404(Tutor, id=tutor_id)
            lesson.student = student_profile
            lesson.tutor = tutor

            booking_date = lesson.booking_date
            start_time = lesson.start_time
            end_time = lesson.end_time

            # Check if the booking date is in the past
            if booking_date < date.today():
                logger.error('Booking date cannot be in the past.')
                return JsonResponse({'errors': 'Booking date cannot be in the past.'}, status=400)

            # Check if the booking date is in the future
            if booking_date <= date.today():
                logger.error('Booking date must be in the future.')
                return JsonResponse({'errors': 'Booking date must be in the future.'}, status=400)

            # Check if the booking date and times are within the tutor's availability
            day_of_week = booking_date.strftime('%A')
            availability = TutorAvailability.objects.filter(
                tutor=tutor,
                day_of_week=day_of_week,
                start_time__lte=start_time,
                end_time__gte=end_time,
                is_available=True
            ).first()

            if not availability:
                logger.error('Selected time is not within the tutor\'s available slots.')
                return JsonResponse({'errors': 'Selected time is not within the tutor\'s available slots.'}, status=400)

            # Ensure the custom time falls within the available slot
            if start_time < availability.start_time or end_time > availability.end_time:
                logger.error('Selected time range is not within the available slot.')
                return JsonResponse({'errors': 'Selected time range is not within the available slot.'}, status=400)

            # Check if the lesson time is already booked
            existing_lesson = Lesson.objects.filter(
                tutor=tutor,
                booking_date=booking_date,
                start_time__lte=end_time,
                end_time__gte=start_time,
            ).first()

            if existing_lesson:
                # Add to queue if slot is already booked
                queue = add_to_queue(tutor_id, booking_date, start_time, end_time, self.request.user.email)
                return JsonResponse({'queued': True, 'position': len(queue)}, status=202)

            lesson.save()

            # Send email notifications
            student_email_content = f'You have booked a lesson with {tutor.user.get_full_name()} for {lesson.booking_date} at {lesson.start_time}.'
            tutor_email_content = f'A lesson has been booked with you by {student_profile.user.get_full_name()} for {lesson.booking_date} at {lesson.start_time}.'

            send_email_notification('Lesson Booked', student_email_content, [self.request.user.email])
            send_email_notification('New Lesson Booked', tutor_email_content, [tutor.user.email])

            return JsonResponse({'success': True})
        except Exception as e:
            logger.error(f'Error in form_valid: {e}', exc_info=True)
            return JsonResponse({'errors': str(e)}, status=500)

    def form_invalid(self, form):
        logger.error(f'Form invalid: {form.errors.as_json()}')
        return JsonResponse({'errors': form.errors}, status=400)


class ModifyLessonView(UpdateView):
    model = Lesson
    form_class = ModifyLessonForm
    template_name = 'core/modify_lesson.html'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        lesson = self.get_object()
        tutor = lesson.tutor
        form.fields['subject'].queryset = tutor.subjects.all()
        return form

    def form_valid(self, form):
        lesson = form.save()

        # Perform the same checks as in BookLessonView
        booking_date = lesson.booking_date
        start_time = lesson.start_time
        end_time = lesson.end_time

        if booking_date < date.today():
            logger.error('Booking date cannot be in the past.')
            return JsonResponse({'errors': 'Booking date cannot be in the past.'}, status=400)

        if booking_date <= date.today():
            logger.error('Booking date must be in the future.')
            return JsonResponse({'errors': 'Booking date must be in the future.'}, status=400)

        day_of_week = booking_date.strftime('%A')
        availability = TutorAvailability.objects.filter(
            tutor=lesson.tutor,
            day_of_week=day_of_week,
            start_time__lte=start_time,
            end_time__gte=end_time,
            is_available=True
        ).first()

        if not availability:
            logger.error('Selected time is not within the tutor\'s available slots.')
            return JsonResponse({'errors': 'Selected time is not within the tutor\'s available slots.'}, status=400)

        if start_time < availability.start_time or end_time > availability.end_time:
            logger.error('Selected time range is not within the available slot.')
            return JsonResponse({'errors': 'Selected time range is not within the available slot.'}, status=400)

        # Check if the lesson time is already booked
        existing_lesson = Lesson.objects.filter(
            tutor=lesson.tutor,
            booking_date=booking_date,
            start_time__lte=end_time,
            end_time__gte=start_time,
        ).exclude(pk=lesson.pk).first()

        if existing_lesson:
            logger.error('The time slot is already booked.')
            return JsonResponse({'errors': 'The time slot is already booked.'}, status=400)

        # Send email notifications
        student_email_content = (f'Your lesson with {lesson.tutor.user.get_full_name()} has been modified. New '
                                 f'details:\nDate: {lesson.booking_date}\nTime: {lesson.start_time} - {lesson.end_time}\nStatus: {lesson.status}')
        tutor_email_content = (f'The lesson with {lesson.student.user.get_full_name()} has been modified. New '
                               f'details:\nDate: {lesson.booking_date}\nTime: {lesson.start_time} - {lesson.end_time}\nStatus: {lesson.status}')

        send_email_notification('Lesson Modified', student_email_content, [self.request.user.email])
        send_email_notification('Lesson Modified', tutor_email_content, [lesson.tutor.user.email])

        return JsonResponse({'success': True})

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors}, status=400)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lesson = self.get_object()
        tutor = lesson.tutor
        context['tutor_availabilities'] = TutorAvailability.objects.filter(tutor=tutor, is_available=True)
        return context


class DeleteLessonView(DeleteView):
    model = Lesson
    form_class = DeleteLessonForm
    success_url = reverse_lazy('core:edit_profile')
    template_name = 'core/delete_lesson.html'

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        lesson = self.get_object()

        # Extract necessary data before deleting the lesson
        tutor_name = lesson.tutor.user.get_full_name()
        booking_date = lesson.booking_date
        start_time = lesson.start_time
        end_time = lesson.end_time
        user_email = self.request.user.email

        # Delete the lesson
        lesson.delete()

        try:
            student_email_content = f'Your lesson with {tutor_name} on {booking_date} has been canceled.'
            tutor_email_content = (f'The lesson with {lesson.student.user.get_full_name()} on {booking_date} has been '
                                   f'canceled.')

            send_email_notification('Lesson Canceled', student_email_content, [user_email])
            send_email_notification('Lesson Canceled', tutor_email_content, [lesson.tutor.user.email])

            logger.info(f"Email sent successfully for lesson cancellation: {lesson.id}")

            # Notify the next student in the queue
            next_user_email = pop_from_queue(lesson.tutor.id, booking_date, start_time, end_time)
            if next_user_email:
                notification_message = (f'A slot has become available for your lesson with {tutor_name} on '
                                        f'{booking_date} from {start_time} to {end_time}. Please log in to book your '
                                        f'lesson.')
                send_email_notification('Slot Available', notification_message, [next_user_email])
                logger.info(f"Queue notification sent to: {next_user_email}")

            return JsonResponse({'success': True, 'message': 'Lesson canceled and email sent successfully.'})
        except Exception as e:
            logger.error(f"Error sending email for lesson cancellation: {e}", exc_info=True)
            return JsonResponse({'success': False, 'message': 'Lesson canceled but email sending failed.'}, status=500)

    def form_invalid(self, form):
        return JsonResponse({'errors': form.errors}, status=400)
