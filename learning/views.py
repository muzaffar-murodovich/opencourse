from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.views import View

from .models import Lesson, LessonProgress, Skill


# ---------------------------------------------------------------------------
# / (home page — public)
# ---------------------------------------------------------------------------

class HomeView(View):
    template_name = 'home.html'

    def get(self, request):
        skills = Skill.objects.filter(parent__isnull=True).order_by('order')
        return render(request, self.template_name, {'skills': skills})


# ---------------------------------------------------------------------------
# /malaka/ (all top-level skills — requires login)
# ---------------------------------------------------------------------------

class SkillListView(View):
    template_name = 'learning/skill_list.html'

    def get(self, request):
        skills = Skill.objects.filter(parent__isnull=True).order_by('order')
        return render(request, self.template_name, {
            'skills': skills,
            'top_level_skills': skills,
        })


# ---------------------------------------------------------------------------
# /malaka/<parent_slug>/
# ---------------------------------------------------------------------------

class SkillDetailView(LoginRequiredMixin, View):
    template_name = 'learning/skill_detail.html'

    def get(self, request, parent_slug):
        parent_skill = get_object_or_404(
            Skill,
            slug=parent_slug,
            parent__isnull=True,
        )
        top_level_skills = Skill.objects.filter(parent__isnull=True).order_by('order')
        child_skills = (
            parent_skill.children
            .prefetch_related('lessons')
            .order_by('order')
        )
        ctx = {
            'parent_skill': parent_skill,
            'top_level_skills': top_level_skills,
            'child_skills': child_skills,
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# /malaka/<parent_slug>/<child_slug>/
# ---------------------------------------------------------------------------

class NestedSkillDetailView(LoginRequiredMixin, View):
    template_name = 'learning/nested_skill_detail.html'

    def get(self, request, parent_slug, child_slug):
        parent_skill = get_object_or_404(Skill, slug=parent_slug, parent__isnull=True)
        child_skill = get_object_or_404(Skill, slug=child_slug, parent=parent_skill)

        lessons = list(child_skill.lessons.order_by('order'))
        lesson_ids = [lesson.id for lesson in lessons]

        progress_map = {
            p.lesson_id: p
            for p in LessonProgress.objects.filter(
                user=request.user,
                lesson_id__in=lesson_ids,
            )
        }
        # Annotate each lesson with its progress object (or None)
        for lesson in lessons:
            lesson.progress = progress_map.get(lesson.id)

        top_level_skills = Skill.objects.filter(parent__isnull=True).order_by('order')

        ctx = {
            'top_level_skills': top_level_skills,
            'parent_skill': parent_skill,
            'child_skill': child_skill,
            'lessons': lessons,
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# /malaka/<parent_slug>/<child_slug>/<lesson_slug>/
# ---------------------------------------------------------------------------

class LessonDetailView(LoginRequiredMixin, View):
    template_name = 'learning/lesson_detail.html'

    def get(self, request, parent_slug, child_slug, lesson_slug):
        parent_skill = get_object_or_404(Skill, slug=parent_slug, parent__isnull=True)
        child_skill = get_object_or_404(Skill, slug=child_slug, parent=parent_skill)
        lesson = get_object_or_404(Lesson, slug=lesson_slug, skill=child_skill)

        progress, _ = LessonProgress.objects.get_or_create(
            user=request.user, lesson=lesson
        )

        sibling_lessons = list(child_skill.lessons.order_by('order'))
        current_index = next(
            (i for i, l in enumerate(sibling_lessons) if l.id == lesson.id), None
        )
        prev_lesson = sibling_lessons[current_index - 1] if current_index and current_index > 0 else None
        next_lesson = sibling_lessons[current_index + 1] if current_index is not None and current_index < len(sibling_lessons) - 1 else None

        top_level_skills = Skill.objects.filter(parent__isnull=True).order_by('order')
        child_skills = parent_skill.children.order_by('order')

        ctx = {
            'top_level_skills': top_level_skills,
            'child_skills': child_skills,
            'parent_skill': parent_skill,
            'child_skill': child_skill,
            'lesson': lesson,
            'progress': progress,
            'prev_lesson': prev_lesson,
            'next_lesson': next_lesson,
        }
        return render(request, self.template_name, ctx)


# ---------------------------------------------------------------------------
# POST /malaka/<parent_slug>/<child_slug>/<lesson_slug>/complete/
# ---------------------------------------------------------------------------

@login_required
def mark_lesson_complete(request, parent_slug, child_slug, lesson_slug):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    parent_skill = get_object_or_404(Skill, slug=parent_slug, parent__isnull=True)
    child_skill = get_object_or_404(Skill, slug=child_slug, parent=parent_skill)
    lesson = get_object_or_404(Lesson, slug=lesson_slug, skill=child_skill)

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
