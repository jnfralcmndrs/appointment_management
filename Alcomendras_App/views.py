
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import Group, User
from django.utils import timezone
from django import forms
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

from .models import Appointment


# =========================================================
# FORMS
# =========================================================

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = [
            'consultation_title',
            'description',
            'consultation_date',
            'consultation_time',
            'location',
        ]

        widgets = {
            'consultation_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter consultation title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your concern',
            }),
            'consultation_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'consultation_time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time',
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Office, room, or meeting location',
            }),
        }

    def clean_consultation_date(self):
        consultation_date = self.cleaned_data['consultation_date']

        if consultation_date < timezone.localdate():
            raise forms.ValidationError(
                'Please choose today or a future date.'
            )

        return consultation_date


class AssignTeacherForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['assigned_teacher']

        widgets = {
            'assigned_teacher': forms.Select(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        try:
            teacher_group = Group.objects.get(name='Teacher')
            self.fields['assigned_teacher'].queryset = (
                User.objects.filter(
                    groups=teacher_group,
                    is_active=True,
                ).order_by('username')
            )
        except Group.DoesNotExist:
            self.fields['assigned_teacher'].queryset = User.objects.none()


# =========================================================
# ROLE HELPERS
# =========================================================

def is_teacher(user):
    return (
        user.is_authenticated
        and user.groups.filter(name='Teacher').exists()
    )


def is_admin(user):
    return user.is_authenticated and user.is_superuser


def get_role_redirect(user):
    if is_admin(user):
        return redirect('admin_appointments')

    if is_teacher(user):
        return redirect('teacher_dashboard')

    return redirect('dashboard')


def require_teacher(user):
    if not is_teacher(user):
        raise PermissionDenied(
            'Only authorized teachers can access this page.'
        )


def require_admin(user):
    if not is_admin(user):
        raise PermissionDenied(
            'Only administrators can access this page.'
        )


# =========================================================
# PUBLIC PAGES
# =========================================================

def home(request):
    return render(request, 'StudentAppointment/home.html')


# =========================================================
# AUTHENTICATION
# =========================================================

def register_view(request):
    if request.user.is_authenticated:
        return get_role_redirect(request.user)

    if request.method == 'POST':
        form = UserCreationForm(request.POST)

        if form.is_valid():
            user = form.save()

            # Public registration always creates a student account.
            login(request, user)

            messages.success(
                request,
                'Your student account was created successfully.',
            )
            return redirect('dashboard')
    else:
        form = UserCreationForm()

    return render(
        request,
        'StudentAppointment/register.html',
        {'form': form},
    )


def login_view(request):
    if request.user.is_authenticated:
        return get_role_redirect(request.user)

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)

        if form.is_valid():
            user = form.get_user()
            login(request, user)

            messages.success(
                request,
                'You have logged in successfully.',
            )

            next_url = request.POST.get('next')

            # Avoid redirecting to an external website.
            if (
                next_url
                and next_url.startswith('/')
                and not next_url.startswith('//')
            ):
                return redirect(next_url)

            return get_role_redirect(user)
    else:
        form = AuthenticationForm()

    return render(
        request,
        'StudentAppointment/login.html',
        {
            'form': form,
            'next': request.GET.get('next', ''),
        },
    )


# =========================================================
# STUDENT DASHBOARD
# =========================================================

@login_required
def dashboard(request):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    appointments = Appointment.objects.filter(
        student=request.user
    ).order_by('-created_at')

    context = {
        'appointments': appointments[:5],
        'pending_count': appointments.filter(
            status='pending'
        ).count(),
        'approved_count': appointments.filter(
            status='approved'
        ).count(),
        'completed_count': appointments.filter(
            status='completed'
        ).count(),
    }

    return render(
        request,
        'StudentAppointment/dashboard.html',
        context,
    )


@login_required
def appointment_list(request):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    appointments = Appointment.objects.filter(
        student=request.user
    ).order_by('-created_at')

    return render(
        request,
        'StudentAppointment/appointment_list.html',
        {'appointments': appointments},
    )


@login_required
def appointment_create(request):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    if request.method == 'POST':
        form = AppointmentForm(request.POST)

        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.student = request.user
            appointment.save()

            messages.success(
                request,
                'Your consultation appointment has been submitted.',
            )
            return redirect(
                'appointment_detail',
                pk=appointment.pk,
            )
    else:
        form = AppointmentForm()

    return render(
        request,
        'StudentAppointment/appointment_form.html',
        {'form': form},
    )


@login_required
def appointment_detail(request, pk):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        student=request.user,
    )

    return render(
        request,
        'StudentAppointment/appointment_detail.html',
        {'appointment': appointment},
    )


@login_required
def appointment_update(request, pk):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        student=request.user,
    )

    if appointment.status != 'pending':
        messages.error(
            request,
            'Only pending appointments can be edited.',
        )
        return redirect(
            'appointment_detail',
            pk=appointment.pk,
        )

    if request.method == 'POST':
        form = AppointmentForm(
            request.POST,
            instance=appointment,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Your appointment has been updated.',
            )
            return redirect(
                'appointment_detail',
                pk=appointment.pk,
            )
    else:
        form = AppointmentForm(instance=appointment)

    return render(
        request,
        'StudentAppointment/appointment_form.html',
        {'form': form},
    )


@login_required
@require_POST
def appointment_cancel(request, pk):
    if is_admin(request.user) or is_teacher(request.user):
        return get_role_redirect(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        student=request.user,
    )

    if appointment.status != 'pending':
        messages.error(
            request,
            'Only pending appointments can be cancelled.',
        )
        return redirect(
            'appointment_detail',
            pk=appointment.pk,
        )

    appointment.delete()

    messages.success(
        request,
        'Your appointment has been cancelled.',
    )
    return redirect('appointment_list')


# =========================================================
# TEACHER DASHBOARD
# =========================================================

@login_required
def teacher_dashboard(request):
    require_teacher(request.user)

    appointments = Appointment.objects.filter(
        assigned_teacher=request.user
    ).order_by('consultation_date', 'consultation_time')

    context = {
        'appointments': appointments,
        'pending_count': appointments.filter(
            status='pending'
        ).count(),
        'approved_count': appointments.filter(
            status='approved'
        ).count(),
        'completed_count': appointments.filter(
            status='completed'
        ).count(),
    }

    return render(
        request,
        'StudentAppointment/teacher_dashboard.html',
        context,
    )


@login_required
def teacher_appointment_detail(request, pk):
    require_teacher(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        assigned_teacher=request.user,
    )

    return render(
        request,
        'StudentAppointment/teacher_appointment_detail.html',
        {'appointment': appointment},
    )


@login_required
@require_POST
def teacher_update_status(request, pk):
    require_teacher(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        assigned_teacher=request.user,
    )

    action = request.POST.get('action', '')
    remarks = request.POST.get('staff_remarks', '').strip()

    if action == 'approve':
        if appointment.status != 'pending':
            messages.error(
                request,
                'Only pending appointments can be approved.',
            )
        else:
            appointment.status = 'approved'
            appointment.staff_remarks = remarks
            appointment.save()

            messages.success(
                request,
                'Appointment approved successfully.',
            )

    elif action == 'reject':
        if appointment.status != 'pending':
            messages.error(
                request,
                'Only pending appointments can be rejected.',
            )
        elif not remarks:
            messages.error(
                request,
                'Please provide a reason before rejecting the appointment.',
            )
        else:
            appointment.status = 'rejected'
            appointment.staff_remarks = remarks
            appointment.save()

            messages.success(
                request,
                'Appointment rejected.',
            )

    elif action == 'complete':
        if appointment.status != 'approved':
            messages.error(
                request,
                'Only approved appointments can be marked as completed.',
            )
        else:
            appointment.status = 'completed'

            if remarks:
                appointment.staff_remarks = remarks

            appointment.save()

            messages.success(
                request,
                'Appointment marked as completed.',
            )

    else:
        messages.error(
            request,
            'Invalid appointment action.',
        )

    return redirect(
        'teacher_appointment_detail',
        pk=appointment.pk,
    )


# =========================================================
# ADMINISTRATOR APPOINTMENT MANAGEMENT
# =========================================================

@login_required
def admin_appointments(request):
    require_admin(request.user)

    appointments = Appointment.objects.select_related(
        'student',
        'assigned_teacher',
    ).all().order_by(
        'consultation_date',
        'consultation_time',
    )

    context = {
        'appointments': appointments,
        'pending_count': appointments.filter(
            status='pending'
        ).count(),
        'approved_count': appointments.filter(
            status='approved'
        ).count(),
        'completed_count': appointments.filter(
            status='completed'
        ).count(),
    }

    return render(
        request,
        'StudentAppointment/admin_appointments.html',
        context,
    )


@login_required
def admin_assign_appointment(request, pk):
    require_admin(request.user)

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
    )

    if request.method == 'POST':
        form = AssignTeacherForm(
            request.POST,
            instance=appointment,
        )

        if form.is_valid():
            form.save()

            messages.success(
                request,
                'Teacher assignment updated successfully.',
            )

            return redirect('admin_appointments')
    else:
        form = AssignTeacherForm(instance=appointment)

    return render(
        request,
        'StudentAppointment/admin_assign_appointment.html',
        {
            'form': form,
            'appointment': appointment,
        },
    )
