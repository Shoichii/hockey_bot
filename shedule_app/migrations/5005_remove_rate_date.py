# Generated by Django 4.2.5 on 2023-11-17 12:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shedule_app', '5004_rate_date_time'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rate',
            name='date',
        ),
    ]