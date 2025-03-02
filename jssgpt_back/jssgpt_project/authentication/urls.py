from django.urls import path
from .views import GoogleLoginCallbackView, CurrentUserView, LogoutView

urlpatterns = [
    path('google/callback/', GoogleLoginCallbackView.as_view(), name='google_callback'),
    path('current-user/', CurrentUserView.as_view(), name='current_user'),
    path('logout/', LogoutView.as_view(), name='logout'),
]
