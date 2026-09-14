import random
import string
from django.conf import settings
from django.db import models
from django.utils import timezone
from doctors.models import DoctorProfile


class Slot(models.Model):
    class SlotPeriod(models.TextChoices):
        MORNING = "MORNING", "Morning (09:00 AM - 12:00 PM)"
        AFTERNOON = "AFTERNOON", "Afternoon (12:00 PM - 04:00 PM)"
        EVENING = "EVENING", "Evening (04:00 PM - 08:00 PM)"

    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField(db_index=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_period = models.CharField(max_length=20, choices=SlotPeriod.choices, default=SlotPeriod.MORNING)
    is_booked = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["date", "start_time"]
        unique_together = ("doctor", "date", "start_time")

    def __str__(self):
        return f"{self.doctor.full_name} | {self.date} {self.start_time.strftime('%I:%M %p')} ({'Booked' if self.is_booked else 'Available'})"


def generate_booking_reference():
    today = timezone.now().strftime("%Y%m%d")
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DP-{today}-{suffix}"


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        IN_CONSULTATION = "IN_CONSULTATION", "In-Consultation"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    booking_reference = models.CharField(
        max_length=30,
        unique=True,
        default=generate_booking_reference,
        db_index=True,
        help_text="Unique digital booking reference ID"
    )
    token_number = models.PositiveIntegerField(
        help_text="Sequential queue token number for the doctor's daily roster"
    )
    doctor = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name="appointments")
    patient_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_appointments"
    )
    slot = models.OneToOneField(
        Slot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="appointment"
    )
    appointment_date = models.DateField(db_index=True)
    appointment_time = models.TimeField()
    patient_name = models.CharField(max_length=150)
    patient_phone = models.CharField(max_length=15, db_index=True)
    patient_age = models.PositiveIntegerField(null=True, blank=True)
    patient_gender = models.CharField(
        max_length=10,
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other")],
        default="Male"
    )
    reason_for_visit = models.TextField(blank=True, help_text="Brief description of symptoms or consultation reason")
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.CONFIRMED, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-appointment_date", "appointment_time"]

    def __str__(self):
        return f"Token #{self.token_number:02d} - {self.patient_name} with {self.doctor.full_name} ({self.get_status_display()})"

    @property
    def formatted_token(self):
        return f"#{self.token_number:02d}"
