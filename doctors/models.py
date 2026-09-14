from django.conf import settings
from django.db import models
from django.utils.text import slugify


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    icon = models.CharField(max_length=50, default="fa-stethoscope", help_text="FontAwesome icon class name")
    description = models.TextField(blank=True)
    is_popular = models.BooleanField(default=True)
    display_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["display_order", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="doctors"
    )
    qualification = models.CharField(max_length=150, help_text="e.g. MBBS, MD, MS")
    specialization = models.CharField(max_length=150, help_text="e.g. Cardiologist, Dermatologist")
    experience_years = models.PositiveIntegerField(default=5)
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)
    clinic_name = models.CharField(max_length=200, default="DocPulse Care Clinic")
    clinic_address = models.TextField(default="123 Health Ave, Medical District")
    city = models.CharField(max_length=100, default="Mumbai")
    bio = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    total_reviews = models.PositiveIntegerField(default=48)
    is_verified = models.BooleanField(default=True, help_text="Doctor verification status")
    available_days = models.CharField(max_length=100, default="Monday - Saturday")
    working_hours = models.CharField(max_length=100, default="09:00 AM - 05:00 PM")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-rating", "-experience_years"]

    def __str__(self):
        doc_name = self.user.full_name or f"Dr. {self.user.phone_number}"
        return f"{doc_name} ({self.department.name if self.department else 'Specialist'})"

    @property
    def full_name(self):
        if self.user.full_name:
            if not self.user.full_name.lower().startswith("dr."):
                return f"Dr. {self.user.full_name}"
            return self.user.full_name
        return f"Dr. {self.user.phone_number}"
