from django.contrib.auth import login
from django.db import transaction, DatabaseError, IntegrityError
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from ..forms.registration import UserRegistrationForm
from ..forms.profile import ProfileForm
from ..models import Tutor
import logging

logger = logging.getLogger(__name__)

class RegisterView(FormView):
    template_name = 'registration/register.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('core:profile')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'profile_form' not in context:
            context['profile_form'] = ProfileForm()
        return context

    def form_valid(self, form):
        try:
            with transaction.atomic():
                logger.debug("Attempting to save user")
                user = form.save()
                logger.debug(f"User {user.username} saved successfully")

                profile_form = ProfileForm(self.request.POST, self.request.FILES, instance=user.profile if hasattr(user, 'profile') else None)
                if profile_form.is_valid():
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.is_tutor = form.cleaned_data.get('is_tutor', False)

                    # Handle profile picture upload
                    if self.request.POST.get('delete_propic') == 'true':
                        profile.propic = 'unknown_user.png'
                    elif 'propic' in self.request.FILES:
                        profile.propic = self.request.FILES['propic']

                    profile.save()
                    logger.debug("Profile saved successfully")

                    if profile.is_tutor:
                        if not Tutor.objects.filter(user=user).exists():
                            tutor = Tutor.objects.create(
                                user=user,
                                hourly_rate=0,
                                qualifications='',
                                experience=0
                            )
                            if self.request.POST.get('delete_propic') == 'true':
                                tutor.profile_picture = 'unknown_user.png'
                            elif 'propic' in self.request.FILES:
                                tutor.profile_picture = self.request.FILES['propic']
                            tutor.save()
                            logger.debug("Tutor profile saved successfully")

                    login(self.request, user)
                    if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                        return JsonResponse({'success': True, 'redirect_url': self.get_success_url()})
                    else:
                        return redirect(self.get_success_url())
                else:
                    logger.error(f'Profile form errors: {profile_form.errors}')
                    if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                        return JsonResponse({'success': False, 'errors': profile_form.errors}, status=400)
                    else:
                        return self.form_invalid(form, profile_form=profile_form)
        except IntegrityError as ie:
            logger.error(f'Integrity error occurred while saving user or profile: {ie}')
            form.add_error(None, 'A user with that username or email already exists.')
        except DatabaseError as db_err:
            logger.error(f'Database error occurred: {db_err}')
            form.add_error(None, 'A database error occurred. Please try again later.')
        except ValueError as val_err:
            logger.error(f'Value error occurred: {val_err}')
            form.add_error(None, 'A value error occurred. Please check your input and try again.')
        except KeyError as key_err:
            logger.error(f'Key error occurred: {key_err}')
            form.add_error(None, 'A key error occurred. Please check your input and try again.')
        except TypeError as type_err:
            logger.error(f'Type error occurred: {type_err}')
            form.add_error(None, 'A type error occurred. Please check your input and try again.')
        except Exception as exc:
            logger.error(f'Unexpected error occurred: {exc}')
            form.add_error(None, 'An unexpected error occurred. Please try again later.')

        if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form, profile_form=None):
        if profile_form is None:
            profile_form = ProfileForm(self.request.POST, self.request.FILES)
        logger.error(f'Form invalid: {form.errors} and profile form errors: {profile_form.errors}')
        if self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'errors': {**form.errors, **profile_form.errors}}, status=400)
        else:
            return self.render_to_response(self.get_context_data(form=form, profile_form=profile_form))
