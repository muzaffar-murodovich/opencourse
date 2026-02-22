from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from learning.models import Skill, Subskill, Lesson
from learning.forms import SkillForm, SubskillForm, LessonForm

# Auth views are handled by django.contrib.auth.views (LoginView, LogoutView).


class SignupView(CreateView):
    form_class = UserCreationForm
    template_name = 'users/signup.html'
    success_url = '/users/login/'

    def form_valid(self, form):
        messages.success(self.request, 'Account created successfully! Please log in.')
        return super().form_valid(form)


class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request):
        user = request.user
        form = UserChangeForm(instance=user)
        is_admin = user.is_staff or user.is_superuser
        return render(request, self.template_name, {
            'form': form,
            'is_admin': is_admin,
        })

    def post(self, request):
        user = request.user
        form = UserChangeForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
        return render(request, self.template_name, {
            'form': form,
            'is_admin': user.is_staff or user.is_superuser,
        })


@method_decorator(user_passes_test(lambda u: u.is_staff or u.is_superuser), name='dispatch')
class AdminPanelView(LoginRequiredMixin, View):
    template_name = 'users/admin_panel.html'

    def get(self, request):
        skill_form = SkillForm()
        subskill_form = SubskillForm()
        lesson_form = LessonForm()
        skills = Skill.objects.all()
        return render(request, self.template_name, {
            'skill_form': skill_form,
            'subskill_form': subskill_form,
            'lesson_form': lesson_form,
            'skills': skills,
        })

    def post(self, request):
        if 'add_skill' in request.POST:
            form = SkillForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Skill added successfully.')
                return redirect('users:admin_panel')
        elif 'add_subskill' in request.POST:
            form = SubskillForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Subskill added successfully.')
                return redirect('users:admin_panel')
        elif 'add_lesson' in request.POST:
            form = LessonForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, 'Lesson added successfully.')
                return redirect('users:admin_panel')
        
        # If form invalid, re-render with errors
        skill_form = SkillForm()
        subskill_form = SubskillForm()
        lesson_form = LessonForm()
        skills = Skill.objects.all()
        return render(request, self.template_name, {
            'skill_form': skill_form,
            'subskill_form': subskill_form,
            'lesson_form': lesson_form,
            'skills': skills,
        })
