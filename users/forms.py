from django import forms
from django.contrib.auth.models import User


class UserProfileForm(forms.ModelForm):
    """
    Safe user profile form that only allows editing of non-sensitive fields.
    Excludes: password, is_staff, is_active, is_superuser, date_joined, last_login, groups, user_permissions.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address',
            }),
        }
