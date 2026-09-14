from datetime import datetime, timedelta
from django.contrib import messages
from django.db import transaction, DatabaseError
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from doctors.models import Department, DoctorProfile
from .models import Slot, Appointment, generate_booking_reference


def home_view(request):
    departments = Department.objects.all()[:8]
    featured_doctors = DoctorProfile.objects.filter(is_verified=True).select_related('department', 'user')[:6]
    return render(request, 'booking/home.html', {
        'departments': departments,
        'featured_doctors': featured_doctors,
    })


def search_view(request):
    query = request.GET.get('q', '').strip()
    dept_id = request.GET.get('dept', '').strip()
    sort_by = request.GET.get('sort', 'rating')

    doctors = DoctorProfile.objects.filter(is_verified=True).select_related('department', 'user')

    # Department filter
    selected_dept = None
    if dept_id:
        if dept_id.isdigit():
            doctors = doctors.filter(department_id=dept_id)
            selected_dept = Department.objects.filter(id=dept_id).first()
        else:
            doctors = doctors.filter(department__slug=dept_id)
            selected_dept = Department.objects.filter(slug=dept_id).first()

    # Search keyword filter (doctor name, specialty, qualification, clinic)
    if query:
        doctors = doctors.filter(
            Q(user__full_name__icontains=query) |
            Q(specialization__icontains=query) |
            Q(qualification__icontains=query) |
            Q(department__name__icontains=query) |
            Q(clinic_name__icontains=query) |
            Q(clinic_address__icontains=query)
        )

    # Sorting
    if sort_by == 'fee_low':
        doctors = doctors.order_by('consultation_fee')
    elif sort_by == 'experience':
        doctors = doctors.order_by('-experience_years')
    else:
        doctors = doctors.order_by('-rating', '-experience_years')

    departments = Department.objects.all()
    today = timezone.localdate()

    return render(request, 'booking/search.html', {
        'doctors': doctors,
        'departments': departments,
        'query': query,
        'dept_id': dept_id,
        'selected_dept': selected_dept,
        'sort_by': sort_by,
        'today': today,
    })


def book_appointment_view(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile.objects.select_related('department', 'user'), id=doctor_id)
    today = timezone.localdate()

    # Date selection
    date_str = request.GET.get('date') or request.POST.get('date')
    if date_str:
        try:
            selected_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            selected_date = today
    else:
        selected_date = today

    # Reject past dates
    if selected_date < today:
        messages.error(request, "Appointments cannot be booked for past dates.")
        selected_date = today

    # Fetch available slots for the selected date
    slots = Slot.objects.filter(doctor=doctor, date=selected_date, is_booked=False).order_by('start_time')
    
    # Group slots by period
    morning_slots = slots.filter(slot_period=Slot.SlotPeriod.MORNING)
    afternoon_slots = slots.filter(slot_period=Slot.SlotPeriod.AFTERNOON)
    evening_slots = slots.filter(slot_period=Slot.SlotPeriod.EVENING)

    # 7-day selector dates
    next_days = [today + timedelta(days=i) for i in range(7)]

    if request.method == 'POST':
        slot_id = request.POST.get('slot_id')
        patient_name = request.POST.get('patient_name', '').strip()
        patient_phone = request.POST.get('patient_phone', '').strip()
        patient_age = request.POST.get('patient_age', '').strip()
        patient_gender = request.POST.get('patient_gender', 'Male')
        reason_for_visit = request.POST.get('reason_for_visit', '').strip()

        if not slot_id:
            messages.error(request, "Please select an available appointment time slot.")
            return render(request, 'booking/book.html', {
                'doctor': doctor,
                'selected_date': selected_date,
                'today': today,
                'next_days': next_days,
                'morning_slots': morning_slots,
                'afternoon_slots': afternoon_slots,
                'evening_slots': evening_slots,
            })

        if not patient_name or not patient_phone:
            messages.error(request, "Patient name and phone number are required.")
            return render(request, 'booking/book.html', {
                'doctor': doctor,
                'selected_date': selected_date,
                'today': today,
                'next_days': next_days,
                'morning_slots': morning_slots,
                'afternoon_slots': afternoon_slots,
                'evening_slots': evening_slots,
            })

        # Atomic transaction with row locking to prevent double booking collision
        try:
            with transaction.atomic():
                # Lock slot record
                slot = Slot.objects.select_for_update().get(id=slot_id, doctor=doctor)

                if slot.is_booked:
                    messages.error(
                        request,
                        "Collision detected: This time slot was just booked by another patient. Please pick another available slot."
                    )
                    return redirect(f"/book/{doctor.id}/?date={selected_date.strftime('%Y-%m-%d')}")

                # Calculate next daily token number for this doctor on this day
                current_tokens = Appointment.objects.filter(
                    doctor=doctor,
                    appointment_date=slot.date
                ).count()
                token_number = current_tokens + 1

                # Parse age
                age_val = int(patient_age) if patient_age and patient_age.isdigit() else None

                # Create appointment record
                appointment = Appointment.objects.create(
                    token_number=token_number,
                    doctor=doctor,
                    patient_user=request.user if request.user.is_authenticated else None,
                    slot=slot,
                    appointment_date=slot.date,
                    appointment_time=slot.start_time,
                    patient_name=patient_name,
                    patient_phone=patient_phone,
                    patient_age=age_val,
                    patient_gender=patient_gender,
                    reason_for_visit=reason_for_visit,
                    consultation_fee=doctor.consultation_fee,
                    status=Appointment.Status.CONFIRMED
                )

                # Mark slot as booked
                slot.is_booked = True
                slot.save()

            messages.success(
                request,
                f"Appointment successfully confirmed! Your Queue Token is #{appointment.token_number:02d}."
            )
            return redirect('appointment_slip', booking_reference=appointment.booking_reference)

        except Slot.DoesNotExist:
            messages.error(request, "The selected time slot does not exist.")
        except DatabaseError as e:
            messages.error(request, f"A database transaction error occurred. Please try again. ({str(e)})")

    # Prefill patient details if user logged in
    initial_name = request.user.full_name if request.user.is_authenticated else ""
    initial_phone = request.user.phone_number if request.user.is_authenticated else ""
    initial_age = request.user.age if (request.user.is_authenticated and request.user.age) else ""
    initial_gender = request.user.gender if (request.user.is_authenticated and request.user.gender) else "Male"

    return render(request, 'booking/book.html', {
        'doctor': doctor,
        'selected_date': selected_date,
        'today': today,
        'next_days': next_days,
        'morning_slots': morning_slots,
        'afternoon_slots': afternoon_slots,
        'evening_slots': evening_slots,
        'initial_name': initial_name,
        'initial_phone': initial_phone,
        'initial_age': initial_age,
        'initial_gender': initial_gender,
    })


def appointment_slip_view(request, booking_reference):
    appointment = get_object_or_404(
        Appointment.objects.select_related('doctor', 'doctor__department', 'doctor__user', 'slot'),
        booking_reference=booking_reference
    )
    return render(request, 'booking/appointment_slip.html', {
        'appointment': appointment,
    })


def track_appointment_view(request):
    lookup_val = request.GET.get('q', '').strip()
    appointments = None

    if lookup_val:
        appointments = Appointment.objects.filter(
            Q(booking_reference__iexact=lookup_val) |
            Q(patient_phone__icontains=lookup_val)
        ).select_related('doctor', 'doctor__department', 'doctor__user').order_by('-appointment_date', 'token_number')
        if not appointments.exists():
            messages.info(request, f"No appointments found matching '{lookup_val}'. Please verify your phone number or booking reference.")

    return render(request, 'booking/track.html', {
        'lookup_val': lookup_val,
        'appointments': appointments,
    })
