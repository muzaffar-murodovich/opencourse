from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse
from django.contrib.auth.decorators import user_passes_test
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from learning.models import Skill, Subskill, Lesson
from learning.forms import SkillForm, SubskillForm, LessonForm
from .forms import UserProfileForm

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
        form = UserProfileForm(instance=user)
        is_admin = user.is_staff or user.is_superuser
        return render(request, self.template_name, {
            'form': form,
            'is_admin': is_admin,
            'user': user,
        })

    def post(self, request):
        user = request.user
        form = UserProfileForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('users:profile')
        is_admin = user.is_staff or user.is_superuser
        return render(request, self.template_name, {
            'form': form,
            'is_admin': is_admin,
            'user': user,
        })


@method_decorator(user_passes_test(lambda u: u.is_staff or u.is_superuser), name='dispatch')
class AdminPanelView(LoginRequiredMixin, View):
    template_name = 'users/admin_panel.html'

    def _context(self, skill_form=None, subskill_form=None, lesson_form=None, active_tab='skill'):
        return {
            'skill_form': skill_form or SkillForm(prefix='skill'),
            'subskill_form': subskill_form or SubskillForm(prefix='subskill'),
            'lesson_form': lesson_form or LessonForm(prefix='lesson'),
            'skills': Skill.objects.prefetch_related('subskills__lessons').all(),
            'active_tab': active_tab,
        }

    def get(self, request):
        return render(request, self.template_name, self._context())

    def post(self, request):
        if 'add_skill' in request.POST:
            form = SkillForm(request.POST, prefix='skill')
            if form.is_valid():
                form.save()
                messages.success(request, 'Skill added successfully.')
                return redirect('users:admin_panel')
            return render(request, self.template_name, self._context(skill_form=form, active_tab='skill'))
        elif 'add_subskill' in request.POST:
            form = SubskillForm(request.POST, prefix='subskill')
            if form.is_valid():
                form.save()
                messages.success(request, 'Subskill added successfully.')
                return redirect('users:admin_panel')
            return render(request, self.template_name, self._context(subskill_form=form, active_tab='subskill'))
        elif 'add_lesson' in request.POST:
            form = LessonForm(request.POST, prefix='lesson')
            if form.is_valid():
                form.save()
                messages.success(request, 'Lesson added successfully.')
                return redirect('users:admin_panel')
            return render(request, self.template_name, self._context(lesson_form=form, active_tab='lesson'))
        return render(request, self.template_name, self._context())
