from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView
from ..forms.reviews import ReviewForm, TutorResponseForm
from ..models import Tutor, Review, Lesson


class CreateReviewView(LoginRequiredMixin, CreateView):
    model = Review
    form_class = ReviewForm
    template_name = 'reviews/create_review.html'
    success_url = reverse_lazy('core:profile')

    def form_valid(self, form):
        form.instance.student = self.request.user.profile
        form.instance.tutor = get_object_or_404(Tutor, pk=self.kwargs['tutor_id'])
        form.instance.lesson = get_object_or_404(Lesson, pk=self.kwargs['lesson_id'])

        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = form.save()
            return JsonResponse({"message": "Your review has been submitted successfully."})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutor'] = get_object_or_404(Tutor, pk=self.kwargs['tutor_id'])
        context['lesson'] = get_object_or_404(Lesson, pk=self.kwargs['lesson_id'])
        return context


class UpdateReviewView(LoginRequiredMixin, UpdateView):
    model = Review
    form_class = TutorResponseForm
    template_name = 'reviews/update_review.html'
    success_url = reverse_lazy('core:profile')

    def get_queryset(self):
        return Review.objects.filter(tutor__user=self.request.user)

    def form_valid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            self.object = form.save()
            return JsonResponse({"message": "Your review has been updated successfully."})
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            errors = form.errors.as_json()
            return JsonResponse({"errors": errors}, status=400)
        return super().form_invalid(form)
