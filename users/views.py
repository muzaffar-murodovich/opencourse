import json
import re
import requests as http_requests
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils.text import slugify
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


@method_decorator(user_passes_test(lambda u: u.is_staff or u.is_superuser), name='dispatch')
class BulkCreateView(LoginRequiredMixin, View):

    def post(self, request):
        try:
            data = json.loads(request.body)
        except (json.JSONDecodeError, ValueError):
            return JsonResponse({'success': False, 'error': 'Invalid JSON body.'}, status=400)

        skill_title = data.get('title', '').strip()
        if not skill_title:
            return JsonResponse({'success': False, 'error': 'Skill title is required.'}, status=400)

        skill_slug = data.get('slug', '').strip() or slugify(skill_title)

        try:
            with transaction.atomic():
                skill = Skill.objects.create(
                    title=skill_title,
                    slug=skill_slug,
                    description=data.get('description', '').strip(),
                    order=int(data.get('order', 0)),
                )
                for ss_data in data.get('subskills', []):
                    ss_title = ss_data.get('title', '').strip()
                    if not ss_title:
                        raise ValueError('Subskill title is required.')
                    subskill = Subskill.objects.create(
                        title=ss_title,
                        slug=ss_data.get('slug', '').strip() or slugify(ss_title),
                        description=ss_data.get('description', '').strip(),
                        skill=skill,
                        order=int(ss_data.get('order', 0)),
                    )
                    for l_data in ss_data.get('lessons', []):
                        l_title = l_data.get('title', '').strip()
                        if not l_title:
                            raise ValueError('Lesson title is required.')
                        Lesson.objects.create(
                            title=l_title,
                            slug=l_data.get('slug', '').strip() or slugify(l_title),
                            description=l_data.get('description', '').strip(),
                            subskill=subskill,
                            youtube_video_id=l_data.get('youtube_video_id', '').strip(),
                            order=int(l_data.get('order', 0)),
                        )
        except ValueError as exc:
            return JsonResponse({'success': False, 'error': str(exc)}, status=400)
        except Exception as exc:
            return JsonResponse({'success': False, 'error': f'Database error: {exc}'}, status=500)

        return JsonResponse({'success': True, 'skill_id': skill.pk})


@method_decorator(user_passes_test(lambda u: u.is_staff or u.is_superuser), name='dispatch')
class FetchPlaylistView(LoginRequiredMixin, View):

    _PATTERNS = [
        re.compile(r'[?&]list=([A-Za-z0-9_\-]+)'),
        re.compile(r'/playlist/([A-Za-z0-9_\-]+)'),
    ]

    def get(self, request):
        if not settings.YOUTUBE_API_KEY:
            return JsonResponse({'error': 'YOUTUBE_API_KEY is not configured.'}, status=503)

        raw_url = request.GET.get('url', '').strip()
        if not raw_url:
            return JsonResponse({'error': 'url parameter is required.'}, status=400)

        playlist_id = None
        for pat in self._PATTERNS:
            m = pat.search(raw_url)
            if m:
                playlist_id = m.group(1)
                break
        if not playlist_id:
            return JsonResponse({'error': 'Could not extract playlist ID from URL.'}, status=400)

        try:
            resp = http_requests.get(
                'https://www.googleapis.com/youtube/v3/playlistItems',
                params={'part': 'snippet', 'maxResults': 50,
                        'playlistId': playlist_id, 'key': settings.YOUTUBE_API_KEY},
                timeout=10,
            )
            resp.raise_for_status()
            items = resp.json().get('items', [])
        except http_requests.exceptions.Timeout:
            return JsonResponse({'error': 'YouTube API request timed out.'}, status=504)
        except http_requests.exceptions.RequestException as exc:
            return JsonResponse({'error': f'YouTube API error: {exc}'}, status=502)

        results = []
        for item in items:
            snippet = item.get('snippet', {})
            thumbs = snippet.get('thumbnails', {})
            results.append({
                'title': snippet.get('title', ''),
                'video_id': snippet.get('resourceId', {}).get('videoId', ''),
                'description': snippet.get('description', ''),
                'position': snippet.get('position', 0),
                'thumbnail': (thumbs.get('medium') or thumbs.get('default') or {}).get('url', ''),
            })

        playlist_title = ''
        try:
            title_resp = http_requests.get(
                'https://www.googleapis.com/youtube/v3/playlists',
                params={'part': 'snippet', 'id': playlist_id, 'key': settings.YOUTUBE_API_KEY},
                timeout=10,
            )
            title_resp.raise_for_status()
            pl_items = title_resp.json().get('items', [])
            if pl_items:
                playlist_title = pl_items[0].get('snippet', {}).get('title', '')
        except http_requests.exceptions.RequestException:
            pass

        return JsonResponse({'playlist_title': playlist_title, 'items': results})
