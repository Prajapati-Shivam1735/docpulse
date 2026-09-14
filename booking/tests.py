from datetime import time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from doctors.models import Department, DoctorProfile
from booking.models import Slot, Appointment


class BookingModuleTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.dept = Department.objects.create(name="Pediatrics", slug="pediatrics", icon="fa-baby")
        self.doc_user = User.objects.create_user(
            phone_number="9876500001",
            password="docpassword",
            full_name="Dr. Sunita Rao",
            role=User.Role.DOCTOR
        )
        self.doctor = DoctorProfile.objects.create(
            user=self.doc_user,
            department=self.dept,
            qualification="MBBS, MD (Pediatrics)",
            specialization="Senior Pediatrician",
            experience_years=12,
            consultation_fee=550.00,
            clinic_name="Little Stars Clinic",
            clinic_address="MG Road, Bangalore",
            is_verified=True
        )
        self.today = timezone.localdate()
        self.tomorrow = self.today + timedelta(days=1)
        self.slot = Slot.objects.create(
            doctor=self.doctor,
            date=self.tomorrow,
            start_time=time(10, 0),
            end_time=time(10, 30),
            slot_period=Slot.SlotPeriod.MORNING,
            is_booked=False
        )

    def test_homepage_renders_cleanly_without_admin_links(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "DocPulse")
        self.assertContains(response, "Pediatrics")
        # Ensure no admin / staff login links are rendered on public home
        self.assertNotContains(response, "Admin Login")
        self.assertNotContains(response, "Staff Login")
        self.assertNotContains(response, "/admin/")

    def test_search_view_filtering_and_param_preservation(self):
        url = reverse("search")
        # Filter by department id
        response = self.client.get(url, {"dept": self.dept.id, "q": "Sunita"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dr. Sunita Rao")
        self.assertContains(response, "Pediatrics")

    def test_successful_slot_booking_and_token_generation(self):
        url = reverse("book_appointment", kwargs={"doctor_id": self.doctor.id})
        data = {
            "date": self.tomorrow.strftime("%Y-%m-%d"),
            "slot_id": self.slot.id,
            "patient_name": "Aarav Sharma",
            "patient_phone": "9812345678",
            "patient_age": 7,
            "patient_gender": "Male",
            "reason_for_visit": "Seasonal cough",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        # Verify Slot is booked
        self.slot.refresh_from_db()
        self.assertTrue(self.slot.is_booked)

        # Verify Appointment record created
        appt = Appointment.objects.get(slot=self.slot)
        self.assertEqual(appt.patient_name, "Aarav Sharma")
        self.assertEqual(appt.token_number, 1)
        self.assertEqual(appt.formatted_token, "#01")
        self.assertEqual(appt.consultation_fee, 550.00)

        # Verify redirect to slip
        slip_url = reverse("appointment_slip", kwargs={"booking_reference": appt.booking_reference})
        self.assertEqual(response.url, slip_url)

        # Verify slip page renders token and details
        slip_res = self.client.get(slip_url)
        self.assertEqual(slip_res.status_code, 200)
        self.assertContains(slip_res, "#01")
        self.assertContains(slip_res, appt.booking_reference)
        self.assertContains(slip_res, "Aarav Sharma")

    def test_slot_collision_double_booking_prevention(self):
        """Verify that booking an already-booked slot is rejected with collision notice."""
        # Pre-book the slot
        self.slot.is_booked = True
        self.slot.save()

        url = reverse("book_appointment", kwargs={"doctor_id": self.doctor.id})
        data = {
            "date": self.tomorrow.strftime("%Y-%m-%d"),
            "slot_id": self.slot.id,
            "patient_name": "Collision Test Patient",
            "patient_phone": "9899999999",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Collision detected")

    def test_past_date_booking_rejected(self):
        past_date = self.today - timedelta(days=2)
        url = reverse("book_appointment", kwargs={"doctor_id": self.doctor.id})
        response = self.client.get(url, {"date": past_date.strftime("%Y-%m-%d")})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Appointments cannot be booked for past dates.")

    def test_track_appointment_lookup(self):
        # Create appointment to track
        appt = Appointment.objects.create(
            booking_reference="DP-2026-TRACK01",
            token_number=3,
            doctor=self.doctor,
            slot=self.slot,
            appointment_date=self.tomorrow,
            appointment_time=time(10, 0),
            patient_name="Deepak Varma",
            patient_phone="9877766554",
            status=Appointment.Status.CONFIRMED
        )

        track_url = reverse("track_appointment")

        # Lookup by Phone Number
        res_phone = self.client.get(track_url, {"q": "9877766554"})
        self.assertEqual(res_phone.status_code, 200)
        self.assertContains(res_phone, "DP-2026-TRACK01")
        self.assertContains(res_phone, "Deepak Varma")

        # Lookup by Booking Reference
        res_ref = self.client.get(track_url, {"q": "DP-2026-TRACK01"})
        self.assertEqual(res_ref.status_code, 200)
        self.assertContains(res_ref, "Deepak Varma")
        self.assertContains(res_ref, "Token #03")
