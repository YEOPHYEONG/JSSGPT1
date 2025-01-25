from django.urls import path
from .views import create_recruitment

urlpatterns = [
    path('create-recruitment/', create_recruitment, name='create-recruitment'),
]
