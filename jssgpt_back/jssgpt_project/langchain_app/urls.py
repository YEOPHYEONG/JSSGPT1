# langchain_app/urls.py
from django.urls import path
from .views import create_recruitment, get_recruitment_events, get_recruitment_detail

urlpatterns = [
    path('create-recruitment/', create_recruitment, name='create-recruitment'),
    path('recruitment-events/', get_recruitment_events, name='recruitment-events'),
    path('recruitments/<int:id>/', get_recruitment_detail, name='recruitment-detail'),
]
# 예시: 프로젝트 urls.py의 맨 아래에 추가
from django.views.generic import RedirectView
urlpatterns += [
    path('favicon.ico', RedirectView.as_view(url='/static/favicon.ico')),
]
