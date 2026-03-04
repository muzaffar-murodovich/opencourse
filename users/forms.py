from django import forms
from django.contrib.auth.models import User


class UserProfileForm(forms.ModelForm):
    """
    Safe user profile form that only allows editing of non-sensitive fields.
    Excludes: password, is_staff, is_active, is_superuser, date_joined, last_login, groups, user_permissions.
    """
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name',
            }),
        }

    def clean_username(self):
        value = self.cleaned_data['username'].strip()
        if User.objects.filter(username=value).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("Bu username band.")
        return value
