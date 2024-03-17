from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth import login, get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.conf import settings
from .forms import RegisterForm, LoginForm
from django.core.mail import send_mail


def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.password = make_password(form.cleaned_data['password'])
            obj.role_id = 3
            obj.is_active = 1
            obj.is_verified = 0
            obj.save()
            send_mail("Activate your account",
                      f"Click this link to activate your account 127.0.0.1:8000/main/verify/{obj.id}",
                      settings.EMAIL_HOST_USER,
                      [form.cleaned_data['email']])
            return redirect("/main/login")
        else:
            return render(request, "register.html", {"form": form})
    else:
        form = RegisterForm()
        return render(request, "register.html", {"form": form})


@login_required
def register_doctor(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.password = make_password(form.cleaned_data['password'])
            obj.role_id = 2
            obj.is_active = 1
            obj.is_verified = 1
            obj.save()
            send_mail("Account details",
                      f"Your username is {form.cleaned_data['username']} and your password is {form.cleaned_data['password']}",
                      settings.EMAIL_HOST_USER,
                      [form.cleaned_data['email']])
            return redirect("/main")
        else:
            return render(request, "registerdoctor.html", {"form": form})
    else:
        form = RegisterForm()
        return render(request, "registerdoctor.html", {"form": form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        username = request.POST['username']
        password = request.POST['password']
        if form.is_valid():
            try:
                db_user = get_user_model().objects.get(username=username)
                if db_user.username == username and check_password(password, db_user.password) and db_user.is_verified and db_user.is_active:
                    login(request, db_user)
                    return redirect("/main")
                else:
                    return render(request, 'login.html', {'form': form})
            except Exception as e:
                return render(request, 'login.html', {'form': form})
        else:
            return render(request, 'login.html', {'form': form})

    else:
        form = LoginForm()
        return render(request, 'login.html', {'form':form})


def logout_view(request):
    if request.user:
        logout(request)
    return redirect("/main/login")