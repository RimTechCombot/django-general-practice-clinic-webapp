# Generated by Django 4.0.4 on 2022-07-16 11:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0014_delete_archive'),
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(help_text='DD-MM-YYYY')),
                ('description', models.TextField(max_length=200)),
                ('doctors_note', models.TextField(max_length=500)),
                ('doctor', models.ForeignKey(limit_choices_to={'role_id': '2'}, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_archive', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]