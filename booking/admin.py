from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from accounts.models import User, UserProfile
from doctors.models import Department, DoctorProfile
from .models import Slot, Appointment


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('phone_number', 'full_name', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('phone_number', 'full_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('phone_number', 'password')}),
        ('Personal Info', {'fields': ('full_name', 'email', 'gender', 'age', 'role')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone_number', 'full_name', 'role', 'password', 'confirm_password'),
        }),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'icon', 'is_popular', 'display_order')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_popular', 'display_order')
    search_fields = ('name',)


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'department', 'qualification', 'consultation_fee', 'is_verified', 'rating')
    list_filter = ('is_verified', 'department', 'city')
    search_fields = ('user__full_name', 'user__phone_number', 'specialization', 'clinic_name')
    list_editable = ('is_verified', 'consultation_fee')
    actions = ['mark_as_verified']

    def mark_as_verified(self, request, queryset):
        queryset.update(is_verified=True)
        self.message_user(request, "Selected doctor profiles were marked as verified.")
    mark_as_verified.short_description = "Verify selected doctors"


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'slot_period', 'is_booked')
    list_filter = ('date', 'slot_period', 'is_booked')
    search_fields = ('doctor__user__full_name', 'doctor__user__phone_number')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'token_number', 'patient_name', 'patient_phone', 'doctor', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('booking_reference', 'patient_name', 'patient_phone', 'doctor__user__full_name')
    readonly_fields = ('booking_reference', 'created_at', 'updated_at')
