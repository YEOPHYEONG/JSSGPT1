from django import forms
from .models import RawExperience

class ResumeUploadForm(forms.ModelForm):
    class Meta:
        model = RawExperience
        fields = ['resume_file']