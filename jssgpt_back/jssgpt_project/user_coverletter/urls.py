# user_coverletter/urls.py
from django.urls import path
from . import views

app_name = 'user_coverletter'

urlpatterns = [
    path('create/<int:recruit_job_id>/', views.create_cover_letter, name='create_cover_letter'),
    path('generate-draft/<int:recruit_job_id>/', views.generate_cover_letter_draft, name='generate_cover_letter_draft'),
    path('edit/<int:pk>/', views.edit_cover_letter, name='edit_cover_letter'),
    path('get/', views.get_user_coverletters, name='get_user_coverletters'),
    path('list/', views.list_cover_letters, name='list_cover_letters'),
    path('update-content/', views.update_cover_letter_content, name='update_cover_letter_content'),
]
