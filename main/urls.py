from django.urls import path

from . import views
from register.views import login_view, logout_view, register, register_doctor

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', register, name='register'),
    path('register-doctor/', register_doctor, name='register-doctor'),
    path('doctorlesslist/', views.no_doctor_list, name='no-doctors-list'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='log-out'),
    path('change-password', views.change_password, name='change-password'),
    path('accounts/', views.accounts, name='accounts'),
    path('accounts/<int:id>/', views.account, name='account'),
    path('accounts/<int:id>/edit', views.edit_account, name='edit-account'),
    path('appointment-pdf/<int:id>', views.appointment_pdf, name='appointment-pdf'),
    path('archive-pdf/<int:id>', views.archive_pdf, name='archive-pdf'),
    path('appointment', views.appointment, name='appointment'),
    path('appointment/<int:id>/edit', views.edit_appointment, name='edit-appointment'),
    path('appointment-list', views.appointment_list, name='appointment-list'),
    path('pending-appointment-list', views.pending_appointment_list, name='pending-appointment-list'),
    path('send-reminder', views.reminder, name='send-reminder'),
    path('verify/<int:id>', views.verify, name='verify'),
    path('archive/<int:id>', views.archive, name='archive'),
    path('illness-data', views.data, name='data'),
    path('illness-data/<int:year>', views.illness_data, name='illness-data'),
    path('category', views.category, name='category'),
    path('category/<int:id>/edit', views.edit_category, name='edit-category'),
    path('category-list', views.category_list, name='category-list'),
    path('doctor-data/<int:id>/<int:year>', views.doctor_archive, name='doctor-data'),


]