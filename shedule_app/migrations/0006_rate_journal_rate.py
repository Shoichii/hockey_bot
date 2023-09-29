# Generated by Django 4.2.5 on 2023-09-20 13:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shedule_app', '0005_alter_user_birthday'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата')),
                ('place', models.CharField(max_length=20, verbose_name='Место')),
                ('address', models.CharField(max_length=20, verbose_name='Адрес проведения')),
                ('rate', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Оценка Тренировки',
                'verbose_name_plural': 'Оценки Тренировок',
            },
        ),
        migrations.AddField(
            model_name='journal',
            name='rate',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
