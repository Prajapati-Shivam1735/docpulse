from datetime import time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from doctors.models import Department, DoctorProfile
from booking.models import Slot, Appointment


class DoctorsModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="General Medicine", slug="general-medicine")
        
        # Doctor User
        self.doc_user = User.objects.create_user(
            phone_number="9988776655",
            password="docpassword123",
            full_name="Dr. Sanjay Gupta",
            role=User.Role.DOCTOR
        )
        self.doc_profile = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            qualification="MBBS, MD",
            specialization="General Physician",
            experience_years=10,
            consultation_fee=500.00,
            clinic_name="Gupta Medical Care",
            clinic_address="7th Cross, Koramangala",
            is_verified=True
        )

        # Patient User
        self.patient_user = User.objects.create_user(
            phone_number="9123456780",
            password="patientpassword",
            full_name="Patient Roy",
            role=User.Role.PATIENT
        )

    def test_anonymous_user_blocked_from_doctor_dashboard(self):
        url = reverse("doctor_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("doctor_login"), response.url)

    def test_patient_user_blocked_from_doctor_dashboard(self):
        self.client.force_login(self.patient_user)
        url = reverse("doctor_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("home"))

    def test_doctor_access_dashboard_success(self):
        self.client.force_login(self.doc_user)
        url = reverse("doctor_dashboard")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Gupta Medical Care")

    def test_doctor_queue_status_transition(self):
        self.client.force_login(self.doc_user)
        today = timezone.localdate()
        
        # Create slot and appointment
        slot = Slot.objects.create(
            doctor=self.doc_profile,
            date=today,
            start_time=time(10, 0),
            end_time=time(10, 30),
            is_booked=True
        )
        appt = Appointment.objects.create(
            booking_reference="DP-TEST-9901",
            token_number=1,
            doctor=self.doc_profile,
            slot=slot,
            appointment_date=today,
            appointment_time=time(10, 0),
            patient_name="Priya Sharma",
            patient_phone="9988001122",
            status=Appointment.Status.CONFIRMED
        )

        update_url = reverse("update_appointment_status", kwargs={"appointment_id": appt.id})
        
        # Advance to IN_CONSULTATION
        res1 = self.client.post(update_url, {"status": "IN_CONSULTATION"})
        self.assertEqual(res1.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.IN_CONSULTATION)

        # Advance to COMPLETED
        res2 = self.client.post(update_url, {"status": "COMPLETED"})
        self.assertEqual(res2.status_code, 302)
        appt.refresh_from_db()
        self.assertEqual(appt.status, Appointment.Status.COMPLETED)

    def test_slot_generator(self):
        self.client.force_login(self.doc_user)
        future_date = timezone.localdate() + timedelta(days=2)
        url = reverse("generate_slots")
        response = self.client.post(url, {"slot_date": future_date.strftime("%Y-%m-%d")})
        self.assertEqual(response.status_code, 302)
        
        slots_count = Slot.objects.filter(doctor=self.doc_profile, date=future_date).count()
        self.assertGreaterEqual(slots_count, 10)

    def test_doctor_profile_edit(self):
        self.client.force_login(self.doc_user)
        url = reverse("doctor_profile_edit")
        data = {
            "full_name": "Dr. Sanjay M. Gupta",
            "specialization": "Senior Consultant Physician",
            "qualification": "MBBS, MD, FACP",
            "experience_years": 15,
            "consultation_fee": 600.00,
            "clinic_name": "Gupta Multi-Specialty Clinic",
            "clinic_address": "New Location 123",
            "working_hours": "09:00 AM - 06:00 PM",
            "available_days": "Mon - Sat",
            "bio": "Updated bio details.",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.doc_profile.refresh_from_db()
        self.assertEqual(self.doc_profile.clinic_name, "Gupta Multi-Specialty Clinic")
        self.assertEqual(self.doc_profile.consultation_fee, 600.00)
        self.assertEqual(self.doc_profile.user.full_name, "Dr. Sanjay M. Gupta")
