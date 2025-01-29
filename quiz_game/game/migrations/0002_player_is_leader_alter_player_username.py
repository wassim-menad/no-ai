# Generated by Django 4.1.3 on 2025-01-27 23:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('game', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='player',
            name='is_leader',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='player',
            name='username',
            field=models.CharField(max_length=100),
        ),
    ]
