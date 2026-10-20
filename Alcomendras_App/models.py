
from django.db import models
from django.contrib.auth.models import User


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='student_appointments'
    )


    assigned_teacher = models.ForeignKey(
    User,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,
    related_name='assigned_appointments'
)

    consultation_title = models.CharField(max_length=150)
    description = models.TextField()
    consultation_date = models.DateField()
    consultation_time = models.TimeField()
    location = models.CharField(max_length=150, blank=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    staff_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['consultation_date', 'consultation_time']

    def __str__(self):
        return f"{self.consultation_title} - {self.student.username}"
