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
        '<slug:parent_slug>/',
        views.SkillDetailView.as_view(),
        name='skill_detail',
    ),
    path(
        '<slug:parent_slug>/<slug:child_slug>/',
        views.NestedSkillDetailView.as_view(),
        name='nested_skill_detail',
    ),
    path(
        '<slug:parent_slug>/<slug:child_slug>/<slug:lesson_slug>/',
        views.LessonDetailView.as_view(),
        name='lesson_detail',
    ),
    path(
        '<slug:parent_slug>/<slug:child_slug>/<slug:lesson_slug>/complete/',
        views.mark_lesson_complete,
        name='mark_complete',
    ),
]
