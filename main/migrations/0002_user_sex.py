# Generated by Django 4.0.4 on 2022-06-04 22:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='sex',
            field=models.CharField(blank=True, max_length=30),
        ),
    ]
