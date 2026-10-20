
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Public homepage
    path('', views.home, name='home'),

    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='home'),
        name='logout',
    ),

    # Student dashboard
    path('dashboard/', views.dashboard, name='dashboard'),

    # Student appointments
    path(
        'appointments/',
        views.appointment_list,
        name='appointment_list',
    ),
    path(
        'appointments/create/',
        views.appointment_create,
        name='appointment_create',
    ),
    path(
        'appointments/<int:pk>/',
        views.appointment_detail,
        name='appointment_detail',
    ),
    path(
        'appointments/<int:pk>/edit/',
        views.appointment_update,
        name='appointment_update',
    ),
    path(
        'appointments/<int:pk>/delete/',
        views.appointment_cancel,
        name='appointment_cancel',
    ),

    # Teacher dashboard and approval workflow
    path(
        'teacher/dashboard/',
        views.teacher_dashboard,
        name='teacher_dashboard',
    ),
    path(
        'teacher/appointments/<int:pk>/',
        views.teacher_appointment_detail,
        name='teacher_appointment_detail',
    ),
    path(
        'teacher/appointments/<int:pk>/update-status/',
        views.teacher_update_status,
        name='teacher_update_status',
    ),

    # Administrator appointment management
    path(
        'management/appointments/',
        views.admin_appointments,
        name='admin_appointments',
    ),
    path(
        'management/appointments/<int:pk>/assign/',
        views.admin_assign_appointment,
        name='admin_assign_appointment',
    ),
]
