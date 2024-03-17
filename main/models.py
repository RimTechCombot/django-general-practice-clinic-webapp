from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.Model):
    role = models.CharField(max_length=50)


class Category(models.Model):
    illness_category = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.illness_category}"


class User(AbstractUser):

    SEX_LIST = (
        ("M", "M"),
        ("F", "F"),
    )
    username = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    password = models.CharField(max_length=200)
    date_of_birth = models.DateField(null=True)
    sex = models.CharField(max_length=10, choices=SEX_LIST, null=True)
    is_verified = models.BooleanField(default=False)
    role = models.ForeignKey(Role, null=True, on_delete=models.SET_NULL)
    doctor = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Appointment(models.Model):
    class Meta:
        unique_together = ('doctor', 'date', 'timeslot')

    TIMESLOT_LIST = (
        (0, '09:00 – 09:30'),
        (1, '10:00 – 10:30'),
        (2, '11:00 – 11:30'),
        (3, '12:00 – 12:30'),
        (4, '13:00 – 13:30'),
        (5, '14:00 – 14:30'),
        (6, '15:00 – 15:30'),
        (7, '16:00 – 16:30'),
        (8, '17:00 – 17:30'),
    )

    doctor = models.ForeignKey('User', on_delete=models.CASCADE, limit_choices_to={'role_id': '2'})
    date = models.DateField(help_text="DD-MM-YYYY")
    timeslot = models.IntegerField(choices=TIMESLOT_LIST)
    description = models.TextField(max_length=200)
    patient = models.ForeignKey('User', on_delete=models.CASCADE, related_name="patient")
    confirmation = models.BooleanField(default=False)
    reschedule = models.BooleanField(default=False)


class Archive(models.Model):

    doctor = models.ForeignKey('User', on_delete=models.CASCADE, limit_choices_to={'role_id': '2'})
    date = models.DateField(help_text="DD-MM-YYYY")
    description = models.TextField(max_length=200)
    patient = models.ForeignKey('User', on_delete=models.CASCADE, related_name="patient_archive")
    doctors_note = models.TextField(max_length=500)
    category = models.ForeignKey(Category, null=True, on_delete=models.SET_NULL)

