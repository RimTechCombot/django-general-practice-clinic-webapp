from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from datetime import date
from django.forms.widgets import DateInput


class RegisterForm(ModelForm):
    email = forms.EmailField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=50)
    date_of_birth = forms.DateInput()


    def clean_date_of_birth(self):
        date_of_birth = self.cleaned_data['date_of_birth']
        if date_of_birth > date.today():
            raise forms.ValidationError("Must be a past date!")
        return date_of_birth

    class Meta:
        model = get_user_model()
        fields = ["username", "first_name", "last_name", "email", "password", "date_of_birth", "sex"]
        widgets = {
            'date_of_birth': DateInput(attrs={'type': 'date'}, ),
        }

class LoginForm(forms.Form):
    username = forms.CharField(max_length=50)
    password = forms.CharField(widget=forms.PasswordInput(), max_length=50)

    class Meta:
        fields = ['username', 'password']
