from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import User as MyUser, Role, Appointment, Archive, Category
from datetime import date
from django.contrib.auth import get_user_model
from django.forms.widgets import DateInput


class RegisterForm(UserCreationForm):

    sex = forms.CharField(max_length=10)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'sex']


class EditUserForm(ModelForm):
    email = forms.CharField(max_length=50)
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    date_of_birth = forms.DateInput()
    doctor = forms.ModelChoiceField(queryset=get_user_model().objects.all().filter(role_id=2))

    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        if date_of_birth > date.today():
            raise forms.ValidationError("Must be a past date!")
        return date_of_birth

    class Meta:
        model = get_user_model()
        fields = ["email", "first_name", "last_name", "date_of_birth", "sex", "doctor"]
        widgets = {
            'date_of_birth': DateInput(attrs={'type': 'date'}, ),
        }


class RoleForm(ModelForm):
    role = forms.CharField(max_length=50)

    class Meta:
        model = Role
        fields = ['role']


class CategoryForm(ModelForm):
    illness_category = forms.CharField(max_length=50)

    class Meta:
        model = Category
        fields = ['illness_category']


class ChangePasswordForm(forms.Form):
    username = forms.CharField(max_length=50)
    old_password = forms.CharField(widget=forms.PasswordInput(), max_length=50)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=50)
    confirm_password = forms.CharField(widget=forms.PasswordInput(), max_length=50)

    class Meta:
        fields = ['username', 'old_password', 'password', 'confirm_password']


class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=50)

    class Meta:
        fields = ['username', 'password']


class AppointmentForm(forms.ModelForm):

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < date.today():
            raise forms.ValidationError("The date cannot be in the past!")
        if date.weekday() > 4:
            raise forms.ValidationError("Date cannot be a weekend!")
        return date

    class Meta:
        model = Appointment
        fields = ('date', 'description')
        widgets = {
            'date': DateInput(attrs={'type': 'date'},),

        }


class EditAppointmentForm(forms.ModelForm):

    def clean_date(self):
        date = self.cleaned_data['date']
        if date < date.today():
            raise forms.ValidationError("The date cannot be in the past!")
        if date.weekday() > 4:
            raise forms.ValidationError("Date cannot be a weekend!")
        return date

    class Meta:
        model = Appointment
        fields = ('date',)
        widgets = {
            'date': DateInput(attrs={'type': 'date'})

        }


class ArchiveForm(forms.ModelForm):
    illness_category = forms.ModelChoiceField(queryset=Category.objects.all())

    class Meta:
        model = Archive
        fields = ['illness_category', 'doctors_note']


