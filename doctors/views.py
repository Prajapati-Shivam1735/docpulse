from datetime import datetime, timedelta, time
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count, Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import DoctorProfile, Department
from booking.models import Appointment, Slot


def doctor_required(view_func):
    """Custom decorator ensuring only logged-in doctors can access doctor views."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in with your doctor credentials to access the Clinic Desk.")
            return redirect('doctor_login')
        if not request.user.is_doctor:
            messages.error(request, "Access restricted. You must be registered as a Doctor to view this page.")
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view


@doctor_required
def doctor_dashboard_view(request):
    try:
        profile = request.user.doctor_profile
    except DoctorProfile.DoesNotExist:
        messages.error(request, "Doctor profile record not found. Please contact support.")
        return redirect('home')

    # Date filter for roster (defaults to today)
    date_str = request.GET.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = timezone.localdate()
    else:
        selected_date = timezone.localdate()

    # Query appointments for the selected date
    appointments = Appointment.objects.filter(
        doctor=profile,
        appointment_date=selected_date
    ).order_by('token_number')

    # Overall & Daily Metrics
    today = timezone.localdate()
    today_appointments = Appointment.objects.filter(doctor=profile, appointment_date=today)
    total_today = today_appointments.count()
    waiting_count = today_appointments.filter(status__in=[Appointment.Status.PENDING, Appointment.Status.CONFIRMED]).count()
    in_consultation_count = today_appointments.filter(status=Appointment.Status.IN_CONSULTATION).count()
    completed_count = today_appointments.filter(status=Appointment.Status.COMPLETED).count()
    
    total_earnings = today_appointments.filter(status=Appointment.Status.COMPLETED).aggregate(
        total=Sum('consultation_fee')
    )['total'] or 0

    # Slots for the selected date
    slots = Slot.objects.filter(doctor=profile, date=selected_date).order_by('start_time')
    open_slots_count = slots.filter(is_booked=False).count()
    booked_slots_count = slots.filter(is_booked=True).count()

    # Upcoming 7 dates for easy date navigation
    date_nav = [today + timedelta(days=i) for i in range(7)]

    return render(request, 'doctors/dashboard.html', {
        'profile': profile,
        'selected_date': selected_date,
        'today': today,
        'appointments': appointments,
        'slots': slots,
        'open_slots_count': open_slots_count,
        'booked_slots_count': booked_slots_count,
        'total_today': total_today,
        'waiting_count': waiting_count,
        'in_consultation_count': in_consultation_count,
        'completed_count': completed_count,
        'total_earnings': total_earnings,
        'date_nav': date_nav,
    })


@doctor_required
def update_appointment_status_view(request, appointment_id):
    if request.method != 'POST':
        return redirect('doctor_dashboard')

    profile = request.user.doctor_profile
    appointment = get_object_or_404(Appointment, id=appointment_id, doctor=profile)
    new_status = request.POST.get('status')

    if new_status in dict(Appointment.Status.choices):
        old_status = appointment.get_status_display()
        appointment.status = new_status
        appointment.save()
        messages.success(
            request,
            f"Token #{appointment.token_number:02d} ({appointment.patient_name}) updated from {old_status} to {appointment.get_status_display()}."
        )
    else:
        messages.error(request, "Invalid status update requested.")

    # Redirect maintaining the appointment date filter
    return redirect(f"{request.POST.get('redirect_to', '') or request.META.get('HTTP_REFERER', 'doctor_dashboard')}")


@doctor_required
def generate_slots_view(request):
    """Allows doctors to quickly generate standard 30-min consultation slots for a day."""
    if request.method == 'POST':
        profile = request.user.doctor_profile
        date_str = request.POST.get('slot_date')
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            messages.error(request, "Invalid date provided for slot generation.")
            return redirect('doctor_dashboard')

        if target_date < timezone.localdate():
            messages.error(request, "Cannot generate slots for past dates.")
            return redirect('doctor_dashboard')

        # Standard schedule: 09:00 AM - 01:00 PM, 04:00 PM - 07:00 PM (30 min slots)
        slot_definitions = [
            (time(9, 0), time(9, 30), Slot.SlotPeriod.MORNING),
            (time(9, 30), time(10, 0), Slot.SlotPeriod.MORNING),
            (time(10, 0), time(10, 30), Slot.SlotPeriod.MORNING),
            (time(10, 30), time(11, 0), Slot.SlotPeriod.MORNING),
            (time(11, 0), time(11, 30), Slot.SlotPeriod.MORNING),
            (time(11, 30), time(12, 0), Slot.SlotPeriod.MORNING),
            (time(12, 0), time(12, 30), Slot.SlotPeriod.AFTERNOON),
            (time(12, 30), time(13, 0), Slot.SlotPeriod.AFTERNOON),
            (time(16, 0), time(16, 30), Slot.SlotPeriod.EVENING),
            (time(16, 30), time(17, 0), Slot.SlotPeriod.EVENING),
            (time(17, 0), time(17, 30), Slot.SlotPeriod.EVENING),
            (time(17, 30), time(18, 0), Slot.SlotPeriod.EVENING),
            (time(18, 0), time(18, 30), Slot.SlotPeriod.EVENING),
            (time(18, 30), time(19, 0), Slot.SlotPeriod.EVENING),
        ]

        created_count = 0
        for start_t, end_t, period in slot_definitions:
            _, created = Slot.objects.get_or_create(
                doctor=profile,
                date=target_date,
                start_time=start_t,
                defaults={'end_time': end_t, 'slot_period': period, 'is_booked': False}
            )
            if created:
                created_count += 1

        messages.success(
            request,
            f"Successfully created {created_count} consultation slots for {target_date.strftime('%b %d, %Y')}."
        )
        return redirect(f"/doctor/dashboard/?date={target_date.strftime('%Y-%m-%d')}")

    return redirect('doctor_dashboard')


@doctor_required
def doctor_profile_edit_view(request):
    profile = request.user.doctor_profile

    if request.method == 'POST':
        profile.qualification = request.POST.get('qualification', profile.qualification).strip()
        profile.specialization = request.POST.get('specialization', profile.specialization).strip()
        try:
            profile.experience_years = int(request.POST.get('experience_years', profile.experience_years))
            profile.consultation_fee = float(request.POST.get('consultation_fee', profile.consultation_fee))
        except (ValueError, TypeError):
            pass
        profile.clinic_name = request.POST.get('clinic_name', profile.clinic_name).strip()
        profile.clinic_address = request.POST.get('clinic_address', profile.clinic_address).strip()
        profile.bio = request.POST.get('bio', profile.bio).strip()
        profile.working_hours = request.POST.get('working_hours', profile.working_hours).strip()
        profile.available_days = request.POST.get('available_days', profile.available_days).strip()
        
        # User details
        full_name = request.POST.get('full_name', '').strip()
        if full_name:
            profile.user.full_name = full_name
            profile.user.save()

        profile.save()
        messages.success(request, "Clinic profile and fees updated successfully.")
        return redirect('doctor_dashboard')

    return render(request, 'doctors/profile_edit.html', {'profile': profile})
