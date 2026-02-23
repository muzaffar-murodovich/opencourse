import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.safestring import mark_safe
from django.views import View

from .models import Lesson, LessonProgress, Note, Skill, Subskill
from .utils import render_markdown


# ---------------------------------------------------------------------------
# / (home page — public)
# ---------------------------------------------------------------------------

class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        skills = Skill.objects.all()
        return render(request, self.template_name, {'skills': skills})


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
    return JsonResponse({'status': 'ok'})
