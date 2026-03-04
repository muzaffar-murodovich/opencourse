from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [('learning', '0003_lesson_duration_seconds_videosession_videoevent_and_more')]
    operations = [
        migrations.RenameModel('Skill', 'Course'),
        migrations.RenameModel('Subskill', 'Module'),
        migrations.RenameField('Module', 'skill', 'course'),
        migrations.RenameField('Lesson', 'subskill', 'module'),
    ]
