from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Skill(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='children',
        on_delete=models.CASCADE,
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent', 'order']),
        ]

    def __str__(self):
        if self.parent:
            return f"{self.parent.title} > {self.title}"
        return self.title


class Lesson(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    description = models.TextField(blank=True)
    skill = models.ForeignKey(
        Skill,
        related_name='lessons',
        on_delete=models.CASCADE,
    )
    youtube_video_id = models.CharField(max_length=20)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        unique_together = [('skill', 'slug')]
        indexes = [
            models.Index(fields=['skill', 'order']),
        ]

    def __str__(self):
        return f"{self.skill.title} – {self.title}"


class LessonProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    watched_seconds = models.PositiveIntegerField(default=0)
    last_watched_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [('user', 'lesson')]

    def __str__(self):
        status = "done" if self.is_completed else "in progress"
        return f"{self.user.username} – {self.lesson.title} ({status})"
