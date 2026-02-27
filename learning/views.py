import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import Lesson, LessonProgress, Note, Skill, Subskill, VideoEvent, VideoSession
from .utils import render_markdown

User = get_user_model()


# ---------------------------------------------------------------------------
# / (home page — public)
# ---------------------------------------------------------------------------

class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        skills = Skill.objects.all()
        total_seconds = (
            VideoSession.objects.aggregate(Sum('actual_watched_seconds'))
            ['actual_watched_seconds__sum'] or 0
        )
        total_hours = round(total_seconds / 3600)
        total_users = User.objects.filter(is_active=True).count()
        total_lessons = Lesson.objects.count()
        return render(request, self.template_name, {
            'skills': skills,
            'total_hours': total_hours,
            'total_users': total_users,
            'total_lessons': total_lessons,
        })


# ---------------------------------------------------------------------------
# /malaka/ (all skills — public)
# ---------------------------------------------------------------------------

class SkillListView(View):
    template_name = 'learning/skill_list.html'

    def get(self, request):
        skills = Skill.objects.all()
        return render(request, self.template_name, {
            'skills': skills,
        })


# ---------------------------------------------------------------------------
# /malaka/<skill_slug>/
# ---------------------------------------------------------------------------

class SkillDetailView(LoginRequiredMixin, View):
    template_name = 'learning/skill_detail.html'

    def get(self, request, skill_slug):
        skill = get_object_or_404(Skill, slug=skill_slug)
        subskills = (
            skill.subskills
            .prefetch_related('lessons')
            .order_by('order')
        )
        ctx = {
            'skill': skill,
            'subskills': subskills,
            'show_sidebar': True,
            'sidebar_skill': skill,
            'sidebar_subskills': subskills,
            'current_subskill': None,
            'current_lesson': None,
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# /malaka/<skill_slug>/<subskill_slug>/
# ---------------------------------------------------------------------------

class SubskillDetailView(LoginRequiredMixin, View):
    template_name = 'learning/subskill_detail.html'

    def get(self, request, skill_slug, subskill_slug):
        skill = get_object_or_404(Skill, slug=skill_slug)
        subskill = get_object_or_404(Subskill, slug=subskill_slug, skill=skill)

        lessons = list(subskill.lessons.order_by('order'))
        lesson_ids = [lesson.id for lesson in lessons]

        progress_map = {
            p.lesson_id: p
            for p in LessonProgress.objects.filter(
                user=request.user,
                lesson_id__in=lesson_ids,
            )
        }
        for lesson in lessons:
            lesson.progress = progress_map.get(lesson.id)

        sidebar_subskills = skill.subskills.prefetch_related('lessons').order_by('order')

        ctx = {
            'skill': skill,
            'subskill': subskill,
            'lessons': lessons,
            'show_sidebar': True,
            'sidebar_skill': skill,
            'sidebar_subskills': sidebar_subskills,
            'current_subskill': subskill,
            'current_lesson': None,
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/
# ---------------------------------------------------------------------------

class LessonDetailView(LoginRequiredMixin, View):
    template_name = 'learning/lesson_detail.html'

    def get(self, request, skill_slug, subskill_slug, lesson_slug):
        skill = get_object_or_404(Skill, slug=skill_slug)
        subskill = get_object_or_404(Subskill, slug=subskill_slug, skill=skill)
        lesson = get_object_or_404(Lesson, slug=lesson_slug, subskill=subskill)

        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user, lesson=lesson
        )

        sibling_lessons = list(subskill.lessons.order_by('order'))
        current_index = next(
            (i for i, l in enumerate(sibling_lessons) if l.id == lesson.id), None
        )
        prev_lesson = sibling_lessons[current_index - 1] if current_index and current_index > 0 else None
        next_lesson = sibling_lessons[current_index + 1] if current_index is not None and current_index < len(sibling_lessons) - 1 else None

        sidebar_subskills = skill.subskills.prefetch_related('lessons').order_by('order')

        note = Note.objects.filter(user=request.user, lesson=lesson).first()

        ctx = {
            'skill': skill,
            'subskill': subskill,
            'lesson': lesson,
            'progress': progress,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
            'show_sidebar': True,
            'sidebar_skill': skill,
            'sidebar_subskills': sidebar_subskills,
            'current_subskill': subskill,
            'current_lesson': lesson,
            'lesson_description_html': mark_safe(render_markdown(lesson.description)),
            'note': note,
            'note_rendered': mark_safe(render_markdown(note.content)) if note and note.content else '',
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# POST /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/complete/
# ---------------------------------------------------------------------------

@login_required
def mark_lesson_complete(request, skill_slug, subskill_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    skill = get_object_or_404(Skill, slug=skill_slug)
    subskill = get_object_or_404(Subskill, slug=subskill_slug, skill=skill)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, subskill=subskill)

    progress, _ = LessonProgress.objects.get_or_create(
        user=request.user, lesson=lesson
    )
    progress.is_completed = True
    progress.save()

    return JsonResponse({
        'status': 'ok',
        'is_completed': progress.is_completed,
        'lesson_id': lesson.id,
    })


# ---------------------------------------------------------------------------
# POST /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/note/
# ---------------------------------------------------------------------------

@login_required
def save_note(request, skill_slug, subskill_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    skill = get_object_or_404(Skill, slug=skill_slug)
    subskill = get_object_or_404(Subskill, slug=subskill_slug, skill=skill)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, subskill=subskill)

    try:
        content = json.loads(request.body).get('content', '')
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    Note.objects.update_or_create(
        user=request.user,
        lesson=lesson,
        defaults={'content': content},
    )
    rendered = render_markdown(content)
    return JsonResponse({'status': 'ok', 'rendered': rendered})


# ---------------------------------------------------------------------------
# Session tracking helpers
# ---------------------------------------------------------------------------

def _get_lesson(skill_slug, subskill_slug, lesson_slug):
    skill = get_object_or_404(Skill, slug=skill_slug)
    subskill = get_object_or_404(Subskill, slug=subskill_slug, skill=skill)
    return get_object_or_404(Lesson, slug=lesson_slug, subskill=subskill)


def _recalculate_watched(session):
    """Update session.actual_watched_seconds from play/pause event intervals (does not save)."""
    events = list(session.events.order_by('created_at'))
    total = 0.0
    play_start = None
    for ev in events:
        if ev.event_type == 'play':
            play_start = ev.position_seconds
        elif ev.event_type in ('pause', 'ended', 'page_hidden') and play_start is not None:
            diff = ev.position_seconds - play_start
            if diff > 0:
                total += diff
            play_start = None
        elif ev.event_type == 'seek' and play_start is not None:
            diff = ev.position_seconds - play_start
            if diff > 0:
                total += diff
            play_start = None
    session.actual_watched_seconds = int(total)


def _maybe_auto_complete(session, lesson):
    """Set LessonProgress.is_completed if 80% watched. Returns True if newly completed."""
    if not lesson.duration_seconds:
        return False
    if session.actual_watched_seconds < lesson.duration_seconds * 0.8:
        return False
    progress, _ = LessonProgress.objects.get_or_create(user=session.user, lesson=lesson)
    if not progress.is_completed:
        progress.is_completed = True
        progress.save(update_fields=['is_completed'])
        return True
    return False


def _handle_session_event(request, lesson, data):
    """Shared logic for session/event/ and session/beacon/ endpoints."""
    session = get_object_or_404(
        VideoSession, id=data.get('session_id'), user=request.user, lesson=lesson
    )
    event_type = data.get('event_type', '')
    position = int(data.get('position_seconds', 0))
    metadata = data.get('metadata') or {}

    VideoEvent.objects.create(
        session=session,
        event_type=event_type,
        position_seconds=position,
        metadata=metadata,
    )

    _recalculate_watched(session)
    session.last_position_seconds = position
    session.max_reached_seconds = max(position, session.max_reached_seconds)
    save_fields = ['actual_watched_seconds', 'last_position_seconds', 'max_reached_seconds']
    if event_type in ('ended', 'page_hidden'):
        session.ended_at = timezone.now()
        save_fields.append('ended_at')
    session.save(update_fields=save_fields)

    LessonProgress.objects.filter(user=request.user, lesson=lesson).update(
        watched_seconds=session.actual_watched_seconds
    )

    auto_completed = _maybe_auto_complete(session, lesson)
    return JsonResponse({'status': 'ok', 'auto_completed': auto_completed})


# ---------------------------------------------------------------------------
# POST /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/session/start/
# ---------------------------------------------------------------------------

@login_required
def session_start(request, skill_slug, subskill_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = _get_lesson(skill_slug, subskill_slug, lesson_slug)

    try:
        data = json.loads(request.body) if request.body else {}
    except (json.JSONDecodeError, ValueError):
        data = {}

    duration = data.get('duration_seconds')
    if duration and not lesson.duration_seconds:
        lesson.duration_seconds = int(duration)
        lesson.save(update_fields=['duration_seconds'])

    now = timezone.now()
    resume_threshold = now - timedelta(minutes=30)

    session = VideoSession.objects.filter(
        user=request.user, lesson=lesson, ended_at__isnull=True
    ).first()

    if not session:
        session = VideoSession.objects.filter(
            user=request.user, lesson=lesson, ended_at__gte=resume_threshold
        ).order_by('-ended_at').first()
        if session:
            session.ended_at = None
            session.save(update_fields=['ended_at'])
        else:
            session = VideoSession.objects.create(user=request.user, lesson=lesson)

    return JsonResponse({'session_id': session.id, 'last_position': session.last_position_seconds})


# ---------------------------------------------------------------------------
# POST /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/session/event/
# ---------------------------------------------------------------------------

@login_required
def session_event(request, skill_slug, subskill_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    lesson = _get_lesson(skill_slug, subskill_slug, lesson_slug)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    return _handle_session_event(request, lesson, data)


# ---------------------------------------------------------------------------
# POST /malaka/<skill_slug>/<subskill_slug>/<lesson_slug>/session/beacon/
# ---------------------------------------------------------------------------

@csrf_exempt
def session_beacon(request, skill_slug, subskill_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Unauthorized'}, status=401)

    lesson = _get_lesson(skill_slug, subskill_slug, lesson_slug)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid data'}, status=400)

    return _handle_session_event(request, lesson, data)
