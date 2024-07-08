import json

from django.db.models import Avg
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.http import JsonResponse

from ..forms.profile import ProfileForm, TutorEditForm, TutorAvailabilityForm, UserForm
from ..models import TutorAvailability, Lesson, User, Review

import logging

logger = logging.getLogger(__name__)

DAYS_OF_WEEK = [
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'
]

TutorAvailabilityFormSet = modelformset_factory(
    TutorAvailability,
    form=TutorAvailabilityForm,
    extra=0,
    can_delete=True
)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'profile/profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tutor = getattr(user, 'tutor', None)
        lessons = Lesson.objects.filter(student__user=user)
        tutor_lessons = Lesson.objects.filter(tutor__user=user)

        lesson_reviews = {}
        for lesson in tutor_lessons:
            lesson_reviews[lesson.pk] = Review.objects.filter(lesson=lesson)

        context.update({
            'tutor_form': TutorEditForm(instance=tutor) if tutor else None,
            'availabilities_form': TutorAvailabilityForm(instance=tutor) if tutor else None,
            'password_form': PasswordChangeForm(user=user),
            'lessons': lessons,
            'tutor_lessons': tutor_lessons,
            'lesson_reviews': lesson_reviews,
        })
        return context


class PublicProfileView(TemplateView):
    template_name = 'profile/public_profile.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_id = kwargs.get('user_id')
        profile_user = get_object_or_404(User, id=user_id)
        tutor = getattr(profile_user, 'tutor', None)
        lessons = Lesson.objects.filter(student__user=profile_user)
        tutor_lessons = Lesson.objects.filter(tutor__user=profile_user)
        context['is_tutor'] = self.request.user.is_authenticated and hasattr(self.request.user, 'tutor')

        total_review_score = None
        reviews = None
        if tutor:
            reviews = tutor.reviews.all().select_related('lesson__subject')
            if reviews.exists():
                total_review_score = reviews.aggregate(average_rating=Avg('rating'))['average_rating']

        context.update({
            'profile_user': profile_user,
            'tutor': tutor,
            'lessons': lessons,
            'tutor_lessons': tutor_lessons,
            'total_review_score': total_review_score,
            'reviews': reviews,
        })

        return context


@method_decorator(login_required, name='dispatch')
class EditProfileView(UpdateView):
    template_name = 'profile/edit_profile.html'
    form_class = ProfileForm
    success_url = reverse_lazy('core:profile')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        tutor = getattr(user, 'tutor', None)
        context.update({
            'user_form': UserForm(instance=user),
            'tutor_form': TutorEditForm(instance=tutor) if tutor else None,
            'availabilities_formset': TutorAvailabilityFormSet(queryset=tutor.availabilities.all(),
                                                               form_kwargs={'tutor': tutor}) if tutor else None,
            'password_form': PasswordChangeForm(user=user),
            'days_of_week_json': json.dumps(DAYS_OF_WEEK)
        })
        return context

    def post(self, request, *args, **kwargs):
        user = self.request.user
        profile_form = ProfileForm(request.POST, request.FILES, instance=user.profile)
        user_form = UserForm(request.POST, instance=user)
        tutor = getattr(user, 'tutor', None)
        tutor_form = TutorEditForm(request.POST, request.FILES, instance=tutor) if tutor else None
        availabilities_formset = TutorAvailabilityFormSet(request.POST, queryset=tutor.availabilities.all(),
                                                          form_kwargs={'tutor': tutor}) if tutor else None

        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(user=user, data=request.POST)
            return self.handle_password_change(password_form)

        if 'save_profile' in request.POST:
            return self.handle_profile_save(profile_form, user_form, tutor_form, availabilities_formset)

        logger.error("Invalid form submission: Neither save_profile nor change_password in POST")
        return JsonResponse({'success': False, 'message': 'Invalid form submission'})

    def handle_profile_save(self, profile_form, user_form, tutor_form, availabilities_formset):
        if all([profile_form.is_valid(), user_form.is_valid(), tutor_form is None or tutor_form.is_valid(),
                availabilities_formset is None or availabilities_formset.is_valid()]):
            user_form.save()
            self._update_username(self.request.user)
            self._handle_profile_picture(self.request.user)
            self.save_profile_and_tutor(profile_form, tutor_form, availabilities_formset)
            logger.info("Profile updated successfully")
            return JsonResponse({'success': True, 'message': "Your profile has been updated."})
        else:
            errors = self.collect_form_errors(profile_form, user_form, tutor_form, availabilities_formset)
            logger.error("Profile update failed with errors: %s", errors)
            return JsonResponse({'success': False, 'errors': errors})

    def handle_password_change(self, password_form):
        if password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(self.request, user)
            logger.info("Password updated successfully")
            return JsonResponse({'success': True, 'message': 'Your password has been updated successfully!'})
        else:
            logger.error("Password change failed with errors: %s", password_form.errors)
            return JsonResponse({'success': False, 'errors': password_form.errors})

    def save_profile_and_tutor(self, profile_form, tutor_form=None, availabilities_formset=None):
        profile = profile_form.save(commit=False)
        profile.save()
        if tutor_form:
            tutor = tutor_form.save(commit=False)
            tutor.save()
            tutor_form.save_m2m()
            if availabilities_formset:
                instances = availabilities_formset.save(commit=False)
                for instance in instances:
                    instance.tutor = tutor
                    instance.save()
                for deleted_form in availabilities_formset.deleted_forms:
                    if deleted_form.instance.pk:
                        deleted_form.instance.delete()
                availabilities_formset.save_m2m()

    def collect_form_errors(self, profile_form, user_form, tutor_form=None, availabilities_formset=None):
        errors = {**profile_form.errors, **user_form.errors}
        if tutor_form:
            errors.update(tutor_form.errors)
        if availabilities_formset and not availabilities_formset.is_valid():
            errors['availabilities'] = availabilities_formset.errors
        return errors

    def _update_username(self, user):
        new_username = self.request.POST.get('username')
        if new_username and new_username != user.username:
            user.username = new_username
            user.save()
            logger.info("Username updated to %s", new_username)

    def _handle_profile_picture(self, user):
        if self.request.POST.get('delete_propic') == 'true':
            default_propic = self.request.POST.get('default_propic')
            self._set_default_picture(user, default_propic)
        elif 'propic' in self.request.FILES:
            self._set_uploaded_picture(user, self.request.FILES['propic'])

    def _set_default_picture(self, user, default_propic):
        propic_path = default_propic.replace('/media/', '')
        if hasattr(user, 'tutor'):
            user.tutor.profile_picture = propic_path
            user.tutor.save()
        else:
            user.profile.propic = propic_path
            user.profile.save()
        logger.info("Profile picture reset to default")

    def _set_uploaded_picture(self, user, uploaded_picture):
        if hasattr(user, 'tutor'):
            user.tutor.profile_picture = uploaded_picture
            user.tutor.save()
        else:
            user.profile.propic = uploaded_picture
            user.profile.save()
        logger.info("Profile picture updated")
