from django.views.generic import TemplateView
from ..models import Tutor


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tutors'] = Tutor.objects.all()
        context['is_tutor'] = self.request.user.is_authenticated and hasattr(self.request.user, 'tutor')
        context['top_tutors'] = Tutor.objects.order_by('-average_rating')[:3]
        return context
