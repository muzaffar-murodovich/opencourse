from django.contrib import admin
from .models import Lesson, LessonProgress, Skill, Subskill


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order']


@admin.register(Subskill)
class SubskillAdmin(admin.ModelAdmin):
    list_display = ['title', 'skill', 'order']
    list_filter = ['skill']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['skill', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'subskill', 'order']
    list_filter = ['subskill']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['subskill', 'order']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'watched_seconds', 'last_watched_at']
    list_filter = ['is_completed']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['last_watched_at']
