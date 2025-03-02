# user_experience/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('upload-resume/', views.upload_resume, name='upload_resume'),
    path('star-experiences/', views.get_star_experiences, name='star_experiences'),
    path('star-experiences/create/', views.create_star_experience, name='create_star_experience'),
    path('star-experiences/<int:star_id>/update/', views.update_star_experience, name='update_star_experience'),
]
