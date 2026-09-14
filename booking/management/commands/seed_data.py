import random
from datetime import time, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User
from doctors.models import Department, DoctorProfile
from booking.models import Slot, Appointment


class Command(BaseCommand):
    help = "Seeds initial departments, verified specialist doctors, available consultation slots, and sample queue appointments."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding DocPulse platform data...")

        # 1. Departments
        departments_data = [
            ("General Physician", "fa-stethoscope", "Diagnosis and treatment of common adult medical issues and illnesses.", 1),
            ("Cardiologist", "fa-heart-pulse", "Heart disorders, hypertension, ECG evaluation, and cardiovascular health.", 2),
            ("Dermatologist", "fa-spa", "Skin conditions, allergies, acne, hair and cosmetic treatments.", 3),
            ("Pediatrician", "fa-baby", "Child healthcare, developmental tracking, and pediatric consultations.", 4),
            ("Orthopedic", "fa-bone", "Bone fractures, joint pain, spine care, and musculoskeletal wellness.", 5),
            ("Neurologist", "fa-brain", "Brain, nerve disorders, migraine, and neurological diagnosis.", 6),
            ("Gynecologist", "fa-venus", "Women's reproductive health, prenatal care, and maternal wellness.", 7),
            ("Ophthalmologist", "fa-eye", "Vision care, eye examinations, cataract, and optical health.", 8),
            ("Dentist", "fa-tooth", "Dental cleaning, root canals, oral hygiene, and cosmetic orthodontics.", 9),
        ]

        dept_objs = {}
        for name, icon, desc, order in departments_data:
            dept, _ = Department.objects.get_or_create(
                name=name,
                defaults={"icon": icon, "description": desc, "display_order": order, "is_popular": True}
            )
            dept_objs[name] = dept
        self.stdout.write(self.style.SUCCESS(f"Created {len(dept_objs)} departments."))

        # 2. Admin user (Phone: 9999999999, Pass: admin123)
        admin_user, admin_created = User.objects.get_or_create(
            phone_number="9999999999",
            defaults={"full_name": "DocPulse Platform Admin", "role": User.Role.ADMIN, "is_staff": True, "is_superuser": True}
        )
        if admin_created:
            admin_user.set_password("admin123")
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created internal admin user (9999999999 / admin123)."))

        # 3. Verified Specialist Doctors
        doctors_info = [
            {
                "phone": "9820011221",
                "name": "Dr. Ananya Sharma",
                "dept": "Cardiologist",
                "qualification": "MBBS, MD (Medicine), DM (Cardiology)",
                "specialization": "Interventional Cardiology & Preventive Heart Care",
                "experience": 14,
                "fee": 800.00,
                "clinic_name": "DocPulse Heart Center",
                "clinic_address": "Suite 401, Metro Medical Towers, Bandra West, Mumbai",
                "rating": 4.9,
                "reviews": 184,
                "bio": "Fellow of the American College of Cardiology. Over 14 years clinical experience managing complex cardiac emergencies and preventive coronary health.",
            },
            {
                "phone": "9820011222",
                "name": "Dr. Rajesh Verma",
                "dept": "General Physician",
                "qualification": "MBBS, MD (Internal Medicine)",
                "specialization": "Consultant Physician & Chronic Disease Management",
                "experience": 11,
                "fee": 450.00,
                "clinic_name": "Verma Family Healthcare",
                "clinic_address": "Ground Floor, City Point Arcade, Andheri East, Mumbai",
                "rating": 4.8,
                "reviews": 230,
                "bio": "Dedicated physician providing comprehensive primary healthcare, seasonal infections management, and diabetes/lifestyle disease consultation.",
            },
            {
                "phone": "9820011223",
                "name": "Dr. Sneha Patel",
                "dept": "Dermatologist",
                "qualification": "MBBS, DDVL (Dermatology)",
                "specialization": "Clinical Dermatologist & Aesthetic Specialist",
                "experience": 8,
                "fee": 650.00,
                "clinic_name": "Glow Skin & Laser Clinic",
                "clinic_address": "Shop 12, Sunrise Plaza, Koramangala, Bengaluru",
                "rating": 4.9,
                "reviews": 142,
                "bio": "Specializes in clinical dermatology, acne therapies, pigmentary disorders, and laser dermatological consultations.",
            },
            {
                "phone": "9820011224",
                "name": "Dr. Vikram Rao",
                "dept": "Orthopedic",
                "qualification": "MBBS, MS (Orthopedics), M.Ch",
                "specialization": "Joint Replacement & Arthroscopy Specialist",
                "experience": 16,
                "fee": 900.00,
                "clinic_name": "Rao Ortho & Spine Clinic",
                "clinic_address": "Level 2, Apex Hospital Annex, Jubilee Hills, Hyderabad",
                "rating": 4.9,
                "reviews": 196,
                "bio": "Pioneer in minimally invasive joint surgery and sports injury rehabilitation. Over 16 years of clinical surgical excellence.",
            },
            {
                "phone": "9820011225",
                "name": "Dr. Meera Nambiar",
                "dept": "Pediatrician",
                "qualification": "MBBS, DCH, DNB (Pediatrics)",
                "specialization": "Senior Child Specialist & Neonatologist",
                "experience": 12,
                "fee": 500.00,
                "clinic_name": "Little Smiles Child Clinic",
                "clinic_address": "Plot 54, Indiranagar 100ft Road, Bengaluru",
                "rating": 5.0,
                "reviews": 310,
                "bio": "Compassionate pediatric care focusing on newborn wellness, immunization schedules, and developmental milestones.",
            },
            {
                "phone": "9820011226",
                "name": "Dr. Arjun Iyer",
                "dept": "Neurologist",
                "qualification": "MBBS, MD, DM (Neurology)",
                "specialization": "Consultant Neurologist & Stroke Specialist",
                "experience": 15,
                "fee": 1000.00,
                "clinic_name": "DocPulse Neuro Care",
                "clinic_address": "8th Floor, Health City Complex, Vasant Kunj, New Delhi",
                "rating": 4.9,
                "reviews": 115,
                "bio": "Expert in neurological evaluations, migraine therapies, epilepsy management, and peripheral nerve disorders.",
            },
        ]

        created_doctors = []
        for d in doctors_info:
            user, u_created = User.objects.get_or_create(
                phone_number=d["phone"],
                defaults={"full_name": d["name"], "role": User.Role.DOCTOR, "email": f"{d['phone']}@docpulse.local"}
            )
            if u_created:
                user.set_password("doctor123")
                user.save()

            profile, _ = DoctorProfile.objects.get_or_create(
                user=user,
                defaults={
                    "department": dept_objs.get(d["dept"]),
                    "qualification": d["qualification"],
                    "specialization": d["specialization"],
                    "experience_years": d["experience"],
                    "consultation_fee": d["fee"],
                    "clinic_name": d["clinic_name"],
                    "clinic_address": d["clinic_address"],
                    "rating": d["rating"],
                    "total_reviews": d["reviews"],
                    "bio": d["bio"],
                    "is_verified": True,
                }
            )
            created_doctors.append(profile)

        self.stdout.write(self.style.SUCCESS(f"Configured {len(created_doctors)} verified specialist doctors."))

        # 4. Generate Slots for today and the next 4 days
        today = timezone.localdate()
        slot_times = [
            (time(9, 30), time(10, 0), Slot.SlotPeriod.MORNING),
            (time(10, 30), time(11, 0), Slot.SlotPeriod.MORNING),
            (time(11, 30), time(12, 0), Slot.SlotPeriod.MORNING),
            (time(14, 0), time(14, 30), Slot.SlotPeriod.AFTERNOON),
            (time(15, 0), time(15, 30), Slot.SlotPeriod.AFTERNOON),
            (time(16, 30), time(17, 0), Slot.SlotPeriod.EVENING),
            (time(17, 30), time(18, 0), Slot.SlotPeriod.EVENING),
        ]

        total_slots = 0
        for doc in created_doctors:
            for day_offset in range(5):
                slot_date = today + timedelta(days=day_offset)
                for start_t, end_t, period in slot_times:
                    _, created = Slot.objects.get_or_create(
                        doctor=doc,
                        date=slot_date,
                        start_time=start_t,
                        defaults={"end_time": end_t, "slot_period": period, "is_booked": False}
                    )
                    if created:
                        total_slots += 1

        self.stdout.write(self.style.SUCCESS(f"Generated {total_slots} consultation slots across upcoming days."))

        # 5. Create Patient User & Seed Sample Appointments for Today's Queue
        patient_user, p_created = User.objects.get_or_create(
            phone_number="9876543210",
            defaults={"full_name": "Aakash Mehta", "role": User.Role.PATIENT, "gender": "Male", "age": 29}
        )
        if p_created:
            patient_user.set_password("patient123")
            patient_user.save()

        # Seed 2 sample appointments for Dr. Ananya Sharma (first doctor)
        first_doc = created_doctors[0]
        today_open_slots = Slot.objects.filter(doctor=first_doc, date=today, is_booked=False).order_by("start_time")
        if today_open_slots.count() >= 2:
            s1 = today_open_slots[0]
            s2 = today_open_slots[1]

            appt1, a1_created = Appointment.objects.get_or_create(
                booking_reference="DP-20260914-1011",
                defaults={
                    "token_number": 1,
                    "doctor": first_doc,
                    "patient_user": patient_user,
                    "slot": s1,
                    "appointment_date": today,
                    "appointment_time": s1.start_time,
                    "patient_name": "Aakash Mehta",
                    "patient_phone": "9876543210",
                    "patient_age": 29,
                    "patient_gender": "Male",
                    "reason_for_visit": "Mild chest tightness and routine blood pressure checkup",
                    "consultation_fee": first_doc.consultation_fee,
                    "status": Appointment.Status.IN_CONSULTATION,
                }
            )
            if a1_created:
                s1.is_booked = True
                s1.save()

            appt2, a2_created = Appointment.objects.get_or_create(
                booking_reference="DP-20260914-1012",
                defaults={
                    "token_number": 2,
                    "doctor": first_doc,
                    "patient_user": None,
                    "slot": s2,
                    "appointment_date": today,
                    "appointment_time": s2.start_time,
                    "patient_name": "Pooja Hegde",
                    "patient_phone": "9876543299",
                    "patient_age": 34,
                    "patient_gender": "Female",
                    "reason_for_visit": "Post-viral fatigue and palpitations check",
                    "consultation_fee": first_doc.consultation_fee,
                    "status": Appointment.Status.CONFIRMED,
                }
            )
            if a2_created:
                s2.is_booked = True
                s2.save()

            self.stdout.write(self.style.SUCCESS("Created sample active queue appointments for Dr. Ananya Sharma."))

        self.stdout.write(self.style.SUCCESS("All DocPulse data seeded successfully!"))
