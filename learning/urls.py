from django.urls import path
from . import views

app_name = 'learning'

urlpatterns = [
    path(
        '',
        views.SkillListView.as_view(),
        name='skill_list',
    ),
    path(
        '<slug:skill_slug>/',
        views.SkillDetailView.as_view(),
        name='skill_detail',
    ),
    path(
        '<slug:skill_slug>/<slug:subskill_slug>/',
        views.SubskillDetailView.as_view(),
        name='subskill_detail',
    ),
    path(
        '<slug:skill_slug>/<slug:subskill_slug>/<slug:lesson_slug>/',
        views.LessonDetailView.as_view(),
        name='lesson_detail',
    ),
    path(
        '<slug:skill_slug>/<slug:subskill_slug>/<slug:lesson_slug>/complete/',
        views.mark_lesson_complete,
        name='mark_complete',
    ),
]
