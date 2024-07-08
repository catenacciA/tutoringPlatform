# views.py
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.generic import FormView, ListView

from core.models import Tutor
from ..forms.research import TutorSearchForm


class TutorSearchView(FormView):
    template_name = 'core/advanced_research.html'
    form_class = TutorSearchForm

    def form_valid(self, form):
        query_params = form.cleaned_data
        return self.render_to_response(self.get_context_data(form=form, query_params=query_params))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form, errors=form.errors))


class TutorResultsView(ListView):
    model = Tutor
    template_name = 'core/search_results.html'
    context_object_name = 'tutors'

    def get_queryset(self):
        queryset = super().get_queryset()
        form = TutorSearchForm(self.request.GET or None)

        if not self.request.GET:
            return queryset.none()

        if form.is_valid():
            try:
                subject = form.cleaned_data.get('subject')
                min_hourly_rate = form.cleaned_data.get('min_hourly_rate')
                max_hourly_rate = form.cleaned_data.get('max_hourly_rate')
                location = form.cleaned_data.get('location')
                min_rating = form.cleaned_data.get('min_rating')
                available_on_day = form.cleaned_data.get('available_on_day')
                available_from = form.cleaned_data.get('available_from')
                available_to = form.cleaned_data.get('available_to')
                experience = form.cleaned_data.get('experience')

                if subject:
                    queryset = queryset.filter(subjects=subject)
                if min_hourly_rate is not None:
                    queryset = queryset.filter(hourly_rate__gte=min_hourly_rate)
                if max_hourly_rate is not None:
                    queryset = queryset.filter(hourly_rate__lte=max_hourly_rate)
                if location:
                    queryset = queryset.filter(user__profile__location__icontains=location)
                if min_rating is not None:
                    queryset = queryset.filter(average_rating__gte=min_rating)
                if experience is not None:
                    queryset = queryset.filter(experience__gte=experience)

                if available_on_day or (available_from and available_to):
                    availability_filter = Q(availabilities__is_available=True)
                    if available_on_day and available_on_day != '---------':
                        availability_filter &= Q(availabilities__day_of_week=available_on_day.capitalize())
                    if available_from and available_to:
                        availability_filter &= Q(availabilities__start_time__lte=available_from,
                                                 availabilities__end_time__gte=available_to)
                    queryset = queryset.filter(availability_filter).distinct()

            except ValidationError as e:
                form.add_error(None, e)
                print(f"ValidationError encountered: {e}")
                return queryset.none()
        else:
            print("Form is not valid, returning none.")
            return queryset.none()

        return queryset

    def render_to_response(self, context, **response_kwargs):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(self.template_name, context)
            return JsonResponse({'html': html})
        return super().render_to_response(context, **response_kwargs)
