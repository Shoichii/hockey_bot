# Generated by Django 4.2.5 on 2023-10-09 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shedule_app', '0021_alter_game_team'),
    ]

    operations = [
        migrations.AddField(
            model_name='journal',
            name='answer_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время ответа'),
        ),
        migrations.AddField(
            model_name='journal',
            name='previuos_answer',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]
