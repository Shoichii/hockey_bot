# Generated by Django 4.2.5 on 2023-10-10 17:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shedule_app', '0023_alter_user_telegram_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='rate',
            name='address',
            field=models.CharField(max_length=150, verbose_name='Адрес проведения'),
        ),
        migrations.AlterField(
            model_name='rate',
            name='place',
            field=models.CharField(max_length=100, verbose_name='Место'),
        ),
    ]
