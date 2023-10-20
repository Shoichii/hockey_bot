# Generated by Django 4.2.5 on 2023-10-20 15:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shedule_app', '0026_game_route'),
    ]

    operations = [
        migrations.AddField(
            model_name='gamejournal',
            name='accept',
            field=models.BooleanField(blank=True, null=True, verbose_name='Запись подтверждена'),
        ),
        migrations.AddField(
            model_name='gamejournal',
            name='answer_time',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время ответа'),
        ),
    ]
