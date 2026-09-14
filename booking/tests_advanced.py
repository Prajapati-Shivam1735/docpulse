from datetime import time, timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from doctors.models import Department, DoctorProfile
from booking.models import Slot, Appointment


class AdvancedIntegrationAndEdgeCaseTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cardio = Department.objects.create(name="Cardiology", slug="cardiology", icon="fa-heart-pulse")
        self.derma = Department.objects.create(name="Dermatology", slug="dermatology", icon="fa-spa")

        # Doctor 1
        self.doc1_user = User.objects.create_user(phone_number="9800000001", password="pass1", full_name="Dr. Alpha", role=User.Role.DOCTOR)
        self.doc1 = DoctorProfile.objects.create(
            user=self.doc1_user, department=self.cardio, qualification="MD Cardiology",
            specialization="Interventional", experience_years=10, consultation_fee=700.00,
            clinic_name="Alpha Clinic", clinic_address="Bandra West", is_verified=True
        )

        # Doctor 2
        self.doc2_user = User.objects.create_user(phone_number="9800000002", password="pass2", full_name="Dr. Beta", role=User.Role.DOCTOR)
        self.doc2 = DoctorProfile.objects.create(
            user=self.doc2_user, department=self.derma, qualification="MD Derma",
            specialization="Skin & Hair", experience_years=7, consultation_fee=500.00,
            clinic_name="Beta Derma", clinic_address="Andheri East", is_verified=True
        )

        # Patient
        self.patient = User.objects.create_user(phone_number="9800000099", password="patientpass", full_name="John Doe", role=User.Role.PATIENT)

        self.today = timezone.localdate()
        self.slot1 = Slot.objects.create(doctor=self.doc1, date=self.today, start_time=time(11, 0), end_time=time(11, 30), is_booked=False)
        self.slot2 = Slot.objects.create(doctor=self.doc1, date=self.today, start_time=time(11, 30), end_time=time(12, 0), is_booked=False)

    def test_sequential_daily_token_increments(self):
        """Verify tokens increment sequentially: #01, #02 for the same doctor on the same day."""
        # Book Slot 1
        url = reverse("book_appointment", kwargs={"doctor_id": self.doc1.id})
        res1 = self.client.post(url, {
            "date": self.today.strftime("%Y-%m-%d"),
            "slot_id": self.slot1.id,
            "patient_name": "Patient One",
            "patient_phone": "9811111111",
        })
        self.assertEqual(res1.status_code, 302)
        appt1 = Appointment.objects.get(slot=self.slot1)
        self.assertEqual(appt1.token_number, 1)
        self.assertEqual(appt1.formatted_token, "#01")

        # Book Slot 2
        res2 = self.client.post(url, {
            "date": self.today.strftime("%Y-%m-%d"),
            "slot_id": self.slot2.id,
            "patient_name": "Patient Two",
            "patient_phone": "9822222222",
        })
        self.assertEqual(res2.status_code, 302)
        appt2 = Appointment.objects.get(slot=self.slot2)
        self.assertEqual(appt2.token_number, 2)
        self.assertEqual(appt2.formatted_token, "#02")

    def test_rapid_consecutive_double_booking_collision(self):
        """Verify that when 2 booking attempts hit the exact same slot, the 1st succeeds and 2nd detects collision."""
        url = reverse("book_appointment", kwargs={"doctor_id": self.doc1.id})
        
        # 1st attempt: Successful
        res1 = self.client.post(url, {
            "date": self.today.strftime("%Y-%m-%d"),
            "slot_id": self.slot1.id,
            "patient_name": "First Patient",
            "patient_phone": "9811110001",
        }, follow=True)
        self.assertEqual(res1.status_code, 200)
        self.assertContains(res1, "Appointment successfully confirmed")
        self.slot1.refresh_from_db()
        self.assertTrue(self.slot1.is_booked)

        # 2nd attempt on the same slot: Collision detected
        res2 = self.client.post(url, {
            "date": self.today.strftime("%Y-%m-%d"),
            "slot_id": self.slot1.id,
            "patient_name": "Second Patient",
            "patient_phone": "9811110002",
        }, follow=True)
        self.assertEqual(res2.status_code, 200)
        self.assertContains(res2, "Collision detected: This time slot was just booked by another patient")

        # Verify only 1 appointment was saved for slot1
        self.assertEqual(Appointment.objects.filter(slot=self.slot1).count(), 1)

    def test_role_based_login_redirection(self):
        """Verify Doctor is redirected to doctor_dashboard and Patient to home upon login."""
        # Doctor login
        login_url = reverse("patient_login")
        doc_res = self.client.post(login_url, {"phone_number": "9800000001", "password": "pass1"}, follow=True)
        self.assertEqual(doc_res.status_code, 200)
        self.assertIn("doctor/dashboard", doc_res.redirect_chain[-1][0])
        self.client.logout()

        # Patient login
        pat_res = self.client.post(login_url, {"phone_number": "9800000099", "password": "patientpass"}, follow=True)
        self.assertEqual(pat_res.status_code, 200)
        self.assertEqual(pat_res.redirect_chain[-1][0], reverse("home"))

    def test_phone_number_cleaning_with_spaces_and_hyphens(self):
        """Ensure inputs with spaces/dashes are cleanly normalized."""
        reg_url = reverse("patient_register")
        data = {
            "full_name": "Spaces User",
            "phone_number": "987 654-3299",
            "password": "cleanpassword",
            "confirm_password": "cleanpassword",
        }
        res = self.client.post(reg_url, data, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(User.objects.filter(phone_number="9876543299").exists())

    def test_custom_404_handler(self):
        """Verify 404 template renders gracefully for nonexistent routes."""
        res = self.client.get("/non-existent-page-url-random-xyz/")
        self.assertEqual(res.status_code, 404)
        self.assertContains(res, "404", status_code=404)
        self.assertContains(res, "Healthcare Resource Not Found", status_code=404)

    def test_search_case_insensitivity_and_partial_matching(self):
        """Verify search matches lowercase, uppercase, and partial strings."""
        search_url = reverse("search")
        res_upper = self.client.get(search_url, {"q": "ALPHA"})
        self.assertEqual(res_upper.status_code, 200)
        self.assertContains(res_upper, "Dr. Alpha")

        res_partial = self.client.get(search_url, {"q": "cardio"})
        self.assertEqual(res_partial.status_code, 200)
        self.assertContains(res_partial, "Dr. Alpha")

    def test_slot_cannot_be_booked_for_different_doctor(self):
        """Security: Slot belonging to Doctor 1 cannot be booked through Doctor 2's booking endpoint."""
        url = reverse("book_appointment", kwargs={"doctor_id": self.doc2.id})
        res = self.client.post(url, {
            "date": self.today.strftime("%Y-%m-%d"),
            "slot_id": self.slot1.id,  # belongs to doc1
            "patient_name": "Hacker Patient",
            "patient_phone": "9800112233",
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "The selected time slot does not exist")
        self.slot1.refresh_from_db()
        self.assertFalse(self.slot1.is_booked)
