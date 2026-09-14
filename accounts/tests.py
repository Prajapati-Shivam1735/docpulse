from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from doctors.models import Department, DoctorProfile


class AccountsAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.cardio_dept = Department.objects.create(name="Cardiology", slug="cardiology", icon="fa-heart-pulse")

    def test_patient_registration_success(self):
        url = reverse("patient_register")
        data = {
            "full_name": "Test Patient",
            "phone_number": "9123456780",
            "gender": "Female",
            "age": 28,
            "password": "patientpassword123",
            "confirm_password": "patientpassword123",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        user = User.objects.get(phone_number="9123456780")
        self.assertEqual(user.full_name, "Test Patient")
        self.assertEqual(user.role, User.Role.PATIENT)
        self.assertTrue(user.check_password("patientpassword123"))

    def test_duplicate_phone_registration_rejected(self):
        User.objects.create_user(phone_number="9123456780", password="password123")
        url = reverse("patient_register")
        data = {
            "full_name": "Duplicate User",
            "phone_number": "9123456780",
            "gender": "Male",
            "age": 30,
            "password": "password123",
            "confirm_password": "password123",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "phone_number", "A user with this phone number already exists.")

    def test_password_mismatch_rejected(self):
        url = reverse("patient_register")
        data = {
            "full_name": "Mismatch User",
            "phone_number": "9123456789",
            "gender": "Male",
            "age": 30,
            "password": "password123",
            "confirm_password": "password456",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "confirm_password", "Passwords do not match.")

    def test_patient_login_and_logout(self):
        user = User.objects.create_user(phone_number="9123456780", password="mypassword123", full_name="Rahul")
        login_url = reverse("patient_login")
        response = self.client.post(login_url, {"phone_number": "9123456780", "password": "mypassword123"}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)

        # Test logout via POST
        logout_url = reverse("logout")
        logout_resp = self.client.post(logout_url, follow=True)
        self.assertEqual(logout_resp.status_code, 200)
        self.assertFalse(logout_resp.context["user"].is_authenticated)

        # Test logout via GET (prevents HTTP 405)
        self.client.force_login(user)
        get_logout_resp = self.client.get(logout_url, follow=True)
        self.assertEqual(get_logout_resp.status_code, 200)
        self.assertFalse(get_logout_resp.context["user"].is_authenticated)

    def test_doctor_self_registration_and_auto_publish(self):
        url = reverse("doctor_register")
        data = {
            "full_name": "Dr. Sameer Kapoor",
            "phone_number": "9811223344",
            "email": "dr.sameer@hospital.com",
            "password": "doctorpassword123",
            "confirm_password": "doctorpassword123",
            "department": self.cardio_dept.id,
            "qualification": "MBBS, MD, DM",
            "specialization": "Interventional Cardiologist",
            "experience_years": 12,
            "consultation_fee": 750.00,
            "clinic_name": "Kapoor Heart Center",
            "clinic_address": "45 Linking Road, Bandra",
            "bio": "Experienced cardiologist with 12+ years in cardiac interventions.",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        # Check User
        user = User.objects.get(phone_number="9811223344")
        self.assertEqual(user.role, User.Role.DOCTOR)
        self.assertTrue(user.is_doctor)

        # Check DoctorProfile auto-published
        profile = DoctorProfile.objects.get(user=user)
        self.assertTrue(profile.is_verified)
        self.assertEqual(profile.consultation_fee, 750.00)
        self.assertEqual(profile.department, self.cardio_dept)
