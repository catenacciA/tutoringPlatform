from django.urls import path
from .views.registration import RegisterView
from .views.auth import CustomLoginView, CustomLogoutView
from .views.main import HomeView
from .views.profile import ProfileView, EditProfileView, PublicProfileView
from .views.contact import BookLessonView, ModifyLessonView, DeleteLessonView
from .views.reviews import CreateReviewView, UpdateReviewView
from .views.research import TutorSearchView, TutorResultsView
from django.conf import settings
from django.conf.urls.static import static

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),
    path('book-lesson/<int:tutor_id>/', BookLessonView.as_view(), name='book_lesson'),
    path('modify-lesson/<int:pk>/', ModifyLessonView.as_view(), name='modify_lesson'),
    path('delete-lesson/<int:pk>/', DeleteLessonView.as_view(), name='delete_lesson'),
    path('profile/<int:user_id>/', PublicProfileView.as_view(), name='public_profile'),
    path('reviews/create/<int:tutor_id>/<int:lesson_id>/', CreateReviewView.as_view(), name='create_review'),
    path('reviews/update/<int:pk>/', UpdateReviewView.as_view(), name='update_review'),
    path('research/', TutorSearchView.as_view(), name='advanced_research'),
    path('research/results/', TutorResultsView.as_view(), name='search_results'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
