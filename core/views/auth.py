from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import AuthenticationForm


class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    authentication_form = AuthenticationForm


class CustomLogoutView(LogoutView):
    template_name = 'auth/logout.html'
