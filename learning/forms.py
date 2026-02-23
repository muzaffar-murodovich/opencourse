from django import forms
from django.utils.text import slugify
from .models import Skill, Subskill, Lesson


class SkillForm(forms.ModelForm):
    class Meta:
        model = Skill
        fields = ['title', 'slug', 'description', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('title'):
            cleaned_data['slug'] = slugify(cleaned_data['title'])
        return cleaned_data


class SubskillForm(forms.ModelForm):
    class Meta:
        model = Subskill
        fields = ['title', 'slug', 'description', 'skill', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('title'):
            cleaned_data['slug'] = slugify(cleaned_data['title'])
        return cleaned_data


class LessonForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'slug', 'description', 'subskill', 'youtube_video_id', 'order']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].required = False

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get('slug') and cleaned_data.get('title'):
            cleaned_data['slug'] = slugify(cleaned_data['title'])
        return cleaned_data
