from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='telegramauthtoken',
            name='is_new_user',
            field=models.BooleanField(default=False),
        ),
    ]
