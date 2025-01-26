from django.urls import path
from .views import GoogleLoginCallbackView

urlpatterns = [
    path('google/callback/', GoogleLoginCallbackView.as_view(), name='google_callback'),
]
