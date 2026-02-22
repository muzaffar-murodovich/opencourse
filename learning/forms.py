from django import forms
from .models import Skill, Subskill, Lesson


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['title', 'slug', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class SubskillForm(forms.ModelForm):
    class Meta:
        model = Subskill
        fields = ['title', 'slug', 'description', 'skill', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'description', 'subskill', 'youtube_video_id', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }