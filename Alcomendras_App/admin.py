
from django.contrib import admin
from .models import Appointment


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = (
        'consultation_title',
        'student',
        'assigned_teacher',
        'consultation_date',
        'consultation_time',
        'status',
    )

    list_filter = (
        'status',
        'consultation_date',
    )

    search_fields = (
        'consultation_title',
        'student__username',
        'assigned_teacher__username',
    )

    list_editable = ('status',)

    ordering = (
        'consultation_date',
        'consultation_time',
    )
