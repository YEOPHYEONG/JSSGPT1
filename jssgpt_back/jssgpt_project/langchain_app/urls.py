# langchain_app/urls.py
from django.urls import path
from .views import create_recruitment, get_recruitment_events, get_recruitment_detail

urlpatterns = [
    path('create-recruitment/', create_recruitment, name='create-recruitment'),
    path('recruitment-events/', get_recruitment_events, name='recruitment-events'),
    path('recruitments/<int:id>/', get_recruitment_detail, name='recruitment-detail'),
]
