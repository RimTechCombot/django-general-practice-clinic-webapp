from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import (
    EditAppointmentForm,
    EditUserForm,
    ArchiveForm,
    CategoryForm,
    ChangePasswordForm,
)
from .models import User, Appointment, Archive, Category
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from .forms import AppointmentForm
from django.conf import settings
from django.forms.models import model_to_dict
from django.core.paginator import Paginator
from django.contrib.auth.hashers import make_password, check_password

import datetime

import io


def index(request):
    return render(request=request, template_name="index.html")


@login_required
def accounts(request):
    if request.method == "POST":
        if request.POST.get("Filter"):
            try:
                if request.user.role.role == "admin":
                    users = (
                        User.objects.filter(
                            last_name__icontains=request.POST["Filter"]
                        )
                        .order_by("last_name")
                        .all()
                    )
                elif request.user.role.role == "doctor":
                    users = (
                        User.objects.filter(
                            last_name__icontains=request.POST["Filter"], doctor_id=request.user.id
                        )
                            .order_by("last_name")
                            .all()
                    )
            except User.DoesNotExist:
                users = None
            user_paginator = Paginator(users, 10)
            page_num = 1
            page = user_paginator.get_page(page_num)
            return render(
                request,
                "accounts.html",
                {
                    "page": page,
                    "account": request.POST["Filter"],
                },
            )
        if request.POST.get("Edit user"):
            return redirect(f"/main/accounts/{request.POST['Edit user']}/edit")
        elif request.POST.get("Deactivate user"):
            User.objects.filter(id=request.POST["Deactivate user"]).update(is_active=0)
            return redirect("/main/accounts")
        elif request.POST.get("Activate user"):
            User.objects.filter(id=request.POST["Activate user"]).update(is_active=1)
            return redirect("/main/accounts")
    if request.GET.get("account"):
        try:
            if request.user.role.role == "admin":
                users = (
                    User.objects.filter(last_name__icontains=request.GET["account"])
                        .order_by("last_name")
                        .all()
                )
            elif request.user.role.role == "doctor":
                users = (
                    User.objects.filter(
                        last_name__icontains=request.GET["account"], doctor_id=request.user.id
                    )
                        .order_by("last_name")
                        .all()
                )
        except User.DoesNotExist:
            users = None
    else:
        user = request.user
        if user.role.role == "admin":
            users = User.objects.order_by("last_name").all()
        elif user.role.role == "doctor":
            users = User.objects.filter(doctor_id=user.id).order_by("last_name").all()
        elif user.role.role == "patient":
            users = None
    user_paginator = Paginator(users, 10)
    page_num = request.GET.get("page")
    page = user_paginator.get_page(page_num)
    return render(
        request=request, template_name="accounts.html", context={"page": page, "account": request.GET.get("account")}
    )


@login_required
def no_doctor_list(request):
    all_users = User.objects.filter(doctor__isnull=True, role__role="patient").order_by("last_name")
    user_paginator = Paginator(all_users, 10)
    page_num = request.GET.get("page")
    page = user_paginator.get_page(page_num)
    return render(
        request=request, template_name="no_doctor_list.html", context={"page": page}
    )


@login_required
def account(request, id):
    try:
        user = User.objects.get(id=id)
        if user.role.role == "patient":
            archives = Archive.objects.filter(patient_id=id).order_by("date").all()
            archive_paginator = Paginator(archives, 5)
            page_num = request.GET.get("page")
            page = archive_paginator.get_page(page_num)
            return render(
                request=request,
                template_name="account.html",
                context={"account": user, "page": page},
            )

        elif user.role.role == "doctor" and request.user.role.role == "admin":
            archives = Archive.objects.filter(doctor_id=id).order_by("date").all()
            data = []
            for archive in archives:
                data.append(archive.date.year)
            data = sorted(list(set(data)))
            return render(
                request=request,
                template_name="account.html",
                context={"account": user, "data": data},
            )
        return render(
                request=request,
                template_name="account.html",
                context={"account": user},
            )

    except User.DoesNotExist:
        user = None
        return render(
            request=request, template_name="account.html", context={"account": user}
        )


@login_required
def edit_account(request, id):
    try:
        user = User.objects.get(id=id)
        doctor = user.doctor_id
        if request.method == "POST":
            form = EditUserForm(request.POST, instance=user)
            if form.is_valid():
                if doctor != form.cleaned_data["doctor"].id:
                    send_mail(
                        "Doctor assigned",
                        f"The administrator has assigned a doctor to you.",
                        settings.EMAIL_HOST_USER,
                        [user.email],
                    )
                form.save()
                return redirect(f"/main/accounts/{id}")
            else:
                return render(request, "edit_account.html", {"form": form, "account": user})
        else:
            form = EditUserForm(initial=model_to_dict(user))
            return render(
                request=request,
                template_name="edit_account.html",
                context={"account": user, "form": form},
            )
    except User.DoesNotExist:
        user = None
        return render(
            request=request,
            template_name="edit_account.html",
            context={"account": user},
        )

@login_required
def appointment_pdf(request, id):

    time_dict = {
        0: "09:00 – 09:30",
        1: "10:00 – 10:30",
        2: "11:00 – 11:30",
        3: "12:00 – 12:30",
        4: "13:00 – 13:30",
        5: "14:00 – 14:30",
        6: "15:00 – 15:30",
        7: "16:00 – 16:30",
        8: "17:00 – 17:30",
    }

    appointment_obj = Appointment.objects.get(id=id)
    buffer = io.BytesIO()
    canv = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
    textobj = canv.beginText()
    textobj.setTextOrigin(inch, inch)
    textobj.setFont("Helvetica", 14)

    lines = []
    lines.append(f"Doctor: {str(appointment_obj.doctor)}")
    lines.append(
        f"Appointment date: {str(appointment_obj.date)} at {str(time_dict[appointment_obj.timeslot])}"
    )
    lines.append(f"Patient: {str(appointment_obj.patient)}")
    lines.append(f"Description: {str(appointment_obj.description)}")

    for line in lines:
        textobj.textLine(line)

    canv.drawText(textobj)
    canv.showPage()
    canv.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=True, filename=f"{appointment_obj.patient}-{appointment_obj.date}.pdf")


@login_required
def archive_pdf(request, id):

    archive_obj = Archive.objects.get(id=id)
    buffer = io.BytesIO()
    canv = canvas.Canvas(buffer, pagesize=letter, bottomup=0)
    textobj = canv.beginText()
    textobj.setTextOrigin(inch, inch)
    textobj.setFont("Helvetica", 14)

    lines = []
    lines.append(f"Doctor: {str(archive_obj.doctor)}")
    lines.append(f"Appointment date: {str(archive_obj.date)}")
    lines.append(f"Patient: {str(archive_obj.patient)}")
    lines.append(f"Description: {str(archive_obj.description)}")
    lines.append(f"Doctor's note: {str(archive_obj.doctors_note)}")

    for line in lines:
        textobj.textLine(line)

    canv.drawText(textobj)
    canv.showPage()
    canv.save()
    buffer.seek(0)
    return FileResponse(
        buffer,
        as_attachment=True,
        filename=f"{archive_obj.patient}-{archive_obj.date}.pdf",
    )


@login_required
def appointment(request):
    time_dict = {
        0: "09:00 – 09:30",
        1: "10:00 – 10:30",
        2: "11:00 – 11:30",
        3: "12:00 – 12:30",
        4: "13:00 – 13:30",
        5: "14:00 – 14:30",
        6: "15:00 – 15:30",
        7: "16:00 – 16:30",
        8: "17:00 – 17:30",
    }
    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            if request.POST.get("Schedule"):
                obj = form.save(commit=False)
                obj.doctor_id = request.user.doctor_id
                obj.timeslot = request.POST["Schedule"]
                obj.patient_id = request.user.id
                obj.save()
                return redirect("/main/pending-appointment-list")
            available = {}
            for key in time_dict.keys():
                if not Appointment.objects.filter(
                    date=form.cleaned_data["date"], timeslot=key
                ).exists():
                    available[key] = time_dict[key]
            return render(
                request, "appointment.html", {"form": form, "available": available}
            )
            return redirect("/main")
    else:
        form = AppointmentForm()
    return render(request, "appointment.html", {"form": form})


@login_required
def pending_appointment_list(request):
    time_dict = {
        0: "09:00 – 09:30",
        1: "10:00 – 10:30",
        2: "11:00 – 11:30",
        3: "12:00 – 12:30",
        4: "13:00 – 13:30",
        5: "14:00 – 14:30",
        6: "15:00 – 15:30",
        7: "16:00 – 16:30",
        8: "17:00 – 17:30",
    }
    if request.method == "POST":
        if request.POST.get("Approve appointment"):

            appointment_obj = Appointment.objects.get(
                id=request.POST["Approve appointment"]
            )
            appointment_obj.confirmation = True
            appointment_obj.save()
            send_mail(
                "Appointment approved",
                f"You have an appointemnt scheduled for {appointment_obj.date} at {time_dict[appointment_obj.timeslot]} for {appointment_obj.description}",
                settings.EMAIL_HOST_USER,
                [appointment_obj.patient.email],
            )
            return redirect("/main/pending-appointment-list")
        elif request.POST.get("Reschedule appointment"):
            return redirect(
                f"/main/appointment/{request.POST['Reschedule appointment']}/edit"
            )
        elif request.POST.get("Cancel appointment"):
            Appointment.objects.get(id=request.POST["Cancel appointment"]).delete()
            return redirect("/main/pending-appointment-list")
    else:
        try:
            if request.user.role.role == "doctor":
                appointments = (
                    Appointment.objects.filter(
                        doctor_id=request.user.id, confirmation=False
                    )
                    .order_by("date", "timeslot")
                    .all()
                )
            elif request.user.role.role == "admin":
                appointments = (
                    Appointment.objects.filter(confirmation=False)
                        .order_by("date", "timeslot")
                        .all()
                )
            elif request.user.role.role == "patient":
                appointments = (
                    Appointment.objects.filter(
                        patient_id=request.user.id, confirmation=False
                    )
                    .order_by("date", "timeslot")
                    .all()
                )
        except Appointment.DoesNotExist:
            appointments = None

        appointment_paginator = Paginator(appointments, 10)
        page_num = request.GET.get("page")
        page = appointment_paginator.get_page(page_num)

        return render(
            request,
            "pending_appointment_list.html",
            {"time_dict": time_dict, "page": page},
        )


@login_required
def appointment_list(request):
    time_dict = {
        0: "09:00 – 09:30",
        1: "10:00 – 10:30",
        2: "11:00 – 11:30",
        3: "12:00 – 12:30",
        4: "13:00 – 13:30",
        5: "14:00 – 14:30",
        6: "15:00 – 15:30",
        7: "16:00 – 16:30",
        8: "17:00 – 17:30",
    }
    if request.method == "POST":
        if request.POST.get("Archive"):
            return redirect(f"/main/archive/{request.POST['Archive']}")
        elif request.POST.get("No show"):
            appointment = Appointment.objects.get(id=request.POST["No show"])
            send_mail(
                "Appointment missed",
                f"You have missed an appointment scheduled for {appointment.date} at "
                f"{time_dict[appointment.timeslot]} for {appointment.description}",
                settings.EMAIL_HOST_USER,
                [appointment.patient.email],
            )
            Appointment.objects.get(id=request.POST["No show"]).delete()
        elif request.POST.get("Cancel appointment"):
            appointment = Appointment.objects.get(id=request.POST["Cancel appointment"])
            if request.user.role != "patient":
                send_mail(
                    "Appointment cancelled",
                    f"Your doctor cancelled your appointment scheduled for {appointment.date} at {time_dict[appointment.timeslot]} for {appointment.description}",
                    settings.EMAIL_HOST_USER,
                    [appointment.patient.email],
                )
            Appointment.objects.get(id=request.POST["Cancel appointment"]).delete()
        elif request.POST.get("Filter"):
            try:
                appointments = (
                    Appointment.objects.filter(
                        doctor__last_name=request.POST["Filter"], confirmation=True
                    )
                    .order_by("date", "timeslot")
                    .all()
                )
            except Appointment.DoesNotExist:
                appointments = None
            appointment_paginator = Paginator(appointments, 10)
            page_num = 1
            page = appointment_paginator.get_page(page_num)
            return render(
                request,
                "appointment_list.html",
                {
                    "time_dict": time_dict,
                    "page": page,
                    "filter": request.POST["Filter"],
                },
            )

        return redirect("/main/appointment-list")
    else:
        if request.user.role.role == "doctor":
            if request.GET.get("date", None):
                date = request.GET.get("date")
                try:
                    if date == "today":
                        appointments = (
                            Appointment.objects.filter(date=datetime.date.today(),
                                                       doctor_id=request.user.id,
                                                       confirmation=True)
                            .order_by("timeslot")
                            .all()
                        )
                    elif date == "tomorrow":
                        appointments = (
                            Appointment.objects.filter(
                                date=datetime.date.today() + datetime.timedelta(days=1),
                                doctor_id=request.user.id,
                                confirmation=True
                            )
                            .order_by("timeslot")
                            .all()
                        )
                    elif date == "past":
                        appointments = (
                            Appointment.objects.filter(date__lte=datetime.date.today(),
                                                       doctor_id=request.user.id,
                                                       confirmation=True)
                            .order_by("date", "timeslot")
                            .all()
                        )
                    else:
                        appointments = (
                            Appointment.objects.filter(
                                doctor_id=request.user.id, confirmation=True
                            )
                            .order_by("date", "timeslot")
                            .all()
                        )
                except Appointment.DoesNotExist:
                    appointments = None
            else:
                try:
                    appointments = (
                        Appointment.objects.filter(
                            doctor_id=request.user.id, confirmation=True
                        )
                        .order_by("date", "timeslot")
                        .all()
                    )
                except Appointment.DoesNotExist:
                    appointments = None
        elif request.user.role.role == "admin":
            try:
                if request.GET.get("doctor"):
                    appointments = (
                        Appointment.objects.filter(doctor__last_name=request.GET["doctor"], confirmation=True)
                        .order_by("date", "timeslot")
                        .all()
                    )
                else:
                    appointments = (
                        Appointment.objects.filter(confirmation=True)
                        .order_by("date", "timeslot")
                        .all()
                    )
            except Appointment.DoesNotExist:
                appointments = None
        elif request.user.role.role == "patient":
            try:
                appointments = (
                    Appointment.objects.filter(
                        patient_id=request.user.id, confirmation=True
                    )
                    .order_by("date")
                    .all()
                )
            except Appointment.DoesNotExist:
                appointments = None
        appointment_paginator = Paginator(appointments, 10)
        page_num = request.GET.get("page")
        page = appointment_paginator.get_page(page_num)

        return render(
            request, "appointment_list.html", {"time_dict": time_dict, "page": page,
                                               "filter": request.GET.get("doctor"),
                                               "date": request.GET.get("date")}
        )


@login_required
def edit_appointment(request, id):
    time_dict = {
        0: "09:00 – 09:30",
        1: "10:00 – 10:30",
        2: "11:00 – 11:30",
        3: "12:00 – 12:30",
        4: "13:00 – 13:30",
        5: "14:00 – 14:30",
        6: "15:00 – 15:30",
        7: "16:00 – 16:30",
        8: "17:00 – 17:30",
    }
    if request.method == "POST":
        available = {}
        form = EditAppointmentForm(request.POST)
        obj = Appointment.objects.get(id=id)
        if form.is_valid():
            if request.POST.get("Schedule"):
                obj.reschedule = True
                obj.date = form.cleaned_data["date"]
                obj.timeslot = request.POST["Schedule"]
                obj.save()
                send_mail(
                    "Appointment rescheduled!",
                    f"You have an appointemnt rescheduled, you need to approve it or cancel it!",
                    settings.EMAIL_HOST_USER,
                    [obj.patient.email],
                )
                return redirect("/main/pending-appointment-list")
            for key in time_dict.keys():
                if not Appointment.objects.filter(
                    date=form.cleaned_data["date"], timeslot=key
                ).exists():
                    available[key] = time_dict[key]
            return render(
                request, "edit_appointment.html", {"form": form, "available": available, "appointment": obj}
            )
        else:
            return render(request, "edit_appointment.html", {"form": form, "appointment": obj})
    else:
        try:
            appointment = Appointment.objects.get(id=id)
            form = EditAppointmentForm(initial=model_to_dict(appointment))
        except Appointment.DoesNotExist:
            return redirect("/main/pending-appointment-list")

    return render(
        request, "edit_appointment.html", {"form": form, "appointment": appointment}
    )


@login_required
def reminder(request):
    if request.method == "POST":
        if request.POST.get("Reminder"):
            time_dict = {
                0: "09:00 – 09:30",
                1: "10:00 – 10:30",
                2: "11:00 – 11:30",
                3: "12:00 – 12:30",
                4: "13:00 – 13:30",
                5: "14:00 – 14:30",
                6: "15:00 – 15:30",
                7: "16:00 – 16:30",
                8: "17:00 – 17:30",
            }
            appointments = Appointment.objects.all().filter(confirmation=True)
            today = datetime.date.today()
            for appointment in appointments:
                if today + datetime.timedelta(days=1) >= appointment.date:
                    send_mail(
                        "Appointment reminder",
                        f"You have an appointemnt scheduled for {appointment.date} at {time_dict[appointment.timeslot]} for {appointment.description}",
                        settings.EMAIL_HOST_USER,
                        [appointment.patient.email],
                    )
            return redirect("/main/send-reminder")
        if request.POST.get("Delete"):
            Appointment.objects.filter(confirmation=False,
                                       date__lte=datetime.date.today()).delete()
            return redirect("/main/send-reminder")
    return render(request, "reminder.html", {})


def verify(request, id):
    try:
        user = User.objects.get(id=id)
        if user.is_verified:
            message = "User was already verified."
        else:
            user.is_verified = 1
            user.save()
            message = "Account verified successfully!"
    except Appointment.DoesNotExist:
        message = "That user doesn't exist."
    return render(request, "verify.html", {"message": message})


@login_required
def archive(request, id):
    if request.method == "POST":
        form = ArchiveForm(request.POST)
        if form.is_valid():
            appointment = Appointment.objects.get(id=id)
            obj = form.save(commit=False)
            obj.doctor_id = appointment.doctor_id
            obj.patient_id = appointment.patient_id
            obj.date = appointment.date
            obj.description = appointment.description
            obj.doctors_note = form.cleaned_data["doctors_note"]
            obj.category_id = form.cleaned_data["illness_category"].id
            obj.save()
            Appointment.objects.get(id=id).delete()
            return redirect("/main/appointment-list")
        else:
            return render(request, "archive.html", {"form": form})
    else:
        form = ArchiveForm()
    return render(request, "archive.html", {"form": form})


@login_required
def data(request):
    all_archives = Archive.objects.exclude(category_id__isnull=True)
    data = {}
    illness_categories = Category.objects.all()
    for archive in all_archives:
        if not data.get(archive.date.year):
            data[archive.date.year] = {}
            for i in range(1, 13):
                data[archive.date.year][i] = {}
                for category in illness_categories:
                    data[archive.date.year][i][category.illness_category] = 0
        data[archive.date.year][archive.date.month][
            archive.category.illness_category
        ] += 1

    return render(request, "data.html", {"data": data})


@login_required
def illness_data(request, year):
    all_archives = Archive.objects.filter(date__startswith=year).exclude(category_id__isnull=True)
    data = {}
    illness_categories = Category.objects.all()
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    for i in months:
        data[i] = {}
        for category in illness_categories:
            data[i][category.illness_category] = 0
    for archive in all_archives:
        data[months[archive.date.month-1]][archive.category.illness_category] += 1

    return render(
        request,
        "illness_statistics.html",
        {"data": data, "illness_categories": illness_categories},
    )


@login_required
def category(request):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.illness_category = form.cleaned_data["illness_category"]
            obj.save()
            return redirect("/main/category-list")
        else:
            return render(request, "category.html", {"form": form})
    else:
        form = CategoryForm()
    return render(request, "category.html", {"form": form})


@login_required
def edit_category(request, id):
    if request.method == "POST":
        form = CategoryForm(request.POST)
        if form.is_valid():
            Category.objects.filter(id=id).update(
                illness_category=form.cleaned_data["illness_category"]
            )
            return redirect("/main/category-list")
        else:
            return render(request, "edit_category.html", {"form": form})
    else:
        try:
            category = Category.objects.get(id=id)
            form = CategoryForm(initial=model_to_dict(category))
        except Category.DoesNotExist:
            return redirect("/main/category-list")

    return render(
        request, "edit_category.html", {"form": form, "appointment": appointment}
    )


@login_required
def category_list(request):
    if request.method == "POST":
        if request.POST.get("Filter"):
            try:
                category = (
                    Category.objects.filter(
                        illness_category__icontains=request.POST["Filter"]
                    )
                    .order_by("illness_category")
                    .all()
                )
            except Category.DoesNotExist:
                category = None
            category_paginator = Paginator(category, 10)
            if request.POST.get("Filter"):
                page_num = 1
            else:
                page_num = request.GET.get("page")
            page = category_paginator.get_page(page_num)
            return render(
                request,
                "category_list.html",
                {
                    "page": page,
                    "filter": request.POST["Filter"],
                },
            )

        if request.POST.get("Edit"):
            return redirect(f"/main/category/{request.POST['Edit']}/edit")
        elif request.POST.get("Delete"):
            Category.objects.get(id=request.POST["Delete"]).delete()
            return redirect("/main/category-list")

    if request.GET.get("category"):
        try:
            categories = (
                Category.objects.filter(illness_category__icontains=request.GET["category"])
                    .order_by("illness_category")
                    .all()
            )
        except Category.DoesNotExist:
            categories = None
    else:
        categories = Category.objects.all().order_by("illness_category")
    category_paginator = Paginator(categories, 10)
    page_num = request.GET.get("page")
    page = category_paginator.get_page(page_num)
    return render(
        request=request, template_name="category_list.html", context={"page": page, "filter": request.GET.get("category", None)}
    )


def change_password(request):
    if request.method == "POST":
        form = ChangePasswordForm(request.POST)
        if form.is_valid():
            try:
                user = User.objects.get(username=form.cleaned_data["username"])
                if form.cleaned_data["password"] == form.cleaned_data[
                    "confirm_password"
                ] and (
                    check_password(form.cleaned_data["old_password"], user.password)
                ):
                    user.password = make_password(form.cleaned_data["password"])
                    user.save()
            except User.DoesNotExist:
                return render(request, "change_password.html", {"form": form})
        else:
            return render(request, "change_password.html", {"form": form})
    else:
        form = ChangePasswordForm()
    return render(
        request, "change_password.html", {"form": form, "appointment": appointment}
    )


@login_required
def doctor_archive(request, id, year):
    archives = Archive.objects.filter(date__startswith=year, doctor_id=id)
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        user = None
    data = {}
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
    for i in months:
        data[i] = 0
    for archive in archives:
        data[months[archive.date.month-1]] += 1
    return render(
        request,
        "doctor_archive_graph.html",
        {"data": data, "account": user},
    )