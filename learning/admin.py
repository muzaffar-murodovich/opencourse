from django.contrib import admin
from .models import Lesson, LessonProgress, Note, Course, Module


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'order']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['order']


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['course', 'order']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'order']
    list_filter = ['module']
    search_fields = ['title']
    prepopulated_fields = {'slug': ('title',)}
    ordering = ['module', 'order']


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'is_completed', 'watched_seconds', 'last_watched_at']
    list_filter = ['is_completed']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['last_watched_at']


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ['user', 'lesson', 'updated_at']
    list_filter = ['lesson__module__course']
    search_fields = ['user__username', 'lesson__title']
    readonly_fields = ['created_at', 'updated_at']
