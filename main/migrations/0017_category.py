# Generated by Django 4.0.4 on 2022-07-29 19:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0016_user_is_verified'),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('illness_category', models.CharField(max_length=50)),
            ],
        ),
    ]